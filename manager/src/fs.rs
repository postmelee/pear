//! Descriptor-relative traversal adapted from #3 Bundle::new/directory/open/read.
use crate::{json, native};
use std::{
    ffi::CString,
    fs::File,
    io::Read,
    os::fd::{AsRawFd, FromRawFd},
    os::unix::fs::MetadataExt,
};
#[derive(Debug)]
pub struct Error {
    pub code: &'static str,
    pub errno: Option<i32>,
}
pub type Result<T> = std::result::Result<T, Error>;
impl Error {
    pub fn code(code: &'static str) -> Self {
        Self { code, errno: None }
    }
    pub fn io(error: std::io::Error) -> Self {
        Self {
            code: "filesystem_error",
            errno: error.raw_os_error(),
        }
    }
}
impl From<()> for Error {
    fn from(_: ()) -> Self {
        Self::code("contract_invalid")
    }
}
impl From<std::io::Error> for Error {
    fn from(error: std::io::Error) -> Self {
        Self::io(error)
    }
}
pub fn require(value: bool, code: &'static str) -> Result<()> {
    if value {
        Ok(())
    } else {
        Err(Error::code(code))
    }
}
pub fn relative(s: &str) -> Result<()> {
    require(
        !s.is_empty()
            && s.len() <= 512
            && !s.starts_with(['/', '~'])
            && !s.contains(['%', '\\', ':'])
            && !s.chars().any(|c| c <= '\u{1f}' || c == '\u{7f}')
            && s.split('/').count() <= 32
            && s.split('/').all(|p| !p.is_empty() && p != "." && p != ".."),
        "invalid_path",
    )
}
pub fn c(s: &str) -> Result<CString> {
    CString::new(s).map_err(|_| Error::code("invalid_path"))
}
pub fn owned_fd(fd: i32) -> Result<File> {
    if fd < 0 {
        Err(Error::io(std::io::Error::last_os_error()))
    } else {
        Ok(unsafe { File::from_raw_fd(fd) })
    }
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Identity {
    pub device: u64,
    pub inode: u64,
}
pub fn identity(file: &File) -> Result<Identity> {
    let m = file.metadata()?;
    Ok(Identity {
        device: m.dev(),
        inode: m.ino(),
    })
}
pub struct Root {
    pub file: File,
}
impl Root {
    pub fn open(path: &str) -> Result<Self> {
        require(
            path.starts_with('/') && !path.ends_with('/') && path.len() <= 4096,
            "invalid_root",
        )?;
        let mut file = owned_fd(unsafe {
            libc::open(
                c("/")?.as_ptr(),
                libc::O_RDONLY | libc::O_DIRECTORY | libc::O_CLOEXEC,
            )
        })?;
        for part in path[1..].split('/') {
            relative(part)?;
            file = owned_fd(unsafe {
                libc::openat(
                    file.as_raw_fd(),
                    c(part)?.as_ptr(),
                    libc::O_RDONLY | libc::O_DIRECTORY | libc::O_NOFOLLOW | libc::O_CLOEXEC,
                )
            })?;
        }
        Ok(Self { file })
    }
    pub fn directory(&self, path: &str) -> Result<File> {
        relative(path)?;
        let mut file = self.file.try_clone()?;
        for part in path.split('/') {
            file = owned_fd(unsafe {
                libc::openat(
                    file.as_raw_fd(),
                    c(part)?.as_ptr(),
                    libc::O_RDONLY | libc::O_DIRECTORY | libc::O_NOFOLLOW | libc::O_CLOEXEC,
                )
            })?;
        }
        Ok(file)
    }
    pub fn parent(&self, path: &str) -> Result<(File, CString)> {
        relative(path)?;
        let (parent, name) = match path.rsplit_once('/') {
            Some((parent, name)) => (self.directory(parent)?, name),
            None => (self.file.try_clone()?, path),
        };
        Ok((parent, c(name)?))
    }
    pub fn open_file(&self, path: &str) -> Result<File> {
        let (parent, name) = self.parent(path)?;
        let file = owned_fd(unsafe {
            libc::openat(
                parent.as_raw_fd(),
                name.as_ptr(),
                libc::O_RDONLY | libc::O_NONBLOCK | libc::O_NOFOLLOW | libc::O_CLOEXEC,
            )
        })?;
        let m = file.metadata()?;
        require(m.is_file() && m.nlink() == 1, "nonregular_or_aliased_file")?;
        Ok(file)
    }
    pub fn read_record(&self, path: &str, remaining: u64) -> Result<(Vec<u8>, String, Identity)> {
        let mut file = self.open_file(path)?;
        let before = file.metadata()?;
        require(
            before.len() <= 262144 && before.len() <= remaining,
            "json_size_limit",
        )?;
        let (digest, size) = native::sha256(&file, 262144.min(remaining))?;
        let mut bytes = Vec::new();
        (&mut file).take(262145).read_to_end(&mut bytes)?;
        let after = file.metadata()?;
        require(
            bytes.len() as u64 == size
                && before.len() == after.len()
                && before.mtime() == after.mtime()
                && before.mtime_nsec() == after.mtime_nsec()
                && before.ctime() == after.ctime()
                && before.ctime_nsec() == after.ctime_nsec(),
            "file_changed",
        )?;
        Ok((bytes, hex(&digest), identity(&file)?))
    }
    pub fn json(&self, path: &str) -> Result<json::J> {
        let (bytes, _, _) = self.read_record(path, 262144)?;
        Ok(json::parse(&bytes)?)
    }
    pub fn private(&self) -> Result<()> {
        let m = self.file.metadata()?;
        require(
            m.uid() == unsafe { libc::geteuid() } && m.mode() & 0o077 == 0,
            "state_root_not_private",
        )
    }
}
pub fn hex(bytes: &[u8]) -> String {
    bytes.iter().map(|b| format!("{b:02x}")).collect()
}

/// Metadata-only descriptor scan, bounded like the independent v1 SafeRoot checker.
pub fn check_mutable(
    directory: File,
    immutable: &std::collections::BTreeSet<(u64, u64)>,
) -> Result<()> {
    fn scan(
        file: File,
        depth: usize,
        count: &mut usize,
        immutable: &std::collections::BTreeSet<(u64, u64)>,
    ) -> Result<()> {
        use std::os::fd::IntoRawFd;
        require(depth <= 32, "state_scan_limit")?;
        let fd = file.into_raw_fd();
        let dir = unsafe { libc::fdopendir(fd) };
        if dir.is_null() {
            let error = Error::io(std::io::Error::last_os_error());
            unsafe { libc::close(fd) };
            return Err(error);
        }
        struct Directory(*mut libc::DIR);
        impl Drop for Directory {
            fn drop(&mut self) {
                unsafe {
                    libc::closedir(self.0);
                }
            }
        }
        let _owner = Directory(dir);
        loop {
            unsafe {
                *libc::__error() = 0;
            }
            let entry = unsafe { libc::readdir(dir) };
            if entry.is_null() {
                let error = std::io::Error::last_os_error();
                if error.raw_os_error() != Some(0) {
                    return Err(error.into());
                }
                break;
            }
            let name = unsafe { std::ffi::CStr::from_ptr((*entry).d_name.as_ptr()) };
            if name.to_bytes() == b"." || name.to_bytes() == b".." {
                continue;
            }
            *count += 1;
            require(*count <= 4096, "state_scan_limit")?;
            let child = owned_fd(unsafe {
                libc::openat(
                    fd,
                    name.as_ptr(),
                    libc::O_RDONLY | libc::O_NOFOLLOW | libc::O_NONBLOCK | libc::O_CLOEXEC,
                )
            })?;
            let m = child.metadata()?;
            require(
                !immutable.contains(&(m.dev(), m.ino())),
                "immutable_path_overlap",
            )?;
            if m.is_dir() {
                scan(child, depth + 1, count, immutable)?;
            } else {
                require(m.is_file() && m.nlink() == 1, "not_regular_or_aliased_file")?;
            }
        }
        Ok(())
    }
    scan(directory, 0, &mut 0, immutable)
}
