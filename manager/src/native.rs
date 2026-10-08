//! Header-checked Darwin calls. These helpers do not grant ownership or launch authority.
use std::ffi::CStr;
use std::io;
use std::os::fd::AsFd;
use std::os::fd::AsRawFd;

unsafe extern "C" {
    fn pear_mount_info(fd: i32, flags: *mut u64, fsid0: *mut i32, fsid1: *mut i32) -> i32;
    fn pear_process_identity(pid: i32, seconds: *mut u64, micros: *mut u64) -> i32;
    fn pear_stage_directory(parent: i32, name: *mut u8, capacity: usize) -> i32;
    fn pear_sha256_fd(fd: i32, limit: u64, digest: *mut u8, bytes: *mut u64) -> i32;
}
fn checked(code: i32) -> io::Result<()> {
    if code == 0 {
        Ok(())
    } else {
        Err(io::Error::from_raw_os_error(code))
    }
}
pub fn process_identity(pid: i32) -> io::Result<(u64, u64)> {
    let (mut seconds, mut micros) = (0, 0);
    // SAFETY: fixed-width caller-owned outputs live throughout the call; no pointers retained.
    checked(unsafe { pear_process_identity(pid, &mut seconds, &mut micros) })?;
    Ok((seconds, micros))
}
pub fn stage_directory(parent: &impl AsFd) -> io::Result<std::ffi::CString> {
    let mut name = *b"stage.XXXXXX\0";
    // SAFETY: a live borrowed FD and writable, NUL-terminated fixed-size template.
    checked(unsafe {
        pear_stage_directory(parent.as_fd().as_raw_fd(), name.as_mut_ptr(), name.len())
    })?;
    Ok(CStr::from_bytes_with_nul(&name)
        .expect("fixed native template")
        .to_owned())
}
pub fn sha256(file: &impl AsFd, limit: u64) -> io::Result<([u8; 32], u64)> {
    let (mut digest, mut bytes) = ([0; 32], 0);
    // SAFETY: borrowed FD and correctly sized outputs; C retains none and uses pread.
    checked(unsafe {
        pear_sha256_fd(
            file.as_fd().as_raw_fd(),
            limit,
            digest.as_mut_ptr(),
            &mut bytes,
        )
    })?;
    Ok((digest, bytes))
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::{Read, Seek, SeekFrom};
    #[test]
    fn hash_preserves_offset_and_returns_exact_bytes() {
        let mut file = std::fs::File::open("Cargo.toml").unwrap();
        file.seek(SeekFrom::Start(7)).unwrap();
        let (_, bytes) = sha256(&file, 4096).unwrap();
        assert_eq!(bytes, file.metadata().unwrap().len());
        assert_eq!(file.stream_position().unwrap(), 7);
        let mut one = [0];
        file.read_exact(&mut one).unwrap();
        assert_eq!(one[0], std::fs::read("Cargo.toml").unwrap()[7]);
    }
    #[test]
    fn invalid_descriptor_clears_outputs_and_keeps_errno() {
        let (mut digest, mut bytes) = ([255; 32], 999);
        let error = unsafe { pear_sha256_fd(-1, 10, digest.as_mut_ptr(), &mut bytes) };
        assert_eq!(error, libc::EBADF);
        assert_eq!(digest, [0; 32]);
        assert_eq!(bytes, 0);
    }
    #[test]
    fn invalid_staging_template_refuses_without_mutation() {
        let mut name = *b"../escape\0";
        let error = unsafe { pear_stage_directory(-1, name.as_mut_ptr(), name.len()) };
        assert_eq!(error, libc::EINVAL);
        assert_eq!(&name, b"../escape\0");
    }
}

pub fn mount_info(file: &impl AsFd) -> io::Result<(u64, i32, i32)> {
    let (mut flags, mut fsid0, mut fsid1) = (0, 0, 0);
    checked(unsafe {
        pear_mount_info(file.as_fd().as_raw_fd(), &mut flags, &mut fsid0, &mut fsid1)
    })?;
    Ok((flags, fsid0, fsid1))
}

pub fn sha256_bytes(bytes: &[u8]) -> io::Result<[u8; 32]> {
    unsafe extern "C" {
        fn pear_sha256_bytes(data: *const u8, size: usize, digest: *mut u8) -> i32;
    }
    let mut digest = [0; 32];
    // SAFETY: borrowed byte slice and fixed caller-owned output; no pointer retained.
    checked(unsafe { pear_sha256_bytes(bytes.as_ptr(), bytes.len(), digest.as_mut_ptr()) })?;
    Ok(digest)
}
