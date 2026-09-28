import Foundation
import Darwin

@_silgen_name("pear_process_identity")
func processIdentity(_ pid: Int32, _ seconds: UnsafeMutablePointer<UInt64>, _ micros: UnsafeMutablePointer<UInt64>) -> Int32

@_silgen_name("proc_listpids")
private func listProcessIDs(_ type: UInt32, _ info: UInt32, _ buffer: UnsafeMutableRawPointer?, _ bytes: Int32) -> Int32

// Darwin can return EPERM for killpg when only the unreaped zombie leader
// remains. Never waive a real permission failure: inspect a bounded, complete
// group list while WNOWAIT still reserves this exact leader identity.
func onlyOwnedTerminalLeader(_ pid: pid_t) -> Bool {
    var info = siginfo_t()
    guard waitid(P_PID, id_t(pid), &info, WEXITED | WNOHANG | WNOWAIT) == 0,
          info.si_pid == pid else { return false }
    var members = [Int32](repeating: 0, count: 256)
    let capacity = members.count * MemoryLayout<Int32>.size
    errno = 0
    let count = members.withUnsafeMutableBytes { listProcessIDs(2, UInt32(pid), $0.baseAddress, Int32(capacity)) }
    guard count >= 0, count < capacity, count % 4 == 0, errno == 0 else { return false }
    return members.prefix(Int(count) / 4).allSatisfy { $0 == 0 || $0 == pid }
}

struct Result: Codable {
    let experiment_version = 1
    let candidate = "swift"
    let fixture_only = true
    let runtime_eligible = false
    var host_architecture = "arm64"
    var translated = false
    var classification = "invalid_contract"
    var spawned = false
    var reaped = false
    var cleanup = "not_started"
    var exit_code: Int? = nil
    var signal: Int? = nil
    var stdout_bytes = 0
    var stderr_bytes = 0
    enum CodingKeys: String, CodingKey {
        case experiment_version, candidate, fixture_only, runtime_eligible, host_architecture,
             translated, classification, spawned, reaped, cleanup, exit_code, signal, stdout_bytes, stderr_bytes
    }
    func encode(to encoder: Encoder) throws {
        var c = encoder.container(keyedBy: CodingKeys.self)
        try c.encode(experiment_version, forKey: .experiment_version); try c.encode(candidate, forKey: .candidate)
        try c.encode(fixture_only, forKey: .fixture_only); try c.encode(runtime_eligible, forKey: .runtime_eligible)
        try c.encode(host_architecture, forKey: .host_architecture); try c.encode(translated, forKey: .translated)
        try c.encode(classification, forKey: .classification); try c.encode(spawned, forKey: .spawned)
        try c.encode(reaped, forKey: .reaped); try c.encode(cleanup, forKey: .cleanup)
        try c.encode(exit_code, forKey: .exit_code); try c.encode(signal, forKey: .signal)
        try c.encode(stdout_bytes, forKey: .stdout_bytes); try c.encode(stderr_bytes, forKey: .stderr_bytes)
    }
}

