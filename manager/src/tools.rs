//! Bounded system-tool inspection using #3 nonblocking pipe/drain limits.
use crate::fs::{require, Error, Result};
use std::{
    io::{Read, Write},
    os::fd::AsRawFd,
    process::{Command, Stdio},
    time::{Duration, Instant},
};
struct Pipe {
    data: Vec<u8>,
    eof: bool,
}
impl Pipe {
    fn drain(&mut self, reader: &mut impl Read) -> Result<()> {
        let mut bytes = [0; 8192];
        for _ in 0..8 {
            match reader.read(&mut bytes) {
                Ok(0) => {
                    self.eof = true;
                    break;
                }
                Ok(n) => {
                    require(self.data.len() + n <= 262144, "tool_output_limit")?;
                    self.data.extend_from_slice(&bytes[..n]);
                }
                Err(e) if e.kind() == std::io::ErrorKind::WouldBlock => break,
                Err(e) if e.kind() == std::io::ErrorKind::Interrupted => continue,
                Err(e) => return Err(e.into()),
            }
        }
        Ok(())
    }
}
pub fn capture(command: &mut Command) -> Result<Vec<u8>> {
    capture_input(command, None)
}
pub fn capture_input(command: &mut Command, input: Option<&[u8]>) -> Result<Vec<u8>> {
    command
        .env_clear()
        .env("PATH", "/usr/bin:/bin:/usr/sbin:/sbin")
        .env("LC_ALL", "C")
        .stdin(if input.is_some() {
            Stdio::piped()
        } else {
            Stdio::null()
        })
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
    let mut child = command.spawn()?;
    let mut writer = child.stdin.take();
    let mut sent = 0;
    let mut out = child.stdout.take().ok_or(Error::code("tool_pipe"))?;
    let mut err = child.stderr.take().ok_or(Error::code("tool_pipe"))?;
    let result = (|| {
        for fd in [
            Some(out.as_raw_fd()),
            Some(err.as_raw_fd()),
            writer.as_ref().map(AsRawFd::as_raw_fd),
        ]
        .into_iter()
        .flatten()
        {
            let flags = unsafe { libc::fcntl(fd, libc::F_GETFL) };
            require(
                flags >= 0
                    && unsafe { libc::fcntl(fd, libc::F_SETFL, flags | libc::O_NONBLOCK) } == 0,
                "tool_pipe",
            )?;
        }
        let start = Instant::now();
        let mut a = Pipe {
            data: Vec::new(),
            eof: false,
        };
        let mut b = Pipe {
            data: Vec::new(),
            eof: false,
        };
        loop {
            if let (Some(w), Some(input)) = (writer.as_mut(), input) {
                match w.write(&input[sent..]) {
                    Ok(n) => sent += n,
                    Err(e) if e.kind() == std::io::ErrorKind::WouldBlock => (),
                    Err(e) if e.kind() == std::io::ErrorKind::Interrupted => (),
                    Err(e) => return Err(e.into()),
                }
                if sent == input.len() {
                    writer.take();
                }
            }
            a.drain(&mut out)?;
            b.drain(&mut err)?;
            if let Some(status) = child.try_wait()? {
                if a.eof && b.eof {
                    require(status.success(), "tool_failed")?;
                    return Ok(a.data);
                }
            }
            require(start.elapsed() < Duration::from_secs(10), "tool_deadline")?;
            std::thread::sleep(Duration::from_millis(5));
        }
    })();
    if result.is_err() {
        let _ = child.kill();
        let _ = child.wait();
    }
    result
}
