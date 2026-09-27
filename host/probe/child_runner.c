#include "baseline.h"

#include <errno.h>
#include <fcntl.h>
#include <libproc.h>
#include <poll.h>
#include <signal.h>
#include <spawn.h>
#include <string.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

extern char **environ;

static int monotonic_ms(uint64_t *value)
{
    struct timespec now;
    if (clock_gettime(CLOCK_MONOTONIC, &now) != 0)
        return -1;
    *value = (uint64_t)now.tv_sec * UINT64_C(1000) +
             (uint64_t)now.tv_nsec / UINT64_C(1000000);
    return 0;
}

static void close_fd(int *fd)
{
    if (*fd >= 0) {
        /* Retrying close after EINTR can close a newly reused descriptor. */
        (void)close(*fd);
        *fd = -1;
    }
}

/* Keep all runner descriptors above stdio before constructing spawn actions. */
static int owned_fd(int fd)
{
    if (fd < 0)
        return -1;
    if (fd < 3) {
        int replacement = fcntl(fd, F_DUPFD_CLOEXEC, 3);
        int saved = errno;
        (void)close(fd);
        errno = saved;
        return replacement;
    }
    if (fcntl(fd, F_SETFD, FD_CLOEXEC) < 0) {
        int saved = errno;
        (void)close(fd);
        errno = saved;
        return -1;
    }
    return fd;
}

static int owned_pipe(int pair[2])
{
    int raw[2];
    if (pipe(raw) != 0)
        return -1;
    pair[0] = owned_fd(raw[0]);
    if (pair[0] < 0) {
        int saved = errno;
        (void)close(raw[1]);
        errno = saved;
        return -1;
    }
    pair[1] = owned_fd(raw[1]);
    if (pair[1] < 0) {
        int saved = errno;
        close_fd(&pair[0]);
        errno = saved;
        return -1;
    }
    int flags = fcntl(pair[0], F_GETFL);
    if (flags < 0 || fcntl(pair[0], F_SETFL, flags | O_NONBLOCK) < 0) {
        int saved = errno;
        close_fd(&pair[0]);
        close_fd(&pair[1]);
        errno = saved;
        return -1;
    }
    return 0;
}

static bool valid_packet(const pear_baseline_packet *packet,
                         pear_probe_id expected)
{
    if (packet->magic != PEAR_BASELINE_MAGIC ||
        packet->version != PEAR_BASELINE_VERSION ||
        packet->probe != (uint32_t)expected ||
        (packet->phase != PEAR_PACKET_COMPLETE &&
         packet->phase != PEAR_PACKET_ARMED))
        return false;
    for (size_t i = 0; i < PEAR_BASELINE_STEPS; ++i) {
        const pear_baseline_step *step = &packet->steps[i];
        if (step->status > PEAR_STEP_FAILED ||
            step->error_domain > PEAR_DOMAIN_INTERNAL)
            return false;
        if (step->status == PEAR_STEP_NOT_RUN) {
            if (step->error_domain != PEAR_DOMAIN_NONE ||
                step->error_code != 0 || step->value != 0)
                return false;
        } else if (step->status == PEAR_STEP_PASSED) {
            if (step->error_domain != PEAR_DOMAIN_NONE || step->error_code != 0)
                return false;
        } else if (step->error_domain == PEAR_DOMAIN_NONE ||
                   step->error_code == 0 ||
                   (step->error_domain == PEAR_DOMAIN_ERRNO &&
                    step->error_code < 0)) {
            return false;
        }
        if (expected == PEAR_PROBE_LOW_ADDRESS && i >= 3 &&
            step->status != PEAR_STEP_NOT_RUN)
            return false;
    }
    /* Cleanup may run after an intermediate failure, including an internal
     * allocation postcondition failure. Other operations require every earlier
     * operation to have passed; a missing step cannot be skipped silently.
     */
    size_t cleanup = expected == PEAR_PROBE_LOW_ADDRESS ? 2 : 5;
    bool prerequisites_passed = true;
    for (size_t i = 0; i < cleanup; ++i) {
        uint32_t status = packet->steps[i].status;
        if (!prerequisites_passed && status != PEAR_STEP_NOT_RUN)
            return false;
        if (status != PEAR_STEP_PASSED)
            prerequisites_passed = false;
    }
    if (packet->phase == PEAR_PACKET_ARMED) {
        if (expected != PEAR_PROBE_PROTECTION)
            return false;
        for (size_t i = 0; i < PEAR_BASELINE_STEPS; ++i) {
            uint32_t wanted = i < 3 ? PEAR_STEP_PASSED : PEAR_STEP_NOT_RUN;
            if (packet->steps[i].status != wanted)
                return false;
        }
    }
    return true;
}