func monotonic() -> UInt64 { clock_gettime_nsec_np(CLOCK_MONOTONIC_RAW) }
func nativeHost() -> (Bool, Bool) {
    #if arch(arm64)
    var translated: Int32 = 0
    var size = MemoryLayout<Int32>.size
    let rc = sysctlbyname("sysctl.proc_translated", &translated, &size, nil, 0)
    if rc != 0 && errno != ENOENT { return (false, false) }
    return (translated == 0, translated != 0)
    #else
    return (false, false)
    #endif
}
func filePath(_ fd: Int32) throws -> String {
    var bytes = [CChar](repeating: 0, count: Int(PATH_MAX))
    guard fcntl(fd, F_GETPATH, &bytes) == 0 else { throw Failure.invalid }
    return String(decoding: bytes.prefix { $0 != 0 }.map { UInt8(bitPattern: $0) }, as: UTF8.self)
}
func checkStateDirectories(_ files: BundleFiles) throws {
    let state = openat(files.root, "state", O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC)
    guard state >= 0 else { throw Failure.invalid }
    defer { close(state) }
    for child in ["runtime", "prefix", "saves", "cache", "logs"] {
        let fd = openat(state, child, O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC)
        guard fd >= 0 else { throw Failure.invalid }
        close(fd)
    }
}
func supervise(_ input: LaunchInput, timeoutMS: Int, outputLimit: Int, gap: Bool) -> Result {
    var result = Result()
    var outPipe: [Int32] = [-1, -1], errPipe: [Int32] = [-1, -1]
    guard pipe(&outPipe) == 0 else { result.classification = "spawn_failed"; return result }
    guard pipe(&errPipe) == 0 else {
        close(outPipe[0]); close(outPipe[1]); result.classification = "spawn_failed"; return result
    }
    defer {
        for fd in outPipe + errPipe where fd >= 0 { close(fd) }
    }
    for fd in outPipe + errPipe { guard fcntl(fd, F_SETFD, FD_CLOEXEC) == 0 else { result.classification = "spawn_failed"; return result } }
    for fd in [outPipe[0], errPipe[0]] { guard fcntl(fd, F_SETFL, O_NONBLOCK) == 0 else { result.classification = "spawn_failed"; return result } }
    var actions: posix_spawn_file_actions_t? = nil
    var attributes: posix_spawnattr_t? = nil
    guard posix_spawn_file_actions_init(&actions) == 0 else { result.classification = "spawn_failed"; return result }
    defer { posix_spawn_file_actions_destroy(&actions) }
    guard posix_spawnattr_init(&attributes) == 0 else { result.classification = "spawn_failed"; return result }
    defer { posix_spawnattr_destroy(&attributes) }
    var mask = sigset_t()
    var defaults = sigset_t()
    sigemptyset(&mask); sigemptyset(&defaults)
    for signal in [SIGTERM, SIGPIPE, SIGINT, SIGCHLD] { sigaddset(&defaults, signal) }
    let setup = [
        posix_spawn_file_actions_addopen(&actions, STDIN_FILENO, "/dev/null", O_RDONLY, 0),
        posix_spawn_file_actions_adddup2(&actions, outPipe[1], STDOUT_FILENO),
        posix_spawn_file_actions_adddup2(&actions, errPipe[1], STDERR_FILENO),
        posix_spawn_file_actions_addfchdir(&actions, input.files.root),
        posix_spawnattr_setflags(&attributes, Int16(POSIX_SPAWN_SETPGROUP | POSIX_SPAWN_CLOEXEC_DEFAULT | POSIX_SPAWN_SETSIGMASK | POSIX_SPAWN_SETSIGDEF)),
        posix_spawnattr_setpgroup(&attributes, 0),
        posix_spawnattr_setsigmask(&attributes, &mask),
        posix_spawnattr_setsigdefault(&attributes, &defaults)
    ]
    guard setup.allSatisfy({ $0 == 0 }) else { result.classification = "spawn_failed"; return result }
    let path: String
    do {
        try checkStateDirectories(input.files)
        // macOS posix_spawn consumes a pathname. Reopen through held nofollow
        // directory descriptors and compare bytes/inode immediately before use.
        // This narrows, but cannot eliminate, a concurrent pathname replacement.
        let current = try input.files.read(input.executablePath, max: 16 * 1024 * 1024)
        try require(sameFile(current.info, input.executable.info) && sha256(current.data) == sha256(input.executable.data))
        path = try filePath(current.fd)
        var atPath = stat()
        try require(lstat(path, &atPath) == 0 && sameFile(atPath, current.info) && (atPath.st_mode & S_IFMT) == S_IFREG)
    } catch { result.classification = "invalid_contract"; return result }
    let argv = ([path] + input.arguments).map { strdup($0) } + [nil]
    let envp = input.environment.map { strdup($0) } + [nil]
    defer { for pointer in argv + envp { if let pointer { free(pointer) } } }
    guard argv.dropLast().allSatisfy({ $0 != nil }), envp.dropLast().allSatisfy({ $0 != nil }) else { result.classification = "spawn_failed"; return result }
    var pid: pid_t = 0
    let rc = argv.withUnsafeBufferPointer { a in envp.withUnsafeBufferPointer { e in
        posix_spawn(&pid, path, &actions, &attributes, a.baseAddress!, e.baseAddress!)
    } }
    guard rc == 0 else { result.classification = "spawn_failed"; return result }
    result.spawned = true
    close(outPipe[1]); outPipe[1] = -1
    close(errPipe[1]); errPipe[1] = -1
    var seconds: UInt64 = 0, micros: UInt64 = 0
    let identityOK = processIdentity(pid, &seconds, &micros) == 0
    let started = monotonic()
    let runDeadline = started + UInt64(timeoutMS) * 1_000_000
    var cleanupDeadline: UInt64? = nil
    var groupTerminated = false
    var terminal = false
    var peekFailed = false
    var stdout = Data()
    var openStreams = [true, true]
    var reason: String? = nil
    var identityChecked = false
    var finalInfo = siginfo_t()
    while true {
        for stream in 0..<2 where openStreams[stream] {
            let fd = stream == 0 ? outPipe[0] : errPipe[0]
            // Bound work per iteration so an output flood cannot starve timers.
            for _ in 0..<16 {
                var buffer = [UInt8](repeating: 0, count: 4096)
                let count = read(fd, &buffer, buffer.count)
                if count > 0 {
                    if stream == 0 {
                        result.stdout_bytes += count
                        if stdout.count < outputLimit { stdout.append(contentsOf: buffer.prefix(min(count, outputLimit - stdout.count))) }
                    } else { result.stderr_bytes += count }
                    if (result.stdout_bytes > outputLimit || result.stderr_bytes > outputLimit) && reason == nil { reason = "output_limit" }
                } else if count == 0 { openStreams[stream] = false; break }
                else if errno == EINTR { continue }
                else if errno == EAGAIN || errno == EWOULDBLOCK { break }
                else { reason = "internal_error"; openStreams[stream] = false; break }
            }
        }
        if !terminal {
            var info = siginfo_t()
            let waitRC = waitid(P_PID, id_t(pid), &info, WEXITED | WNOHANG | WNOWAIT)
            if waitRC == 0 && info.si_pid == pid { terminal = true; finalInfo = info }
            else if waitRC != 0 && errno != EINTR { peekFailed = true; break }
        }
        if !identityChecked {
            if (!identityOK && !terminal) || (getpgid(pid) != pid && !terminal) { reason = "internal_error" }
            identityChecked = true
        }
        let now = monotonic()
        let pipesClosed = openStreams.allSatisfy { !$0 }
        if reason == nil && now >= runDeadline && (!terminal || !pipesClosed) { reason = "timeout" }
        if !groupTerminated && ((terminal && pipesClosed) || reason != nil) {
            // The unreaped direct child reserves its PID/group identifier.
            // Group termination always occurs before waitpid reaps that child.
            let killRC = kill(-pid, SIGKILL)
            let killError = errno
            if killRC != 0 && killError != ESRCH && !(killError == EPERM && terminal && onlyOwnedTerminalLeader(pid)) {
                reason = "cleanup_failed"
            }
            groupTerminated = true
            cleanupDeadline = now + 2_000_000_000
        }
        if terminal && openStreams.allSatisfy({ !$0 }) { break }
        if let deadline = cleanupDeadline, now >= deadline { reason = "cleanup_failed"; break }
        var pollers = [pollfd(fd: openStreams[0] ? outPipe[0] : -1, events: Int16(POLLIN | POLLHUP), revents: 0), pollfd(fd: openStreams[1] ? errPipe[0] : -1, events: Int16(POLLIN | POLLHUP), revents: 0)]
        _ = poll(&pollers, nfds_t(pollers.count), 5)
    }
    if terminal && !peekFailed {
        var status: Int32 = 0
        var reaped: pid_t = -1
        repeat { reaped = waitpid(pid, &status, WNOHANG) } while reaped < 0 && errno == EINTR
        result.reaped = reaped == pid
        if finalInfo.si_code == CLD_EXITED { result.exit_code = Int(finalInfo.si_status) }
        else { result.signal = Int(finalInfo.si_status) }
    }
    result.cleanup = result.reaped && groupTerminated && !peekFailed && reason != "cleanup_failed" && openStreams.allSatisfy({ !$0 }) ? "passed" : "failed"
    if result.cleanup != "passed" { result.classification = "cleanup_failed" }
    else if let reason { result.classification = reason }
    else if gap { result.classification = "observer_gap" }
    else if result.signal != nil { result.classification = "signal_exit" }
    else if result.exit_code != 0 { result.classification = "nonzero_exit" }
    else {
        do {
            var parser = try StrictJSON(stdout)
            let response = try object(parser.parse(), "fixture ok")
            try require(response["fixture"] == .integer(1) && response["ok"] == .bool(true))
            result.classification = "success"
        } catch { result.classification = "child_output_invalid" }
    }
    return result
}
