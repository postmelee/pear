#include "baseline.h"

#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

/* This symbol replaces kill only in the separately compiled test runner.
 * Production child_runner.c has no injection switches or fixture arguments.
 */
static int deny_kill;
int pear_fixture_kill(pid_t pid, int value) {
    if (deny_kill && value == SIGKILL) {
        errno = EPERM;
        return -1;
    }
    return kill(pid, value);
}

static const char *outcome_name(pear_run_outcome value) {
    switch (value) {
    case PEAR_RUN_EXITED: return "exited";
    case PEAR_RUN_SIGNALED: return "signaled";
    case PEAR_RUN_TIMED_OUT: return "timed_out";
    case PEAR_RUN_OUTPUT_LIMIT: return "output_limit";
    case PEAR_RUN_SPAWN_ERROR: return "spawn_error";
    case PEAR_RUN_IO_ERROR: return "io_error";
    case PEAR_RUN_INVALID_OUTPUT: return "invalid_output";
    }
    return "unknown";
}

static int count_descriptors(void) {
    DIR *directory = opendir("/dev/fd");
    if (directory == NULL) return -1;
    int count = 0;
    struct dirent *entry;
    errno = 0;
    while ((entry = readdir(directory)) != NULL) {
        if (entry->d_name[0] >= '0' && entry->d_name[0] <= '9') ++count;
    }
    int read_error = errno;
    if (closedir(directory) != 0 || read_error != 0) return -1;
    return count;
}

int main(int argc, char **argv) {
    if (argc < 4 || argc > 6) return 64;
    char *end = NULL;
    unsigned long timeout = strtoul(argv[3], &end, 10);
    if (*end != '\0' || timeout > 60000) return 64;
    unsigned repeats = argc == 6 ? (unsigned)strtoul(argv[5], &end, 10) : 1;
    if (repeats == 0 || repeats > 64 || (argc == 6 && *end != '\0')) return 64;
    char fd_argument[32];
    int inherited_fd = -1;
    if (strcmp(argv[2], "closed-stdin") == 0) close(STDIN_FILENO);
    if (strcmp(argv[2], "check-inherited") == 0) {
        inherited_fd = open("/dev/null", O_RDONLY);
        if (inherited_fd < 0) return 66;
        snprintf(fd_argument, sizeof(fd_argument), "%d", inherited_fd);
    }
    if (strcmp(argv[2], "parent-ignore-sigchld") == 0 ||
        strcmp(argv[2], "parent-nocldwait") == 0) {
        struct sigaction action = {0};
        action.sa_handler = strcmp(argv[2], "parent-ignore-sigchld") == 0 ?
            SIG_IGN : SIG_DFL;
        action.sa_flags = strcmp(argv[2], "parent-nocldwait") == 0 ? SA_NOCLDWAIT : 0;
        sigemptyset(&action.sa_mask);
        if (sigaction(SIGCHLD, &action, NULL) != 0) return 67;
    }
    char *child_argument = inherited_fd >= 0 ? fd_argument : argc >= 5 ? argv[4] : NULL;
    char *child_argv[] = {argv[1], argv[2], child_argument, NULL};
    pear_probe_id expected = strncmp(argv[2], "protection-", 11) == 0 ?
        PEAR_PROBE_PROTECTION : strncmp(argv[2], "jit-", 4) == 0 ?
        PEAR_PROBE_JIT : PEAR_PROBE_MEMORY;
    deny_kill = strcmp(argv[2], "denied-cleanup") == 0;
    int before = count_descriptors();
    unsigned not_reaped = 0;
    unsigned remaining_children = 0;
    int remaining_error = 0;
    int remaining_pid = 0;
    unsigned test_cleanup_reaped = 0;
    pear_child_result result = {0};
    int status = 0;
    for (unsigned index = 0; index < repeats; ++index) {
        if (pear_run_child(argv[1], child_argv, expected,
                           (unsigned)timeout, &result) != 0) return 65;
        if (!result.child_reaped && result.outcome != PEAR_RUN_SPAWN_ERROR)
            ++not_reaped;
        if (deny_kill && !result.child_reaped && argc >= 5) {
            /* Reap only the PID written by this test's child; this recovery is
             * deliberately outside the runner and never changes its result.
             */
            FILE *pid_file = fopen(argv[4], "r");
            long owned_pid = -1;
            if (pid_file == NULL) return 68;
            int scanned = fscanf(pid_file, "%ld", &owned_pid);
            fclose(pid_file);
            if (scanned != 1 || owned_pid <= 1) return 69;
            for (unsigned attempt = 0; attempt < 300; ++attempt) {
                pid_t reaped = waitpid((pid_t)owned_pid, &status, WNOHANG);
                if (reaped == (pid_t)owned_pid) {
                    ++test_cleanup_reaped;
                    break;
                }
                if (reaped < 0 && errno != EINTR) break;
                struct timespec delay = {0, 10000000};
                nanosleep(&delay, NULL);
            }
        }
        errno = 0;
        pid_t extra = waitpid(-1, &status, WNOHANG);
        /* Darwin can briefly retain a failed-spawn child during kernel-owned
         * exit1 cleanup, without returning its PID. Never reap an unknown live
         * child to hide a leak; allow only this bounded, zero-result transition
         * to ECHILD. A positive (reapable) PID remains a failure.
         */
        for (unsigned attempt = 0;
             result.outcome == PEAR_RUN_SPAWN_ERROR && extra == 0 && attempt < 50;
             ++attempt) {
            struct timespec delay = {0, 1000000};
            nanosleep(&delay, NULL);
            errno = 0;
            extra = waitpid(-1, &status, WNOHANG);
        }
        if (extra >= 0 || errno != ECHILD) {
            ++remaining_children;
            remaining_error = errno;
            remaining_pid = (int)extra;
        }
    }
    int after = count_descriptors();
    if (inherited_fd >= 0) close(inherited_fd);
    pear_baseline_outcome assessment = pear_assess_baseline(expected, &result);
    const char *assessment_name = assessment == PEAR_BASELINE_PASSED ? "passed" :
        assessment == PEAR_BASELINE_UNAVAILABLE ? "unavailable" : "failed";
    printf("{\"outcome\":\"%s\",\"exit_code\":%d,\"term_signal\":%d,"
           "\"error_code\":%d,\"elapsed_ms\":%llu,\"stdout_bytes\":%zu,"
           "\"stderr_bytes\":%zu,\"packet_valid\":%s,\"child_reaped\":%s,"
           "\"fd_before\":%d,\"fd_after\":%d,\"not_reaped\":%u,"
           "\"remaining_children\":%u,\"repeats\":%u,\"assessment\":\"%s\","
           "\"remaining_error\":%d,\"remaining_pid\":%d,\"test_cleanup_reaped\":%u}\n",
           outcome_name(result.outcome), result.exit_code, result.term_signal,
           result.error_code, (unsigned long long)result.elapsed_ms,
           result.stdout_bytes, result.stderr_bytes,
           result.packet_valid ? "true" : "false",
           result.child_reaped ? "true" : "false", before, after,
           not_reaped, remaining_children, repeats, assessment_name,
           remaining_error, remaining_pid, test_cleanup_reaped);
    return 0;
}
