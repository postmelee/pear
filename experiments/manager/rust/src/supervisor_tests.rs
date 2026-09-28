//! Owned fault-injection tests; excluded from the production manager binary.
use super::*;
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};

static NEXT_DIRECTORY: AtomicU64 = AtomicU64::new(0);

struct Sentinel(Child);
impl Drop for Sentinel {
    fn drop(&mut self) {
        // This guard still owns its unreaped direct child. No process-name or
        // post-reap process-group signal is used when an assertion fails.
        if self.0.try_wait().ok().flatten().is_none() {
            let _ = self.0.kill();
            let _ = self.0.wait();
        }
    }
}

fn spawn_fixture(executable: &Path, root: &Path, mode: &str, pipes: bool) -> Child {
    let mut command = Command::new(executable);
    command
        .arg(mode)
        .current_dir(root)
        .env_clear()
        .stdin(Stdio::null())
        .stdout(if pipes { Stdio::piped() } else { Stdio::null() })
        .stderr(if pipes { Stdio::piped() } else { Stdio::null() });
    unsafe {
        command.pre_exec(|| {
            if libc::setpgid(0, 0) != 0 {
                return Err(std::io::Error::last_os_error());
            }
            Ok(())
        });
    }
    command.spawn().expect("owned fixture spawn")
}

fn trace(path: &Path) -> Option<(i32, u64, u64)> {
    let bytes = fs::read(path).ok()?;
    let value = json::parse(&bytes).ok()?;
    let pid = value.get("pid").ok()?.i().ok()?;
    let sec = value.get("started_sec").ok()?.i().ok()?;
    let usec = value.get("started_usec").ok()?.i().ok()?;
    if pid <= 0 || pid > i32::MAX as i64 || sec <= 0 || !(0..1_000_000).contains(&usec) {
        return None;
    }
    Some((pid as i32, sec as u64, usec as u64))
}

fn identity_gone(expected: (i32, u64, u64)) -> bool {
    let deadline = Instant::now() + Duration::from_secs(2);
    loop {
        let (mut sec, mut usec) = (0, 0);
        let code = unsafe { pear_process_identity(expected.0, &mut sec, &mut usec) };
        if code == libc::ESRCH || (code == 0 && (sec, usec) != (expected.1, expected.2)) {
            return true;
        }
        if code != 0 || Instant::now() >= deadline {
            return false;
        }
        std::thread::sleep(Duration::from_millis(2));
    }
}

fn setup_failure(failed_call: usize) {
    assert!(native_host());
    // Test-only configuration: the production CLI and environment never read it.
    let executable = PathBuf::from(
        std::env::var_os("PEAR_MANAGER_TEST_FIXTURE").expect("set the shared owned fixture path"),
    );
    assert!(executable.is_absolute() && executable.is_file());
    let counter = NEXT_DIRECTORY.fetch_add(1, Ordering::Relaxed);
    let nanos = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    let root = PathBuf::from(format!(
        "/private/tmp/pear-rust-pipe-test-{}-{counter}-{nanos}",
        std::process::id()
    ));
    fs::create_dir(&root).expect("fresh owned test root");
    fs::create_dir_all(root.join("state/prefix")).unwrap();
    let mut sentinel = Sentinel(spawn_fixture(&executable, &root, "sentinel", false));
    let sentinel_identity = identity(sentinel.0.id() as i32).expect("sentinel identity");
    let child = spawn_fixture(&executable, &root, "descendant_pipe", true);
    let direct_pid = child.id() as i32;
    let cfg = Config {
        root: String::new(),
        entry: String::new(),
        sha: String::new(),
        timeout: 300,
        limit: 4096,
        ready: true,
        gap: false,
    };
    let mut calls = 0;
    let mut read_fds = Vec::new();
    let mut held_pipe_observed = false;
    let mut direct_trace = None;
    let mut descendant_trace = None;
    let mut injected_at = None;
    let mut injected_was_blocking = false;
    let outcome = supervise(child, &cfg, true, |fd| {
        calls += 1;
        read_fds.push(fd);
        if calls == failed_call {
            // Hold the descriptor in blocking mode while the existing fixture's
            // descendant retains both pipes. This is a real process, not a mock
            // reader returning WouldBlock regardless of descriptor state.
            let flags = unsafe { libc::fcntl(fd, libc::F_GETFL) };
            injected_was_blocking = flags >= 0 && flags & libc::O_NONBLOCK == 0;
            let deadline = Instant::now() + Duration::from_secs(3);
            while Instant::now() < deadline {
                direct_trace = trace(&root.join("state/prefix/child.json"));
                descendant_trace = trace(&root.join("state/prefix/descendant.json"));
                if direct_trace.is_some() && descendant_trace.is_some() {
                    held_pipe_observed = true;
                    break;
                }
                std::thread::sleep(Duration::from_millis(2));
            }
            injected_at = Some(Instant::now());
            false
        } else {
            nonblocking(fd)
        }
    });
    assert_eq!(calls, 2, "both pipe setups must be evaluated independently");
    for fd in read_fds {
        assert_eq!(unsafe { libc::fcntl(fd, libc::F_GETFD) }, -1);
        assert_eq!(
            std::io::Error::last_os_error().raw_os_error(),
            Some(libc::EBADF)
        );
    }
    assert!(
        injected_was_blocking,
        "the failed setup must leave a real blocking pipe"
    );
    assert!(
        held_pipe_observed,
        "owned descendant must retain the pipes at injection"
    );
    assert!(injected_at.unwrap().elapsed() < Duration::from_secs(2));
    assert_eq!(outcome.classification, "internal_error");
    assert!(outcome.spawned && outcome.reaped);
    assert_eq!(outcome.cleanup, "passed");
    assert_eq!(
        (outcome.out, outcome.err),
        (0, 0),
        "closed streams were not read"
    );
    assert_eq!(
        exited(direct_pid),
        Err(()),
        "the direct child is already reaped"
    );
    assert!(identity_gone(direct_trace.unwrap()));
    assert!(identity_gone(descendant_trace.unwrap()));
    assert!(sentinel.0.try_wait().unwrap().is_none());
    assert_eq!(identity(sentinel.0.id() as i32).unwrap(), sentinel_identity);
    drop(sentinel);
    // Preserve the test-owned traces on assertion failure for local diagnosis.
    fs::remove_dir_all(root).unwrap();
}

#[test]
fn first_nonblocking_setup_failure_closes_pipes_and_reaps_owned_child() {
    setup_failure(1);
}

#[test]
fn second_nonblocking_setup_failure_closes_pipes_and_reaps_owned_child() {
    setup_failure(2);
}