/* Read once per poll iteration so a writer cannot postpone the deadline.
 * Counters saturate at limit + 1; the extra byte is an overflow sentinel.
 */
static int collect_output(int *fd, unsigned char *destination, size_t limit,
                          size_t *count)
{
    unsigned char scratch[PEAR_BASELINE_STDERR_LIMIT + 1];
    size_t available = limit - *count;
    ssize_t length = read(*fd, scratch, available + 1);
    if (length == 0) {
        close_fd(fd);
        return 0;
    }
    if (length < 0)
        return errno == EINTR || errno == EAGAIN || errno == EWOULDBLOCK ? 0 : -1;
    size_t received = (size_t)length;
    if (destination != NULL) {
        size_t retained = received > available ? available : received;
        memcpy(destination + *count, scratch, retained);
    }
    *count += received;
    return received > available ? 1 : 0;
}

/* XNU excludes zombies from group signalling and can return EPERM for a
 * group containing only our unreaped leader. Do not mistake that case for a
 * live-member permission failure, and do not suppress other EPERM results.
 */
static bool only_exited_leader_remains(pid_t child)
{
    siginfo_t state;
    memset(&state, 0, sizeof(state));
    if (waitid(P_PID, (id_t)child, &state, WEXITED | WNOHANG | WNOWAIT) != 0 ||
        state.si_pid != child)
        return false;
    pid_t members[64];
    memset(members, 0, sizeof(members));
    errno = 0;
    int bytes = proc_listpids(PROC_PGRP_ONLY, (uint32_t)child,
                             members, (int)sizeof(members));
    if (bytes < 0 || errno != 0 || bytes >= (int)sizeof(members) ||
        bytes % (int)sizeof(pid_t) != 0)
        return false;
    for (size_t i = 0; i < (size_t)bytes / sizeof(pid_t); ++i)
        if (members[i] != 0 && members[i] != child)
            return false;
    return true;
}

/* A refused SIGKILL must not turn timeout recovery into an unbounded wait.
 * Keep the leader unreaped throughout this bounded cleanup grace period.
 */
static int await_owned_exit(pid_t child)
{
    uint64_t started, now;
    if (monotonic_ms(&started) != 0)
        return -1;
    for (;;) {
        siginfo_t state;
        memset(&state, 0, sizeof(state));
        int code = waitid(P_PID, (id_t)child, &state, WEXITED | WNOHANG | WNOWAIT);
        if (code == 0 && state.si_pid == child)
            return 0;
        if (code != 0 && errno != EINTR)
            return -1;
        if (monotonic_ms(&now) != 0)
            return -1;
        if (now - started >= 1000) {
            errno = ETIMEDOUT;
            return -1;
        }
        uint64_t remaining = 1000 - (now - started);
        int delay = remaining > 10 ? 10 : (int)remaining;
        if (poll(NULL, 0, delay) < 0 && errno != EINTR)
            return -1;
    }
}

