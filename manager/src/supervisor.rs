//! Foreground owned-child supervision adapted from #3; no persisted-PID cleanup.
use crate::{
    fs::Result,
    json::{R, ensure},
    observer::Session,
    state::Context,
};
use std::{
    io::Read,
    os::{
        fd::AsRawFd,
        unix::process::{CommandExt, ExitStatusExt},
    },
    process::{Child, Command, Stdio},
    sync::atomic::{AtomicBool, Ordering},
    time::{Duration, Instant},
};
unsafe extern "C" {
    fn pear_process_identity(pid: i32, sec: *mut u64, usec: *mut u64) -> i32;
    fn proc_listpids(kind: u32, info: u32, buffer: *mut libc::c_void, size: i32) -> i32;
}
static CANCELLED: AtomicBool = AtomicBool::new(false);
extern "C" fn request_cancel(_: i32) {
    CANCELLED.store(true, Ordering::Relaxed);
}
pub fn cancelled() -> bool {
    CANCELLED.load(Ordering::Relaxed)
}
pub fn install_cancellation() -> Result<()> {
    let mut child_action = unsafe { std::mem::zeroed::<libc::sigaction>() };
    child_action.sa_sigaction = libc::SIG_DFL;
    unsafe {
        libc::sigemptyset(&mut child_action.sa_mask);
    };
    if unsafe { libc::sigaction(libc::SIGCHLD, &child_action, std::ptr::null_mut()) } != 0 {
        return Err(std::io::Error::last_os_error().into());
    }
    for signal in [libc::SIGINT, libc::SIGTERM] {
        let mut action = unsafe { std::mem::zeroed::<libc::sigaction>() };
        action.sa_sigaction = request_cancel as *const () as usize;
        unsafe {
            libc::sigemptyset(&mut action.sa_mask);
        };
        if unsafe { libc::sigaction(signal, &action, std::ptr::null_mut()) } != 0 {
            return Err(std::io::Error::last_os_error().into());
        }
    }
    Ok(())
}
pub struct Config {
    pub timeout: u64,
    pub limit: usize,
}
pub struct Outcome {
    pub classification: &'static str,
    pub spawned: bool,
    pub reaped: bool,
    pub cleanup: &'static str,
    pub code: Option<i32>,
    pub signal: Option<i32>,
    pub out: usize,
    pub err: usize,
    pub native: bool,
    pub native_error: Option<i32>,
    pub observation_complete: bool,
}
impl Outcome {
    pub fn new(classification: &'static str, native: bool) -> Self {
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
            native_error: None,
            observation_complete: false,
        }
    }
    pub fn emit(&self) -> i32 {
        let opt = |n: Option<i32>| n.map_or("null".into(), |n| n.to_string());
        println!(
            "{{\"diagnostic_version\":1,\"fixture_only\":true,\"runtime_eligible\":false,\"host_architecture\":\"arm64\",\"translated\":{},\"classification\":\"{}\",\"spawned\":{},\"reaped\":{},\"cleanup\":\"{}\",\"exit_code\":{},\"signal\":{},\"stdout_bytes\":{},\"stderr_bytes\":{},\"native_error\":{},\"observation_complete\":{}}}",
            if self.native { "false" } else { "null" },
            self.classification,
            self.spawned,
            self.reaped,
            self.cleanup,
            opt(self.code),
            opt(self.signal),
            self.out,
            self.err,
            opt(self.native_error),
            self.observation_complete
        );
        match self.classification {
            "success" => 0,
            "invalid_contract" => 1,
            "ineligible" | "observer_not_ready" | "context_incomplete" | "context_busy" => 3,
            _ => 4,
        }
    }
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
fn supervise_with_signal(
    mut child: Child,
    cfg: &Config,
    native: bool,
    mut setup_pipe: impl FnMut(i32) -> bool,
    mut observer: Option<&mut crate::observer::Session>,
    journal: Option<&crate::state::Context>,
    mut signal_owned: impl FnMut(i32, i32) -> i32,
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
    if let Some(peer) = observer.as_mut() {
        if let Ok(generation) = observed {
            if let Err(e) = peer.spawned(pid, generation) {
                outcome.native_error = e.errno;
                reason = Some("observer_gap");
            }
        } else {
            reason = Some("observer_gap");
        }
    }
    while reason.is_none() {
        if cancelled() {
            reason = Some("cancelled");
            break;
        }
        if let Some(peer) = observer.as_mut() {
            peer.service();
            if let Some(e) = peer.failure.as_ref() {
                outcome.native_error = e.errno;
                reason = Some("observer_gap");
                break;
            }
        }
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
    if let Some(journal) = journal {
        if let Err(e) = journal.publish("cleanup_pending") {
            outcome.native_error = e.errno;
            reason = Some("journal_failed");
        }
    }
    // Keep the unreaped child reservation until the process group is terminated.
    // Even a rapidly exiting leader cannot have its PID/PGID reused here.
    // After the owned group signal, reap the leader promptly: waiting for orphan
    // kernel records to disappear first can itself delay their reparenting/reap.
    let identity_ok = exited(pid) == Ok(true)
        || observed
            .as_ref()
            .is_ok_and(|old| identity(pid).is_ok_and(|now| now == *old));
    let signal_result = if group && identity_ok {
        signal_owned(-pid, libc::SIGKILL)
    } else {
        signal_owned(pid, libc::SIGKILL)
    };
    let signal_error = if signal_result < 0 {
        std::io::Error::last_os_error().raw_os_error()
    } else {
        None
    };
    outcome.native_error = signal_error.or(outcome.native_error);
    let cleanup_started = Instant::now();
    let mut reserved_only = only_reserved_leader(pid);
    // Darwin can briefly retain a killed orphan's group entry. Preserve the
    // original EPERM and the leader reservation; only accept the original
    // zombie-leader exception after a fresh bounded enumeration confirms it.
    if signal_error == Some(libc::EPERM) && exited(pid) == Ok(true) {
        while !reserved_only && cleanup_started.elapsed() < Duration::from_millis(250) {
            std::thread::sleep(Duration::from_millis(2));
            reserved_only = only_reserved_leader(pid);
        }
    }
    if signal_result < 0 && signal_error != Some(libc::ESRCH) && !reserved_only && identity_ok {
        let _ = child.kill();
    }
    let mut cleanup_ok = (signal_result == 0
        || signal_error == Some(libc::ESRCH)
        || (signal_error == Some(libc::EPERM) && reserved_only))
        && group
        && identity_ok;
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
    if let Some(peer) = observer.as_mut() {
        if outcome.reaped && peer.failure.is_none() {
            if let Err(e) = peer.exited() {
                peer.failure = Some(e);
            }
        }
        while cleanup_started.elapsed() < Duration::from_secs(2)
            && peer.failure.is_none()
            && (!peer.complete || peer.transport.pending())
        {
            peer.service();
            if cancelled() {
                reason = Some("cancelled");
            }
            std::thread::sleep(Duration::from_millis(2));
        }
        if peer
            .failure
            .as_ref()
            .is_some_and(|e| e.code == "observer_scope_incomplete")
        {
            cleanup_ok = false;
        }
        outcome.observation_complete =
            peer.complete && peer.failure.is_none() && !peer.transport.pending();
        if !outcome.observation_complete {
            if reason.is_none() {
                reason = Some("observer_gap");
            }
            outcome.native_error = peer
                .failure
                .as_ref()
                .and_then(|e| e.errno)
                .or(outcome.native_error);
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
    } else if outcome.signal.is_some() {
        "signal_exit"
    } else if outcome.code != Some(0) {
        "nonzero_exit"
    } else {
        "success"
    };
    if let Some(journal) = journal {
        if outcome.cleanup == "passed" && outcome.observation_complete {
            if let Err(e) = journal.publish("clean") {
                outcome.classification = "journal_failed";
                outcome.native_error = e.errno;
            }
        }
    }
    outcome
}

fn supervise(
    child: Child,
    cfg: &Config,
    native: bool,
    setup_pipe: impl FnMut(i32) -> bool,
    observer: Option<&mut Session>,
    journal: Option<&Context>,
) -> Outcome {
    supervise_with_signal(
        child,
        cfg,
        native,
        setup_pipe,
        observer,
        journal,
        |pid, signal| unsafe { libc::kill(pid, signal) },
    )
}
pub fn run(mut command: Command, cfg: &Config, peer: &mut Session, journal: &Context) -> Outcome {
    let native = native_host();
    if !native {
        return Outcome::new("host_not_native", false);
    }
    if cancelled() {
        return Outcome::new("cancelled", native);
    }
    if let Err(e) = journal.publish("running") {
        let mut out = Outcome::new("journal_failed", native);
        out.native_error = e.errno;
        return out;
    }
    if let Err(e) = peer.ready(cancelled, Duration::from_millis(cfg.timeout)) {
        let mut out = Outcome::new(
            if e.code == "cancelled" {
                "cancelled"
            } else {
                "observer_not_ready"
            },
            native,
        );
        out.native_error = e.errno;
        return out;
    }
    if cancelled() {
        return Outcome::new("cancelled", native);
    }
    command
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
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
    match command.spawn() {
        Ok(child) => supervise(child, cfg, native, nonblocking, Some(peer), Some(journal)),
        Err(e) => {
            let mut out = Outcome::new("spawn_failed", native);
            out.native_error = e.raw_os_error();
            out
        }
    }
}
#[cfg(test)]
#[path = "supervisor_tests.rs"]
mod supervisor_tests;
