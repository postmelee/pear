//! Prepared private contexts, canonical prefix leases and preservation-first recovery.
use crate::{
    activation,
    encoding::encode,
    fs::{self, Error, Result, Root, require},
    json::J,
    native, profile,
};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs::File,
    io::Write,
    os::{fd::AsRawFd, unix::fs::MetadataExt},
};
fn obj(fields: impl IntoIterator<Item = (&'static str, J)>) -> J {
    J::Obj(fields.into_iter().map(|(k, v)| (k.into(), v)).collect())
}
fn text(v: &str) -> J {
    J::Str(v.into())
}
fn exclusive(file: &File) -> Result<()> {
    file.try_lock().map_err(|error| match error {
        std::fs::TryLockError::WouldBlock => Error::code("context_busy"),
        std::fs::TryLockError::Error(error) => Error::io(error),
    })
}
fn private_json(root: &Root, path: &str) -> Result<J> {
    let file = root.open_file(path)?;
    let m = file.metadata()?;
    require(
        m.uid() == unsafe { libc::geteuid() } && m.mode() & 0o077 == 0,
        "unsafe_state_file",
    )?;
    root.json(path)
}
pub(crate) fn mkdirs(root: &Root, path: &str) -> Result<File> {
    fs::relative(path)?;
    let mut file = root.file.try_clone()?;
    for part in path.split('/') {
        if unsafe { libc::mkdirat(file.as_raw_fd(), fs::c(part)?.as_ptr(), 0o700) } != 0 {
            let error = std::io::Error::last_os_error();
            if error.raw_os_error() != Some(libc::EEXIST) {
                return Err(error.into());
            }
        }
        file.sync_all()?;
        let parent = Root { file };
        file = parent.directory(part)?;
        Root {
            file: file.try_clone()?,
        }
        .private()?;
    }
    file.sync_all()?;
    Ok(file)
}
/// Reuse the Stage 2 private staged-file publication sequence for local metadata.
pub(crate) fn write_json(root: &Root, path: &str, value: &J) -> Result<()> {
    let bytes = encode(value);
    require(bytes.len() <= 262144, "state_size_limit")?;
    let (parent, name) = root.parent(path)?;
    let parent = Root { file: parent };
    parent.private()?;
    let stage = native::stage_directory(&parent.file)?;
    let dir = parent.directory(stage.to_str().map_err(|_| Error::code("invalid_stage"))?)?;
    let result = (|| {
        let mut file = fs::owned_fd(unsafe {
            libc::openat(
                dir.as_raw_fd(),
                c"record".as_ptr(),
                libc::O_WRONLY | libc::O_CREAT | libc::O_EXCL | libc::O_NOFOLLOW | libc::O_CLOEXEC,
                0o600,
            )
        })?;
        file.write_all(bytes.as_bytes())?;
        file.sync_all()?;
        dir.sync_all()?;
        if unsafe {
            libc::renameat(
                dir.as_raw_fd(),
                c"record".as_ptr(),
                parent.file.as_raw_fd(),
                name.as_ptr(),
            )
        } != 0
        {
            return Err(std::io::Error::last_os_error().into());
        }
        parent.file.sync_all()?;
        Ok(())
    })();
    unsafe {
        libc::unlinkat(dir.as_raw_fd(), c"record".as_ptr(), 0);
        libc::unlinkat(parent.file.as_raw_fd(), stage.as_ptr(), libc::AT_REMOVEDIR);
    }
    result
}
fn metadata(state: &Root, id: &str) -> Result<J> {
    crate::contract::id(&text(id))?;
    require(id == id.to_ascii_lowercase(), "context_id_not_canonical")?;
    state.private()?;
    let root = Root {
        file: state.directory(&format!("contexts/{id}"))?,
    };
    root.private()?;
    let value = private_json(&root, ".pear-context.json")?;
    value.keys(&[
        "context_version",
        "context_id",
        "selection",
        "binding",
        "identities",
    ])?;
    require(
        value.get("context_version")?.i()? == 1 && value.get("context_id")?.s()? == id,
        "context_identity_mismatch",
    )?;
    Ok(value)
}
pub(crate) fn selection(state: &Root, id: &str) -> Result<J> {
    Ok(metadata(state, id)?.get("selection")?.clone())
}
fn binding(request: &J, profile: &J) -> Result<J> {
    profile::validate(profile)?;
    require(
        request.get("prefix_family")?.s()? == profile.get("compatibility_family")?.s()?,
        "context_family_mismatch",
    )?;
    // Context ID is the caller's explicit library instance; store/App ID and exact
    // profile/cache identities prevent an ID from silently changing game/family.
    Ok(obj([
        ("family", request.get("prefix_family")?.clone()),
        ("store", profile.get("store")?.clone()),
        ("app_id", profile.get("app_id")?.clone()),
        (
            "profile",
            request.get("profile")?.get("digest")?.get("value")?.clone(),
        ),
        ("cache", request.get("cache_identity")?.clone()),
        ("roots", request.get("roots")?.clone()),
    ]))
}
fn identities(root: &Root, roots: &J) -> Result<J> {
    let mut result = Vec::new();
    let mut seen = BTreeSet::new();
    let mut add = |path: &str, file: File| -> Result<()> {
        let identity = fs::identity(&file)?;
        require(
            seen.insert((identity.device, identity.inode)),
            "context_alias",
        )?;
        result.push(obj([
            ("path", text(path)),
            ("device", text(&identity.device.to_string())),
            ("inode", text(&identity.inode.to_string())),
        ]));
        Ok(())
    };
    add(".", root.file.try_clone()?)?;
    add(".pear-lease", root.open_file(".pear-lease")?)?;
    for name in ["runtime", "prefix", "saves", "cache", "logs"] {
        let path = roots.get(name)?.s()?;
        let file = root.directory(path)?;
        Root {
            file: file.try_clone()?,
        }
        .private()?;
        fs::check_mutable(file.try_clone()?, &BTreeSet::new())?;
        add(path, file)?;
    }
    let path = format!("{}/.pear-prefix-lease", roots.get("prefix")?.s()?);
    add(&path, root.open_file(&path)?)?;
    Ok(J::Arr(result))
}
pub struct Context {
    pub root: Root,
    state: Root,
    metadata: J,
    _lease: File,
    _prefix_lease: File,
    pub capture: String,
    request: String,
    run_id: String,
    pub id: String,
}
impl Context {
    pub fn open(state: &Root, id: &str, request: &str, run_id: &str) -> Result<Self> {
        Self::acquire(state, id, request, run_id, false)
    }
    fn acquire(
        state: &Root,
        id: &str,
        request: &str,
        run_id: &str,
        allow_dirty: bool,
    ) -> Result<Self> {
        let metadata = metadata(state, id)?;
        require(
            metadata.get("selection")?.get("request_sha256")?.s()? == request,
            "context_request_mismatch",
        )?;
        let root = Root {
            file: state.directory(&format!("contexts/{id}"))?,
        };
        root.private()?;
        let lease = root.open_file(".pear-lease")?;
        exclusive(&lease)?;
        let prefix_lease = root.open_file(&format!(
            "{}/.pear-prefix-lease",
            metadata.get("binding")?.get("roots")?.get("prefix")?.s()?
        ))?;
        exclusive(&prefix_lease)?;
        match root.open_file(".pear-journal.json") {
            Ok(file) => {
                let m = file.metadata()?;
                require(
                    m.uid() == unsafe { libc::geteuid() } && m.mode() & 0o077 == 0,
                    "unsafe_journal",
                )?;
                let previous = root.json(".pear-journal.json")?;
                previous.keys(&[
                    "journal_version",
                    "state",
                    "context_id",
                    "request_sha256",
                    "run_id",
                    "capture_id",
                    "owner_pid",
                    "owner_started_sec",
                    "owner_started_usec",
                ])?;
                crate::contract::id(previous.get("run_id")?)?;
                crate::contract::id(previous.get("capture_id")?)?;
                require(
                    previous.get("request_sha256")?.s()?.len() == 64
                        && previous
                            .get("request_sha256")?
                            .s()?
                            .bytes()
                            .all(|c| c.is_ascii_hexdigit() && !c.is_ascii_uppercase()),
                    "unsafe_journal",
                )?;
                require(
                    (1..=i32::MAX as i64).contains(&previous.get("owner_pid")?.i()?)
                        && previous.get("owner_started_sec")?.i()? > 0
                        && (0..1_000_000).contains(&previous.get("owner_started_usec")?.i()?),
                    "unsafe_journal",
                )?;
                require(
                    previous.get("journal_version")?.i()? == 1
                        && previous.get("context_id")?.s()? == id
                        && ["clean", "running", "cleanup_pending"]
                            .contains(&previous.get("state")?.s()?),
                    "context_incomplete",
                )?;
                require(
                    allow_dirty || previous.get("state")?.s()? == "clean",
                    "context_incomplete",
                )?;
            }
            Err(e) if e.errno == Some(libc::ENOENT) => (),
            Err(e) => return Err(e),
        }
        let mut random = [0u8; 16];
        unsafe { libc::arc4random_buf(random.as_mut_ptr().cast(), random.len()) };
        let result = Self {
            root,
            state: Root {
                file: state.file.try_clone()?,
            },
            metadata,
            _lease: lease,
            _prefix_lease: prefix_lease,
            capture: format!("capture-{}", fs::hex(&random)),
            request: request.into(),
            run_id: run_id.into(),
            id: id.into(),
        };
        result.validate()?;
        Ok(result)
    }
    pub fn validate(&self) -> Result<()> {
        require(
            fs::identity(&self.state.directory(&format!("contexts/{}", self.id))?)?
                == fs::identity(&self.root.file)?,
            "context_replaced",
        )?;
        require(
            private_json(&self.root, ".pear-context.json")? == self.metadata,
            "context_metadata_changed",
        )?;
        let roots = self.metadata.get("binding")?.get("roots")?;
        require(
            &identities(&self.root, roots)? == self.metadata.get("identities")?,
            "context_replaced",
        )?;
        require(
            fs::identity(&self.root.open_file(".pear-lease")?)? == fs::identity(&self._lease)?
                && fs::identity(
                    &self
                        .root
                        .open_file(&format!("{}/.pear-prefix-lease", roots.get("prefix")?.s()?))?,
                )? == fs::identity(&self._prefix_lease)?,
            "context_lock_replaced",
        )?;
        let cache = Root {
            file: self.root.directory(roots.get("cache")?.s()?)?,
        };
        require(
            private_json(&cache, ".pear-cache.json")?
                == *self.metadata.get("binding")?.get("cache")?,
            "cache_identity_mismatch",
        )?;
        Ok(())
    }
    pub(crate) fn matches(&self, request: &J, profile: &J) -> Result<()> {
        require(
            self.metadata.get("binding")? == &binding(request, profile)?,
            "context_incompatible",
        )
    }
    pub(crate) fn bindings(&self, request: &J) -> Result<Vec<(String, File)>> {
        ["prefix", "saves", "cache", "logs"]
            .iter()
            .map(|name| {
                Ok((
                    name.to_string(),
                    self.root.directory(request.get("roots")?.get(name)?.s()?)?,
                ))
            })
            .collect()
    }
    pub fn publish(&self, status: &str) -> Result<()> {
        self.validate()?;
        require(
            ["running", "cleanup_pending", "clean"].contains(&status),
            "invalid_journal_state",
        )?;
        let (sec, usec) = native::process_identity(std::process::id() as i32)?;
        let mut fields = BTreeMap::new();
        for (k, v) in [
            ("state", status),
            ("context_id", &self.id),
            ("request_sha256", &self.request),
            ("run_id", &self.run_id),
            ("capture_id", &self.capture),
        ] {
            fields.insert(k.into(), text(v));
        }
        for (k, v) in [
            ("journal_version", 1),
            ("owner_pid", std::process::id() as i64),
            ("owner_started_sec", sec as i64),
            ("owner_started_usec", usec as i64),
        ] {
            fields.insert(k.into(), J::Int(v));
        }
        write_json(&self.root, ".pear-journal.json", &J::Obj(fields))
    }
    pub fn work_descriptor(&self) -> Result<File> {
        Ok(self.root.file.try_clone()?)
    }
}
/// Explicit fixture harness hooks; the CLI always supplies a no-op callback.
pub fn prepare_with(
    state: &Root,
    id: &str,
    selection: &J,
    admitted: &activation::Admitted,
    mut hook: impl FnMut(&str) -> Result<()>,
) -> Result<()> {
    crate::contract::id(&text(id))?;
    require(id == id.to_ascii_lowercase(), "context_id_not_canonical")?;
    state.private()?;
    let request = admitted.request_record()?;
    let profile = admitted.profile()?;
    let bind = binding(request, profile)?;
    let _version = activation::version_lease(state, admitted)?;
    let parent = Root {
        file: mkdirs(state, "contexts")?,
    };
    let prepare_lease = activation::private_file(&parent, ".pear-prepare-lease")?;
    exclusive(&prepare_lease)?;
    match parent.directory(id) {
        Ok(_) => {
            let context = Context::open(
                state,
                id,
                admitted.request_digest(),
                request.get("run_id")?.s()?,
            )?;
            context.matches(request, profile)?;
            context.publish("running")?;
            profile::apply(&context.root, request, profile)?;
            hook("settings_written")?;
            context.publish("clean")?;
            return Ok(());
        }
        Err(error) if error.errno == Some(libc::ENOENT) => (),
        Err(error) => return Err(error),
    }
    let stage = native::stage_directory(&parent.file)?;
    let root = Root {
        file: parent.directory(stage.to_str().map_err(|_| Error::code("invalid_stage"))?)?,
    };
    // Incomplete staged contexts are left private and are never selected/reused.
    for name in ["runtime", "prefix", "saves", "cache", "logs"] {
        mkdirs(&root, request.get("roots")?.get(name)?.s()?)?;
    }
    let _context_lease = activation::private_file(&root, ".pear-lease")?;
    let prefix = Root {
        file: root.directory(request.get("roots")?.get("prefix")?.s()?)?,
    };
    let _prefix_lease = activation::private_file(&prefix, ".pear-prefix-lease")?;
    let saves = Root {
        file: root.directory(request.get("roots")?.get("saves")?.s()?)?,
    };
    for save in profile.get("save_paths")?.a()? {
        if let Some((path, _)) = save.get("path")?.s()?.rsplit_once('/') {
            mkdirs(&saves, path)?;
        }
    }
    let cache = Root {
        file: root.directory(request.get("roots")?.get("cache")?.s()?)?,
    };
    write_json(&cache, ".pear-cache.json", request.get("cache_identity")?)?;
    profile::apply(&root, request, profile)?;
    let metadata = obj([
        ("context_version", J::Int(1)),
        ("context_id", text(id)),
        ("selection", selection.clone()),
        ("binding", bind),
        ("identities", identities(&root, request.get("roots")?)?),
    ]);
    write_json(&root, ".pear-context.json", &metadata)?;
    root.file.sync_all()?;
    admitted.revalidate()?;
    hook("before_publish")?;
    if unsafe {
        libc::renameatx_np(
            parent.file.as_raw_fd(),
            stage.as_ptr(),
            parent.file.as_raw_fd(),
            fs::c(id)?.as_ptr(),
            libc::RENAME_EXCL,
        )
    } != 0
    {
        return Err(std::io::Error::last_os_error().into());
    }
    hook("after_publish").map_err(|error| Error {
        code: "context_commit_uncertain",
        errno: error.errno,
    })?;
    parent.file.sync_all().map_err(|error| Error {
        code: "context_commit_uncertain",
        errno: error.raw_os_error(),
    })?;
    Ok(())
}
pub fn command(name: &str, options: &BTreeMap<&str, &str>) -> Result<&'static str> {
    let get = |key| options.get(key).copied().ok_or(Error::code("cli_misuse"));
    let allowed = if name == "status" {
        vec!["--state-root", "--context-id"]
    } else {
        vec![
            "--state-root",
            "--profile",
            "--context-id",
            "--new-context",
            "--policy",
        ]
    };
    require(
        options.keys().all(|key| allowed.contains(key)),
        "cli_misuse",
    )?;
    let state = Root::open(get("--state-root")?)?;
    state.private()?;
    if name == "status" {
        let id = get("--context-id")?;
        let selection = selection(&state, id)?;
        let context = Context::acquire(
            &state,
            id,
            selection.get("request_sha256")?.s()?,
            "status",
            true,
        )?;
        return match context.root.json(".pear-journal.json") {
            Ok(journal) => Ok(if journal.get("state")?.s()? == "clean" {
                "context_clean"
            } else {
                "context_incomplete"
            }),
            Err(error) if error.errno == Some(libc::ENOENT) => Ok("context_prepared"),
            Err(error) => Err(error),
        };
    }
    let existing = name == "recover" && options.contains_key("--context-id");
    let id = if name == "prepare" || existing {
        get("--context-id")?
    } else {
        get("--new-context")?
    };
    require(
        !(options.contains_key("--context-id") && options.contains_key("--new-context"))
            && (name == "recover" || !options.contains_key("--new-context")),
        "cli_misuse",
    )?;
    let selection = if existing {
        selection(&state, id)?
    } else {
        state.json("selection.json")?
    };
    let admitted =
        crate::launch::load(&selection, selection.get("request")?.s()?, get("--policy")?)?;
    require(
        admitted
            .request_record()?
            .get("profile")?
            .get("path")?
            .s()?
            == get("--profile")?,
        "profile_selection_mismatch",
    )?;
    if existing {
        let context = Context::open(
            &state,
            id,
            admitted.request_digest(),
            admitted.request_record()?.get("run_id")?.s()?,
        )?;
        context.matches(admitted.request_record()?, admitted.profile()?)?;
        admitted.revalidate()?;
        return Ok("compatible_context_selected");
    }
    if name == "recover" {
        match state.directory(&format!("contexts/{id}")) {
            Ok(_) => return Err(Error::code("recovery_requires_new_context")),
            Err(error) if error.errno == Some(libc::ENOENT) => (),
            Err(error) => return Err(error),
        }
    }
    prepare_with(&state, id, &selection, &admitted, |_| Ok(()))?;
    Ok("context_prepared")
}