int pear_run_child(const char *path, char *const argv[], pear_probe_id expected,
                   unsigned timeout_ms, pear_child_result *result)
{
    if (result == NULL)
        return -1;
    memset(result, 0, sizeof(*result));
    result->outcome = PEAR_RUN_SPAWN_ERROR;
    result->exit_code = -1;
    if (path == NULL || path[0] == '\0' || argv == NULL || argv[0] == NULL ||
        expected < PEAR_PROBE_MEMORY || expected > PEAR_PROBE_JIT ||
        timeout_ms == 0 || timeout_ms > 60000) {
        result->error_code = EINVAL;
        return -1;
    }

    int output[2] = {-1, -1};
    int errors[2] = {-1, -1};
    int input = -1;
    pid_t child = -1;
    bool actions_ready = false, attributes_ready = false;
    bool ownership_lost = false;
    posix_spawn_file_actions_t actions;
    posix_spawnattr_t attributes;
    uint64_t started = 0, now = 0;
    int code;
    int group_error = 0;
    unsigned char packet_bytes[sizeof(pear_baseline_packet)] = {0};

    if (monotonic_ms(&started) != 0) {
        result->outcome = PEAR_RUN_IO_ERROR;
        result->error_code = errno;
        goto finish;
    }
    /* Auto-reaping would release the leader PID before group cleanup. */
    struct sigaction child_action;
    if (sigaction(SIGCHLD, NULL, &child_action) != 0) {
        result->error_code = errno;
        goto finish;
    }
    if (child_action.sa_handler == SIG_IGN ||
        (child_action.sa_flags & SA_NOCLDWAIT) != 0) {
        result->error_code = EINVAL;
        goto finish;
    }
    if (owned_pipe(output) != 0 || owned_pipe(errors) != 0 ||
        (input = owned_fd(open("/dev/null", O_RDONLY | O_CLOEXEC))) < 0) {
        result->error_code = errno;
        goto finish;
    }
    code = posix_spawn_file_actions_init(&actions);
    if (code != 0) {
        result->error_code = code;
        goto finish;
    }
    actions_ready = true;
    code = posix_spawnattr_init(&attributes);
    if (code != 0) {
        result->error_code = code;
        goto finish;
    }
    attributes_ready = true;

#define SPAWN_SETUP(call) do { \
    code = (call); \
    if (code != 0) { result->error_code = code; goto finish; } \
} while (0)
    SPAWN_SETUP(posix_spawn_file_actions_adddup2(&actions, input, STDIN_FILENO));
    SPAWN_SETUP(posix_spawn_file_actions_adddup2(&actions, output[1], STDOUT_FILENO));
    SPAWN_SETUP(posix_spawn_file_actions_adddup2(&actions, errors[1], STDERR_FILENO));
    int descriptors[] = {input, output[0], output[1], errors[0], errors[1]};
    for (size_t i = 0; i < sizeof(descriptors) / sizeof(descriptors[0]); ++i)
        SPAWN_SETUP(posix_spawn_file_actions_addclose(&actions, descriptors[i]));
    SPAWN_SETUP(posix_spawnattr_setpgroup(&attributes, 0));
    sigset_t empty_mask, default_signals;
    sigemptyset(&empty_mask);
    sigfillset(&default_signals);
    sigdelset(&default_signals, SIGKILL);
    sigdelset(&default_signals, SIGSTOP);
    SPAWN_SETUP(posix_spawnattr_setsigmask(&attributes, &empty_mask));
    SPAWN_SETUP(posix_spawnattr_setsigdefault(&attributes, &default_signals));
    SPAWN_SETUP(posix_spawnattr_setflags(&attributes, POSIX_SPAWN_SETPGROUP |
        POSIX_SPAWN_SETSIGMASK | POSIX_SPAWN_SETSIGDEF | POSIX_SPAWN_CLOEXEC_DEFAULT));
