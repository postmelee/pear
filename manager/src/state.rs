//! Private run journal and canonical context lease; never signal a recorded PID.
use crate::{
    activation,
    encoding::encode,
    fs::{self, Error, Result, Root, require},
    json::J,
    native,
};
use std::{
    collections::BTreeMap,
    fs::File,
    io::Write,
    os::{fd::AsRawFd, unix::fs::MetadataExt},
};
pub struct Context {
    pub root: Root,
    _lease: File,
    pub capture: String,
    request: String,
    run_id: String,
    pub id: String,
}
impl Context {
    pub fn open(state: &Root, id: &str, request: &str, run_id: &str) -> Result<Self> {
        crate::contract::id(&J::Str(id.into()))?;
        state.private()?;
        let root = Root {
            file: state.directory(&format!("contexts/{id}"))?,
        };
        root.private()?;
        let lease = activation::private_file(&root, ".pear-lease")?;
        lease.try_lock().map_err(|e| match e {
            std::fs::TryLockError::WouldBlock => Error::code("context_busy"),
            std::fs::TryLockError::Error(e) => Error::io(e),
        })?;
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
                        && previous.get("state")?.s()? == "clean",
                    "context_incomplete",
                )?;
            }
            Err(e) if e.errno == Some(libc::ENOENT) => (),
            Err(e) => return Err(e),
        }
        let mut random = [0u8; 16];
        unsafe { libc::arc4random_buf(random.as_mut_ptr().cast(), random.len()) };
        Ok(Self {
            root,
            _lease: lease,
            capture: format!("capture-{}", fs::hex(&random)),
            request: request.into(),
            run_id: run_id.into(),
            id: id.into(),
        })
    }
    pub fn publish(&self, status: &str) -> Result<()> {
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
            fields.insert(k.into(), J::Str(v.into()));
        }
        for (k, v) in [
            ("journal_version", 1),
            ("owner_pid", std::process::id() as i64),
            ("owner_started_sec", sec as i64),
            ("owner_started_usec", usec as i64),
        ] {
            fields.insert(k.into(), J::Int(v));
        }
        let bytes = encode(&J::Obj(fields));
        let stage = native::stage_directory(&self.root.file)?;
        let dir = self
            .root
            .directory(stage.to_str().map_err(|_| Error::code("invalid_stage"))?)?;
        let result = (|| {
            let mut f = fs::owned_fd(unsafe {
                libc::openat(
                    dir.as_raw_fd(),
                    c"journal".as_ptr(),
                    libc::O_WRONLY
                        | libc::O_CREAT
                        | libc::O_EXCL
                        | libc::O_CLOEXEC
                        | libc::O_NOFOLLOW,
                    0o600,
                )
            })?;
            f.write_all(bytes.as_bytes())?;
            f.sync_all()?;
            dir.sync_all()?;
            if unsafe {
                libc::renameat(
                    dir.as_raw_fd(),
                    c"journal".as_ptr(),
                    self.root.file.as_raw_fd(),
                    c".pear-journal.json".as_ptr(),
                )
            } != 0
            {
                return Err(std::io::Error::last_os_error().into());
            }
            self.root.file.sync_all()?;
            Ok(())
        })();
        unsafe {
            libc::unlinkat(dir.as_raw_fd(), c"journal".as_ptr(), 0);
            libc::unlinkat(
                self.root.file.as_raw_fd(),
                stage.as_ptr(),
                libc::AT_REMOVEDIR,
            );
        }
        result
    }
    pub fn work_descriptor(&self) -> Result<File> {
        self.root.file.try_clone().map_err(Error::io)
    }
}
