//! Selected immutable payload plus private manual context; preparation is a later stage.
use crate::{
    activation::{Admitted, version_lease},
    contract::Bundle,
    fs::{Error, Result, Root, require},
    json,
    observer::Session,
    state::Context,
    supervisor::{self, Config, Outcome},
};
use std::{
    collections::BTreeMap,
    os::{fd::AsRawFd, unix::process::CommandExt},
};
pub fn run(options: &BTreeMap<&str, &str>) -> Result<Outcome> {
    let get = |key| options.get(key).copied().ok_or(Error::code("cli_misuse"));
    let allowed = [
        "--state-root",
        "--request",
        "--policy",
        "--observer-fd",
        "--context-id",
        "--timeout-ms",
        "--output-limit",
    ];
    require(options.keys().all(|k| allowed.contains(k)), "cli_misuse")?;
    let timeout = options
        .get("--timeout-ms")
        .unwrap_or(&"5000")
        .parse::<u64>()
        .map_err(|_| Error::code("cli_misuse"))?;
    let limit = options
        .get("--output-limit")
        .unwrap_or(&"4096")
        .parse::<usize>()
        .map_err(|_| Error::code("cli_misuse"))?;
    require(
        (100..=5000).contains(&timeout) && (256..=65536).contains(&limit),
        "cli_misuse",
    )?;
    let state = Root::open(get("--state-root")?)?;
    state.private()?;
    let selection = state.json("selection.json")?;
    selection.keys(&[
        "selection_version",
        "bundle_root",
        "request",
        "request_sha256",
        "artifact_sha256",
        "policy_sha256",
        "root_device",
        "root_inode",
        "media_sha256",
    ])?;
    require(
        selection.get("selection_version")?.i()? == 1
            && selection.get("request")?.s()? == get("--request")?,
        "selection_changed",
    )?;
    let root = Root::open(selection.get("bundle_root")?.s()?)?;
    let request = get("--request")?;
    let q = root.json(request)?;
    let bundle = Bundle::inspect(root, request, q.get("record_context")?.s()?)?;
    let path = get("--policy")?;
    let (parent, name) = path.rsplit_once('/').ok_or(Error::code("invalid_path"))?;
    let (bytes, hash, _) = Root::open(parent)?.read_record(name, 262144)?;
    let admitted = Admitted::new(bundle, request, &json::parse(&bytes)?, &hash)?;
    admitted.matches_selection(&selection)?;
    let _version_lease = version_lease(&state, &admitted)?;
    let profile = admitted.profile()?;
    require(
        profile.get("operations")?.a()?.is_empty(),
        "unsupported_operations",
    )?;
    let context = Context::open(
        &state,
        get("--context-id")?,
        admitted.request_digest(),
        admitted.request_record()?.get("run_id")?.s()?,
    )?;
    let work = context.work_descriptor()?;
    let work_fd = work.as_raw_fd();
    // Descriptor identity and all supplied roots are validated before the wrapper can
    // enter this explicit private work directory. No arbitrary cwd executable lookup.
    for name in ["runtime", "prefix", "saves", "cache", "logs"] {
        let directory = context
            .root
            .directory(admitted.request_record()?.get("roots")?.get(name)?.s()?)?;
        Root { file: directory }.private()?;
    }
    let mut command = admitted.fixture_command()?;
    for arg in profile.get("arguments")?.a()? {
        command.arg(arg.s()?);
    }
    for pair in profile.get("environment")?.a()? {
        command.env(pair.get("key")?.s()?, pair.get("value")?.s()?);
    }
    command.env("PEAR_FIXTURE_WORK_FD", work_fd.to_string());
    unsafe {
        command.pre_exec(move || {
            let flags = libc::fcntl(work_fd, libc::F_GETFD);
            if flags < 0 || libc::fcntl(work_fd, libc::F_SETFD, flags & !libc::FD_CLOEXEC) != 0 {
                return Err(std::io::Error::last_os_error());
            }
            Ok(())
        });
    }
    let fd = get("--observer-fd")?
        .parse::<i32>()
        .map_err(|_| Error::code("cli_misuse"))?;
    let mut peer = Session::new(
        fd,
        admitted.request_record()?,
        request,
        admitted.request_digest(),
        &context.capture,
    )?;
    Ok(supervisor::run(
        command,
        &Config { timeout, limit },
        &mut peer,
        &context,
    ))
}
pub fn failure(error: Error) -> Outcome {
    let mut outcome = Outcome::new(
        match error.code {
            "context_incomplete" => "context_incomplete",
            "context_busy" => "context_busy",
            "unsupported_operations" | "ineligible" | "runtime_authorization_unavailable" => {
                "ineligible"
            }
            _ => "invalid_contract",
        },
        true,
    );
    outcome.native_error = error.errno;
    outcome
}