#undef SPAWN_SETUP
    code = posix_spawn(&child, path, &actions, &attributes, argv, environ);
    if (code != 0) {
        child = -1;
        result->error_code = code;
        goto finish;
    }
    close_fd(&input);
    close_fd(&output[1]);
    close_fd(&errors[1]);
    result->outcome = PEAR_RUN_EXITED;

    for (;;) {
        if (monotonic_ms(&now) != 0) {
            result->outcome = PEAR_RUN_IO_ERROR;
            result->error_code = errno;
            break;
        }
        if (now - started >= timeout_ms) {
            result->outcome = PEAR_RUN_TIMED_OUT;
            break;
        }
        siginfo_t state;
        memset(&state, 0, sizeof(state));
        if (waitid(P_PID, (id_t)child, &state, WEXITED | WNOHANG | WNOWAIT) != 0) {
            if (errno == EINTR)
                continue;
            result->outcome = PEAR_RUN_IO_ERROR;
            result->error_code = errno;
            ownership_lost = errno == ECHILD;
            break;
        }
        if (state.si_pid == child && output[0] < 0 && errors[0] < 0)
            break;
        uint64_t remaining = timeout_ms - (now - started);
        int wait_ms = remaining > 20 ? 20 : (int)remaining;
        struct pollfd pipes[2] = {
            {.fd = output[0], .events = POLLIN},
            {.fd = errors[0], .events = POLLIN}
        };
        int ready = poll(pipes, 2, wait_ms);
        if (ready < 0) {
            if (errno == EINTR)
                continue;
            result->outcome = PEAR_RUN_IO_ERROR;
            result->error_code = errno;
            break;
        }
        bool stop = false;
        for (size_t i = 0; i < 2; ++i) {
            if (pipes[i].revents == 0)
                continue;
            if ((pipes[i].revents & POLLNVAL) != 0) {
                result->outcome = PEAR_RUN_IO_ERROR;
                result->error_code = EBADF;
                stop = true;
                break;
            }
            int collected = i == 0 ?
                collect_output(&output[0], packet_bytes, sizeof(packet_bytes),
                               &result->stdout_bytes) :
                collect_output(&errors[0], NULL, PEAR_BASELINE_STDERR_LIMIT,
                               &result->stderr_bytes);
            if (collected != 0) {
                result->outcome = collected > 0 ? PEAR_RUN_OUTPUT_LIMIT : PEAR_RUN_IO_ERROR;
                if (collected < 0)
                    result->error_code = errno;
                stop = true;
                break;
            }
        }
        if (stop)
            break;
    }

finish:
    /* WNOWAIT retains the leader even when it exits before its descendants.
     * Its PID therefore cannot be reused between group kill and final reap.
     * The caller must not concurrently reap this function's direct child.
     */
    if (child > 0 && !ownership_lost) {
        if (kill(-child, SIGKILL) != 0 && errno != ESRCH)
            group_error = errno;
        /* Also cover the owned leader if it changed its own process group. */
        if (kill(child, SIGKILL) != 0 && errno != ESRCH) {
            result->outcome = PEAR_RUN_IO_ERROR;
            result->error_code = errno;
        }
    }
    close_fd(&input);
    close_fd(&output[0]);
    close_fd(&output[1]);
    close_fd(&errors[0]);
    close_fd(&errors[1]);
    if (actions_ready)
        (void)posix_spawn_file_actions_destroy(&actions);
    if (attributes_ready)
        (void)posix_spawnattr_destroy(&attributes);
    if (child > 0 && !ownership_lost) {
        bool exited = await_owned_exit(child) == 0;
        if (!exited) {
            result->outcome = PEAR_RUN_IO_ERROR;
            result->error_code = errno;
        }
        if (group_error != 0 &&
            !(group_error == EPERM && exited && only_exited_leader_remains(child))) {
            result->outcome = PEAR_RUN_IO_ERROR;
            result->error_code = group_error;
        }
        if (exited) {
            int status = 0;
            pid_t reaped = -1;
            for (unsigned attempt = 0; attempt < 8; ++attempt) {
                reaped = waitpid(child, &status, WNOHANG);
                if (reaped >= 0 || errno != EINTR)
                    break;
            }
            if (reaped == child) {
                result->child_reaped = true;
                if (WIFEXITED(status))
                    result->exit_code = WEXITSTATUS(status);
                else if (WIFSIGNALED(status))
                    result->term_signal = WTERMSIG(status);
                if (result->outcome == PEAR_RUN_EXITED && WIFSIGNALED(status))
                    result->outcome = PEAR_RUN_SIGNALED;
            } else {
                result->outcome = PEAR_RUN_IO_ERROR;
                result->error_code = reaped == 0 ? EAGAIN : errno;
            }
        }
    }
    if (result->stdout_bytes == sizeof(packet_bytes) && result->stderr_bytes == 0) {
        pear_baseline_packet packet;
        memcpy(&packet, packet_bytes, sizeof(packet));
        if (valid_packet(&packet, expected)) {
            result->packet = packet;
            result->packet_valid = true;
        }
    }
    if (result->outcome == PEAR_RUN_EXITED && result->exit_code == 0 &&
        !result->packet_valid)
        result->outcome = PEAR_RUN_INVALID_OUTPUT;
    if (started != 0 && monotonic_ms(&now) == 0)
        result->elapsed_ms = now - started;
    return 0;
}
