// Stage 4 incremental marker: baseline
mod contract;
mod json;

use json::{ensure, J, R};
use std::collections::BTreeMap;
use std::io::Read;
use std::os::fd::AsRawFd;
use std::os::unix::process::{CommandExt, ExitStatusExt};
use std::process::{Child, Command, Stdio};
use std::time::{Duration, Instant};

unsafe extern "C" {
    fn pear_process_identity(pid: i32, sec: *mut u64, usec: *mut u64) -> i32;
    fn proc_listpids(kind: u32, info: u32, buffer: *mut libc::c_void, size: i32) -> i32;
}
struct Config {
    root: String,
    entry: String,
    sha: String,
    timeout: u64,
    limit: usize,
    ready: bool,
    gap: bool,
}
struct Outcome {
    classification: &'static str,
    spawned: bool,
    reaped: bool,
    cleanup: &'static str,
    code: Option<i32>,
    signal: Option<i32>,
    out: usize,
    err: usize,
    native: bool,
}
impl Outcome {
    fn new(classification: &'static str, native: bool) -> Self {
        Self {
            classification,
            spawned: false,
            reaped: false,
            cleanup: "not_started",
            code: None,
            signal: None,
            out: 0,
            err: 0,
            native,
        }
    }
    fn emit(&self) -> i32 {
        let opt = |x: Option<i32>| x.map(|v| v.to_string()).unwrap_or("null".into());
        println!("{{\"experiment_version\":1,\"candidate\":\"rust\",\"fixture_only\":true,\"runtime_eligible\":false,\"host_architecture\":\"{}\",\"translated\":{},\"classification\":\"{}\",\"spawned\":{},\"reaped\":{},\"cleanup\":\"{}\",\"exit_code\":{},\"signal\":{},\"stdout_bytes\":{},\"stderr_bytes\":{}}}",if cfg!(target_arch="aarch64"){"arm64"}else{"unknown"},if self.native{"false"}else{"null"},self.classification,self.spawned,self.reaped,self.cleanup,opt(self.code),opt(self.signal),self.out,self.err);
        match self.classification {
            "success" => 0,
            "invalid_contract" => 1,
            "ineligible" | "observer_not_ready" => 3,
            _ => 4,
        }
    }
}
fn config() -> R<Config> {
    let args: Vec<String> = std::env::args_os()
        .skip(1)
        .map(|a| a.into_string().map_err(|_| ()))
        .collect::<R<_>>()?;
    ensure(args.len() == 14)?;
    let mut fields = BTreeMap::new();
    for p in args.chunks(2) {
        ensure(fields.insert(p[0].as_str(), p[1].as_str()).is_none())?;
    }
    ensure(fields.keys().all(|k| {
        [
            "--bundle-root",
            "--entry",
            "--fixture-sha256",
            "--timeout-ms",
            "--output-limit",
            "--observer-ready",
            "--observer-gap",
        ]
        .contains(k)
    }))?;
    let get = |k| fields.get(k).copied().ok_or(());
    let boolean = |k| match get(k)? {
        "yes" => Ok(true),
        "no" => Ok(false),
        _ => Err(()),
    };
    let timeout = get("--timeout-ms")?.parse().map_err(|_| ())?;
    ensure((100..=5000).contains(&timeout))?;
    let limit = get("--output-limit")?.parse().map_err(|_| ())?;
    ensure((256..=65536).contains(&limit))?;
    let sha = get("--fixture-sha256")?;
    ensure(
        sha.len() == 64
            && sha
                .bytes()
                .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b)),
    )?;
    Ok(Config {
        root: get("--bundle-root")?.into(),
        entry: get("--entry")?.into(),
        sha: sha.into(),
        timeout,
        limit,
        ready: boolean("--observer-ready")?,
        gap: boolean("--observer-gap")?,
    })
}
fn native_host() -> bool {
    if !cfg!(all(target_os = "macos", target_arch = "aarch64")) {
        return false;
    }
    let mut translated: i32 = 0;
    let mut len = std::mem::size_of::<i32>();
    let key = c"sysctl.proc_translated";
    let r = unsafe {
        libc::sysctlbyname(
            key.as_ptr(),
            (&mut translated as *mut i32).cast(),
            &mut len,
            std::ptr::null_mut(),
            0,
        )
    };
    (r == 0 && len == 4 && translated == 0)
        || (r != 0 && std::io::Error::last_os_error().raw_os_error() == Some(libc::ENOENT))
}
fn identity(pid: i32) -> R<(u64, u64)> {
    let (mut sec, mut usec) = (0, 0);
    ensure(unsafe { pear_process_identity(pid, &mut sec, &mut usec) } == 0)?;
    Ok((sec, usec))
}
fn exited(pid: i32) -> R<bool> {
    let mut info = unsafe { std::mem::zeroed::<libc::siginfo_t>() };
    let r = unsafe {
        libc::waitid(
            libc::P_PID,
            pid as u32,
            &mut info,
            libc::WEXITED | libc::WNOHANG | libc::WNOWAIT,
        )
    };
    if r != 0 && std::io::Error::last_os_error().raw_os_error() == Some(libc::EINTR) {
        return Ok(false);
    }
    ensure(r == 0)?;
    Ok(info.si_pid == pid)
}
// A zombie-only Darwin process group can return EPERM from killpg. Accept that
// case only while WNOWAIT reserves our exact child and the bounded kernel group
// enumeration confirms that no other member remains. Full/error results fail.
fn only_reserved_leader(pid: i32) -> bool {
    if exited(pid) != Ok(true) {
        return false;
    }
    let mut pids = [0i32; 256];
    let bytes = unsafe {
        proc_listpids(
            2,
            pid as u32,
            pids.as_mut_ptr().cast(),
            std::mem::size_of_val(&pids) as i32,
        )
    };
    if bytes <= 0 || bytes as usize >= std::mem::size_of_val(&pids) || bytes % 4 != 0 {
        return false;
    }
    pids[..bytes as usize / 4].iter().all(|p| *p == pid)
}
struct Pipe {
    data: Vec<u8>,
    count: usize,
    eof: bool,
}
impl Pipe {
    fn new() -> Self {
        Self {
            data: Vec::new(),
            count: 0,
            eof: false,
        }
    }
    fn drain(&mut self, reader: &mut Option<impl Read>, limit: usize) -> R<bool> {
        let Some(reader) = reader.as_mut() else {
            return Ok(false);
        };
        if self.eof {
            return Ok(false);
        }
        let mut b = [0u8; 8192];
        for _ in 0..32 {
            match reader.read(&mut b) {
                Ok(0) => {
                    self.eof = true;
                    break;
                }
                Ok(n) => {
                    self.count = self.count.saturating_add(n);
                    let keep = n.min((limit + 1).saturating_sub(self.data.len()));
                    self.data.extend_from_slice(&b[..keep]);
                    if self.count > limit {
                        return Ok(true);
                    }
                }
                Err(e) if e.kind() == std::io::ErrorKind::WouldBlock => break,
                Err(e) if e.kind() == std::io::ErrorKind::Interrupted => continue,
                Err(_) => return Err(()),
            }
        }
        Ok(false)
    }
}
fn nonblocking(fd: i32) -> bool {
    unsafe {
        let f = libc::fcntl(fd, libc::F_GETFL);
        f >= 0 && libc::fcntl(fd, libc::F_SETFL, f | libc::O_NONBLOCK) == 0
    }
}
fn run(cfg: Config) -> Outcome {
    let native = native_host();
    if !native {
        return Outcome::new("host_not_native", false);
    }
    let mut bundle = match contract::Bundle::new(&cfg.root) {
        Ok(x) => x,
        Err(_) => return Outcome::new("invalid_contract", native),
    };
    let (args, env, executable) = match bundle.validate(&cfg.entry, &cfg.sha) {
        Ok(x) => x,
        Err(_) => return Outcome::new("invalid_contract", native),
    };
    if !bundle.eligible {
        return Outcome::new("ineligible", native);
    }
    if !cfg.ready {
        return Outcome::new("observer_not_ready", native);
    }
    let mut command = Command::new(bundle.path.join("blobs/fixture-child"));
    command
        .args(&args)
        .env_clear()
        .envs(env)
        .current_dir(&bundle.path)
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
    // No allocations or non-async-signal-safe operations in the post-fork callback.
    unsafe {
        command.pre_exec(|| {
            if libc::setpgid(0, 0) != 0 {
                return Err(std::io::Error::last_os_error());
            }
            let mut mask = std::mem::zeroed::<libc::sigset_t>();
            libc::sigemptyset(&mut mask);
            if libc::sigprocmask(libc::SIG_SETMASK, &mask, std::ptr::null_mut()) != 0 {
                return Err(std::io::Error::last_os_error());
            }
            for signal in [libc::SIGTERM, libc::SIGPIPE, libc::SIGINT, libc::SIGCHLD] {
                if libc::signal(signal, libc::SIG_DFL) == libc::SIG_ERR {
                    return Err(std::io::Error::last_os_error());
                }
            }
            Ok(())
        });
    }
    // Reopen immediately before spawn. The descriptor is kept alive; bundle mutation
    // between this check and path-based exec remains an explicit prototype limitation.
    let fresh = match bundle.open("blobs/fixture-child") {
        Ok(f) => f,
        Err(_) => return Outcome::new("invalid_contract", native),
    };
    use std::os::unix::fs::MetadataExt;
    let same = match (fresh.metadata(), executable.metadata()) {
        (Ok(a), Ok(b)) => {
            a.dev() == b.dev()
                && a.ino() == b.ino()
                && a.len() == b.len()
                && a.mtime() == b.mtime()
                && a.mtime_nsec() == b.mtime_nsec()
        }
        _ => false,
    };
    if !same {
        return Outcome::new("invalid_contract", native);
    }
    let child = match command.spawn() {
        Ok(c) => c,
        Err(_) => return Outcome::new("spawn_failed", native),
    };
    supervise(child, &cfg, native, nonblocking)
}

