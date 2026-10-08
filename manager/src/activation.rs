//! Admission of manually prepared UDRO media and atomic local selection metadata.
//! No download, installer, general dynamic-loading support, or real-runtime grant.
use crate::{
    contract::Bundle,
    fs::{self, Error, Identity, Result, Root, require},
    json::{self, J},
    native, tools,
};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs::File,
    io::Write,
    os::{
        fd::AsRawFd,
        unix::{
            fs::{FileExt, MetadataExt},
            process::CommandExt,
        },
    },
    process::Command,
};
const MEDIA_LIMIT: u64 = 64 * 1024 * 1024 * 1024;
fn plist(command: &mut Command) -> Result<J> {
    let xml = tools::capture(command)?;
    let bytes = tools::capture_input(
        Command::new("/usr/bin/plutil").args(["-convert", "json", "-o", "-", "-"]),
        Some(&xml),
    )?;
    Ok(json::parse(&bytes)?)
}
fn readonly(root: &Root) -> Result<(u64, i32, i32)> {
    let info = native::mount_info(&root.file)?;
    require(
        info.0 & libc::MNT_RDONLY as u64 != 0,
        "payload_not_readonly",
    )?;
    require(info.0 & libc::MNT_NOEXEC as u64 == 0, "payload_noexec")?;
    Ok(info)
}
struct Media {
    file: File,
    digest: [u8; 32],
    identity: Identity,
}
impl Media {
    fn inspect(root: &Root) -> Result<Self> {
        let dev = root.file.metadata()?.dev();
        let info = plist(Command::new("/usr/bin/hdiutil").args(["info", "-plist"]))?;
        let mut selected = None;
        for image in info.get("images")?.a()? {
            for entity in image.get("system-entities")?.a()? {
                let Ok(mount) = entity.get("mount-point").and_then(J::s) else {
                    continue;
                };
                let Ok(mounted) = Root::open(mount) else {
                    continue;
                };
                if mounted.file.metadata()?.dev() != dev {
                    continue;
                }
                require(selected.is_none(), "ambiguous_media")?;
                require(
                    !image.get("writeable")?.b()?
                        && image.get("owner-uid")?.i()? == unsafe { libc::geteuid() } as i64,
                    "unowned_or_writable_media",
                )?;
                let image_path = image.get("image-path")?.s()?;
                let (parent, name) = image_path
                    .rsplit_once('/')
                    .ok_or(Error::code("invalid_media"))?;
                let file = Root::open(parent)?.open_file(name)?;
                let m = file.metadata()?;
                require(
                    m.uid() == unsafe { libc::geteuid() } && m.mode() & 0o022 == 0,
                    "unowned_or_writable_media",
                )?;
                let format = plist(Command::new("/usr/bin/hdiutil").args([
                    "imageinfo",
                    "-plist",
                    image_path,
                ]))?;
                require(format.get("Format")?.s()? == "UDRO", "unsupported_media")?;
                let (digest, _) = native::sha256(&file, MEDIA_LIMIT)?;
                selected = Some(Self {
                    identity: fs::identity(&file)?,
                    file,
                    digest,
                });
            }
        }
        selected.ok_or(Error::code("unidentified_media"))
    }
    fn revalidate(&self) -> Result<()> {
        let m = self.file.metadata()?;
        require(
            m.uid() == unsafe { libc::geteuid() }
                && m.mode() & 0o022 == 0
                && fs::identity(&self.file)? == self.identity
                && native::sha256(&self.file, MEDIA_LIMIT)?.0 == self.digest,
            "media_changed",
        )
    }
}
fn rooted(root: &Root, program: &str, args: &[&str]) -> Command {
    let mut command = Command::new(program);
    command.args(args);
    let fd = root.file.as_raw_fd();
    // SAFETY: the root descriptor outlives spawn; only async-signal-safe fchdir runs.
    unsafe {
        command.pre_exec(move || {
            if libc::fchdir(fd) == 0 {
                Ok(())
            } else {
                Err(std::io::Error::last_os_error())
            }
        });
    }
    command
}
fn parent(path: &str) -> &str {
    path.rsplit_once('/').map_or("", |x| x.0)
}
fn join(base: &str, tail: &str) -> Result<String> {
    fs::relative(tail)?;
    let value = if base.is_empty() {
        tail.into()
    } else {
        format!("{base}/{tail}")
    };
    fs::relative(&value)?;
    Ok(value)
}
fn local_token(token: &str, loader: &str, entry: &str) -> Result<String> {
    if let Some(tail) = token.strip_prefix("@loader_path/") {
        join(parent(loader), tail)
    } else if let Some(tail) = token.strip_prefix("@executable_path/") {
        join(parent(entry), tail)
    } else {
        Err(Error::code("unsupported_load_path"))
    }
}
fn dependencies(bundle: &Bundle, artifact: &J, entry: &str) -> Result<()> {
    let mut declared = BTreeMap::new();
    for f in artifact.get("files")?.a()? {
        if f.get("role")?.s()? == "host" {
            require(
                f.get("architecture")?.s()? == "arm64"
                    && ["mach_o", "fixture"].contains(&f.get("format")?.s()?),
                "host_not_native",
            )?;
            declared.insert(f.get("content")?.get("path")?.s()?, f);
        }
    }
    let mut graphs = BTreeMap::new();
    for path in declared.keys() {
        let file = bundle.root.open_file(path)?;
        let mut header = [0; 16];
        require(
            file.read_at(&mut header, 0)? == 16
                && u32::from_le_bytes(header[..4].try_into().unwrap()) == 0xfeedfacf
                && u32::from_le_bytes(header[4..8].try_into().unwrap()) == 0x0100000c,
            "unsupported_mach_o",
        )?;
        let kind = u32::from_le_bytes(header[12..16].try_into().unwrap());
        require(
            kind == if *path == entry { 2 } else { 6 },
            "unsupported_mach_o",
        )?;
        let relative = format!("./{path}");
        tools::capture(&mut rooted(
            &bundle.root,
            "/usr/bin/codesign",
            &["--verify", "--strict", &relative],
        ))?;
        let listing = tools::capture(&mut rooted(
            &bundle.root,
            "/usr/bin/otool",
            &["-L", &relative],
        ))?;
        require(!listing.is_empty(), "dependency_inspection_failed")?;
        let output = tools::capture(&mut rooted(
            &bundle.root,
            "/usr/bin/otool",
            &["-l", &relative],
        ))?;
        let output =
            String::from_utf8(output).map_err(|_| Error::code("dependency_inspection_failed"))?;
        let mut loads = Vec::new();
        let mut rpaths = Vec::new();
        let mut current = "";
        for line in output.lines().map(str::trim) {
            if let Some(cmd) = line.strip_prefix("cmd ") {
                current = cmd;
                require(
                    ![
                        "LC_DYLD_ENVIRONMENT",
                        "LC_LOAD_WEAK_DYLIB",
                        "LC_REEXPORT_DYLIB",
                        "LC_LOAD_UPWARD_DYLIB",
                        "LC_LAZY_LOAD_DYLIB",
                        "LC_LOADFVMLIB",
                        "LC_IDFVMLIB",
                        "LC_PREBOUND_DYLIB",
                        "LC_SUB_FRAMEWORK",
                        "LC_SUB_UMBRELLA",
                        "LC_SUB_CLIENT",
                        "LC_SUB_LIBRARY",
                        "LC_FILESET_ENTRY",
                    ]
                    .contains(&cmd),
                    "unsupported_dynamic_loading",
                )?;
            }
            if let Some(value) = line
                .strip_prefix("name ")
                .and_then(|s| s.rsplit_once(" (offset ").map(|x| x.0))
            {
                if current == "LC_LOAD_DYLIB" {
                    loads.push(value.to_owned());
                } else if current == "LC_LOAD_DYLINKER" {
                    require(value == "/usr/lib/dyld", "unsupported_load_path")?;
                }
            }
            if current == "LC_RPATH" {
                if let Some(value) = line
                    .strip_prefix("path ")
                    .and_then(|s| s.rsplit_once(" (offset ").map(|x| x.0))
                {
                    rpaths.push(local_token(value, path, entry)?);
                }
            }
        }
        require(
            *path == entry || rpaths.is_empty(),
            "unsupported_inherited_rpath",
        )?;
        graphs.insert(*path, (loads, rpaths));
    }
    let entry_paths = &graphs
        .get(entry)
        .ok_or(Error::code("invalid_entry_file"))?
        .1;
    for (path, (loads, paths)) in &graphs {
        for load in loads {
            if load == "/usr/lib/libSystem.B.dylib" {
                continue;
            }
            let resolved = if let Some(tail) = load.strip_prefix("@rpath/") {
                fs::relative(tail)?;
                let mut candidates = BTreeSet::new();
                for base in paths.iter().chain(entry_paths) {
                    let p = join(base, tail)?;
                    match bundle.root.open_file(&p) {
                        Ok(_) => {
                            require(declared.contains_key(p.as_str()), "undeclared_dependency")?;
                            candidates.insert(p);
                        }
                        Err(e) if e.errno == Some(libc::ENOENT) => (),
                        Err(e) => return Err(e),
                    }
                }
                require(candidates.len() == 1, "ambiguous_or_external_dependency")?;
                candidates.into_iter().next().unwrap()
            } else {
                local_token(load, path, entry)?
            };
            require(
                declared.contains_key(resolved.as_str()),
                "undeclared_dependency",
            )?;
        }
    }
    Ok(())
}
pub struct Admitted {
    bundle: Bundle,
    entry: String,
    request: String,
    artifact_digest: String,
    policy_digest: String,
    mount: (u64, i32, i32),
    root_identity: Identity,
    media: Media,
}
impl Admitted {
    pub fn new(bundle: Bundle, request: &str, policy: &J, policy_sha256: &str) -> Result<Self> {
        crate::policy::validate(policy)?;
        let q = bundle.request(request)?;
        let purpose = q.get("purpose")?.s()?;
        let now = unsafe { libc::time(std::ptr::null_mut()) };
        require(
            bundle
                .eligibility(request, purpose, Some(policy), now)?
                .is_empty(),
            "ineligible",
        )?;
        // The independent host/signing/observer grant producer is unavailable in Stage 2.
        // Submitted policy or synthetic signing records cannot authorize runtime execution.
        require(
            bundle.context == "fixture" && purpose == "fixture_launch",
            "runtime_authorization_unavailable",
        )?;
        for k in ["lock", "artifact", "profile"] {
            require(
                crate::contract::string_set(policy.get("approved_record_digests")?)?
                    .contains(q.get(k)?.get("digest")?.get("value")?.s()?),
                "identity_not_trusted",
            )?;
        }
        let mount = readonly(&bundle.root)?;
        let media = Media::inspect(&bundle.root)?;
        let root_identity = fs::identity(&bundle.root.file)?;
        let artifact = bundle.target(q.get("artifact")?, "runtime_artifact")?;
        let f = artifact
            .get("files")?
            .a()?
            .iter()
            .find(|f| f.get("file_id") == q.get("entry_file_id"))
            .ok_or(Error::code("invalid_entry_file"))?;
        let entry = f.get("content")?.get("path")?.s()?.to_owned();
        dependencies(&bundle, artifact, &entry)?;
        let artifact_digest = q
            .get("artifact")?
            .get("digest")?
            .get("value")?
            .s()?
            .to_owned();
        crate::contract::digest_value(&J::Str(policy_sha256.into()))?;
        let policy_digest = policy_sha256.to_owned();
        Ok(Self {
            bundle,
            entry,
            request: request.into(),
            artifact_digest,
            policy_digest,
            mount,
            root_identity,
            media,
        })
    }
    pub(crate) fn request_record(&self) -> Result<&J> {
        self.bundle.request(&self.request)
    }
    pub(crate) fn request_digest(&self) -> &str {
        &self.bundle.hashes[&self.request]
    }
    pub(crate) fn profile(&self) -> Result<&J> {
        self.bundle
            .target(self.request_record()?.get("profile")?, "game_profile")
    }
    pub(crate) fn matches_selection(&self, s: &J) -> Result<()> {
        require(
            s.get("request_sha256")?.s()? == self.request_digest()
                && s.get("artifact_sha256")?.s()? == self.artifact_digest
                && s.get("policy_sha256")?.s()? == self.policy_digest
                && s.get("root_device")?.s()? == self.root_identity.device.to_string()
                && s.get("root_inode")?.s()? == self.root_identity.inode.to_string()
                && s.get("media_sha256")?.s()? == fs::hex(&self.media.digest),
            "selection_changed",
        )
    }
    pub fn revalidate(&self) -> Result<()> {
        require(
            readonly(&self.bundle.root)? == self.mount
                && fs::identity(&self.bundle.root.file)? == self.root_identity,
            "mount_changed",
        )?;
        self.media.revalidate()?;
        for (path, hash) in self.bundle.hashes.iter().chain(&self.bundle.blobs) {
            let file = self.bundle.root.open_file(path)?;
            require(
                fs::hex(&native::sha256(&file, MEDIA_LIMIT)?.0) == *hash,
                "payload_changed",
            )?;
        }
        Ok(())
    }
    /// Stage 2 exposes command construction solely for the finite fixture probe.
    /// The caller retains this admission and its version lease through child reap.
    pub fn fixture_command(&self) -> Result<Command> {
        self.revalidate()?;
        let relative = format!("./{}", self.entry);
        let mut cmd = rooted(&self.bundle.root, &relative, &[]);
        cmd.env_clear();
        Ok(cmd)
    }
}
pub(crate) fn private_file(root: &Root, name: &str) -> Result<File> {
    let fd = unsafe {
        libc::openat(
            root.file.as_raw_fd(),
            fs::c(name)?.as_ptr(),
            libc::O_RDWR | libc::O_CREAT | libc::O_NOFOLLOW | libc::O_CLOEXEC | libc::O_NONBLOCK,
            0o600,
        )
    };
    let f = fs::owned_fd(fd)?;
    let m = f.metadata()?;
    require(
        m.is_file()
            && m.nlink() == 1
            && m.uid() == unsafe { libc::geteuid() }
            && m.mode() & 0o077 == 0,
        "unsafe_state_file",
    )?;
    Ok(f)
}
pub fn version_lease(state: &Root, admitted: &Admitted) -> Result<File> {
    state.private()?;
    let f = private_file(state, &format!("lease-{}", admitted.artifact_digest))?;
    f.try_lock_shared().map_err(|e| match e {
        std::fs::TryLockError::WouldBlock => Error::code("version_busy"),
        std::fs::TryLockError::Error(e) => Error::io(e),
    })?;
    Ok(f)
}
/// Atomically publishes only metadata; previous media and versions are untouched.
pub fn activate(state: &Root, admitted: &Admitted, root_path: &str, request: &str) -> Result<()> {
    activate_with(state, admitted, root_path, request, |_| Ok(()))
}
/// Explicit fault boundary for the fixture harness; no environment-controlled behavior.
#[doc(hidden)]
pub fn activate_with(
    state: &Root,
    a: &Admitted,
    root_path: &str,
    request: &str,
    mut boundary: impl FnMut(&str) -> Result<()>,
) -> Result<()> {
    state.private()?;
    require(request == a.request, "request_mismatch")?;
    a.revalidate()?;
    let lock = private_file(state, "activation.lock")?;
    lock.try_lock().map_err(|e| match e {
        std::fs::TryLockError::WouldBlock => Error::code("state_busy"),
        std::fs::TryLockError::Error(e) => Error::io(e),
    })?;
    let _lease = version_lease(state, a)?;
    match state.open_file("selection.json") {
        Ok(f) => {
            let m = f.metadata()?;
            require(
                m.uid() == unsafe { libc::geteuid() } && m.mode() & 0o077 == 0,
                "unsafe_state_file",
            )?;
        }
        Err(e) if e.errno == Some(libc::ENOENT) => (),
        Err(e) => return Err(e),
    }
    let stage = native::stage_directory(&state.file)?;
    let name = stage.to_str().map_err(|_| Error::code("invalid_stage"))?;
    let stage_root = Root {
        file: state.directory(name)?,
    };
    let operation = (|| {
        boundary("staged")?;
        let mut fields = BTreeMap::new();
        fields.insert("selection_version".into(), J::Int(1));
        fields.insert("bundle_root".into(), J::Str(root_path.into()));
        fields.insert("request".into(), J::Str(request.into()));
        fields.insert(
            "request_sha256".into(),
            J::Str(a.bundle.hashes[request].clone()),
        );
        fields.insert("artifact_sha256".into(), J::Str(a.artifact_digest.clone()));
        fields.insert("policy_sha256".into(), J::Str(a.policy_digest.clone()));
        fields.insert(
            "root_device".into(),
            J::Str(a.root_identity.device.to_string()),
        );
        fields.insert(
            "root_inode".into(),
            J::Str(a.root_identity.inode.to_string()),
        );
        fields.insert("media_sha256".into(), J::Str(fs::hex(&a.media.digest)));
        let bytes = crate::encoding::encode(&J::Obj(fields));
        require(bytes.len() <= 262144, "selection_size_limit")?;
        let mut f = fs::owned_fd(unsafe {
            libc::openat(
                stage_root.file.as_raw_fd(),
                fs::c("selection.json")?.as_ptr(),
                libc::O_WRONLY | libc::O_CREAT | libc::O_EXCL | libc::O_NOFOLLOW | libc::O_CLOEXEC,
                0o600,
            )
        })?;
        boundary("write")?;
        f.write_all(bytes.as_bytes())?;
        boundary("written")?;
        boundary("sync")?;
        f.sync_all()?;
        stage_root.file.sync_all()?;
        boundary("durable")?;
        a.revalidate()?;
        if unsafe {
            libc::renameat(
                stage_root.file.as_raw_fd(),
                fs::c("selection.json")?.as_ptr(),
                state.file.as_raw_fd(),
                fs::c("selection.json")?.as_ptr(),
            )
        } != 0
        {
            return Err(Error {
                code: "selection_rename_failed",
                errno: std::io::Error::last_os_error().raw_os_error(),
            });
        }
        // Publication has occurred. Any later failure is explicitly indeterminate, not rollback.
        boundary("published").map_err(|e| Error {
            code: "selection_commit_uncertain",
            errno: e.errno,
        })?;
        state.file.sync_all().map_err(|e| Error {
            code: "selection_commit_uncertain",
            errno: e.raw_os_error(),
        })?;
        Ok(())
    })();
    unsafe {
        libc::unlinkat(
            stage_root.file.as_raw_fd(),
            fs::c("selection.json")?.as_ptr(),
            0,
        );
        libc::unlinkat(state.file.as_raw_fd(), stage.as_ptr(), libc::AT_REMOVEDIR);
    }
    operation
}