// The callback is internal dependency injection for owned fault tests. Production
// always passes nonblocking; no public input can select a fault-injection path.
fn supervise(
    mut child: Child,
    cfg: &Config,
    native: bool,
    mut setup_pipe: impl FnMut(i32) -> bool,
) -> Outcome {
    let pid = child.id() as i32;
    let mut outcome = Outcome::new("internal_error", native);
    outcome.spawned = true;
    outcome.cleanup = "failed";
    let observed = identity(pid);
    let group = unsafe { libc::getpgid(pid) } == pid || exited(pid) == Ok(true);
    let mut stdout = Some(child.stdout.take().expect("owned pipe"));
    let mut stderr = Some(child.stderr.take().expect("owned pipe"));
    let mut out = Pipe::new();
    let mut err = Pipe::new();
    let started = Instant::now();
    let mut reason = None;
    // Evaluate both independently: short-circuiting could leave one pipe in
    // blocking mode. If either setup fails, close both ends before cleanup can
    // attempt a read. Bytes discarded this way are intentionally unobserved.
    let stdout_ready = setup_pipe(stdout.as_ref().expect("owned pipe").as_raw_fd());
    let stderr_ready = setup_pipe(stderr.as_ref().expect("owned pipe").as_raw_fd());
    let pipes_closed = !stdout_ready || !stderr_ready;
    if pipes_closed {
        drop(stdout.take());
        drop(stderr.take());
    }
    if (observed.is_err() && exited(pid) != Ok(true)) || !group || pipes_closed {
        reason = Some("internal_error");
    }
    while reason.is_none() {
        match (
            out.drain(&mut stdout, cfg.limit),
            err.drain(&mut stderr, cfg.limit),
        ) {
            (Ok(a), Ok(b)) => {
                if a || b {
                    reason = Some("output_limit");
                    break;
                }
            }
            _ => {
                reason = Some("internal_error");
                break;
            }
        }
        match exited(pid) {
            Ok(true) if out.eof && err.eof => break,
            Ok(_) => (),
            Err(_) => {
                reason = Some("cleanup_failed");
                break;
            }
        }
        if started.elapsed() >= Duration::from_millis(cfg.timeout) {
            reason = Some("timeout");
            break;
        }
        std::thread::sleep(Duration::from_millis(2));
    }
    // Keep the unreaped child reservation until the process group is terminated.
    // Even a rapidly exiting leader cannot have its PID/PGID reused here.
    let identity_ok = exited(pid) == Ok(true)
        || observed
            .as_ref()
            .is_ok_and(|old| identity(pid).is_ok_and(|now| now == *old));
    let signal_result = if group && identity_ok {
        unsafe { libc::kill(-pid, libc::SIGKILL) }
    } else {
        unsafe { libc::kill(pid, libc::SIGKILL) }
    };
    let signal_error = if signal_result < 0 {
        std::io::Error::last_os_error().raw_os_error()
    } else {
        None
    };
    let mut cleanup_ok = (signal_result == 0
        || signal_error == Some(libc::ESRCH)
        || (signal_error == Some(libc::EPERM) && only_reserved_leader(pid)))
        && group
        && identity_ok;
    let cleanup_started = Instant::now();
    let mut ready = false;
    while cleanup_started.elapsed() < Duration::from_secs(2) {
        if out.drain(&mut stdout, cfg.limit).is_err() || err.drain(&mut stderr, cfg.limit).is_err()
        {
            cleanup_ok = false;
        }
        match exited(pid) {
            Ok(true) => {
                ready = true;
                break;
            }
            Ok(false) => (),
            Err(_) => {
                cleanup_ok = false;
                break;
            }
        }
        std::thread::sleep(Duration::from_millis(2));
    }
    if ready {
        match child.wait() {
            Ok(status) => {
                outcome.reaped = true;
                outcome.code = status.code();
                outcome.signal = status.signal();
            }
            Err(_) => cleanup_ok = false,
        }
    } else {
        cleanup_ok = false;
    }
    while !pipes_closed
        && cleanup_started.elapsed() < Duration::from_secs(2)
        && (!out.eof || !err.eof)
    {
        if out.drain(&mut stdout, cfg.limit).is_err() || err.drain(&mut stderr, cfg.limit).is_err()
        {
            cleanup_ok = false;
            break;
        }
        // After a limit breach retain no further bytes, but read enough to observe EOF.
        if out.count > cfg.limit || err.count > cfg.limit {
            break;
        }
        if !out.eof || !err.eof {
            std::thread::sleep(Duration::from_millis(2));
        }
    }
    outcome.out = out.count;
    outcome.err = err.count;
    if !pipes_closed && out.count <= cfg.limit && err.count <= cfg.limit {
        cleanup_ok &= out.eof && err.eof;
    }
    outcome.cleanup = if cleanup_ok && outcome.reaped {
        "passed"
    } else {
        "failed"
    };
    outcome.classification = if outcome.cleanup != "passed" {
        "cleanup_failed"
    } else if let Some(r) = reason {
        r
    } else if out.count > cfg.limit || err.count > cfg.limit {
        "output_limit"
    } else if cfg.gap {
        "observer_gap"
    } else if outcome.signal.is_some() {
        "signal_exit"
    } else if outcome.code != Some(0) {
        "nonzero_exit"
    } else if json::parse(&out.data).ok().is_some_and(|v| {
        v.keys(&["fixture", "ok"]).is_ok()
            && v.get("fixture").and_then(J::i) == Ok(1)
            && v.get("ok").and_then(J::b) == Ok(true)
    }) {
        "success"
    } else {
        "child_output_invalid"
    };
    outcome
}
fn main() {
    std::panic::set_hook(Box::new(|_| {}));
    let outcome = match config() {
        Ok(cfg) => run(cfg),
        Err(_) => {
            Outcome::new("invalid_contract", native_host()).emit();
            std::process::exit(2)
        }
    };
    std::process::exit(outcome.emit());
}

#[cfg(test)]
mod supervisor_tests;
