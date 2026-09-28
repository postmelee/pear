/* Owned native fixture, never a game or a process supervisor. */
#include "native_bridge.h"
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/sysctl.h>
#include <time.h>
#include <unistd.h>

static int native_host(void) {
#if !defined(__aarch64__)
    return 0;
#else
    int translated = -1;
    size_t size = sizeof(translated);
    if (sysctlbyname("sysctl.proc_translated", &translated, &size, NULL, 0) == 0)
        return translated == 0;
    return errno == ENOENT;
#endif
}
static void delay_ms(unsigned ms) {
    struct timespec wait = {(time_t)(ms / 1000), (long)(ms % 1000) * 1000000};
    while (nanosleep(&wait, &wait) < 0 && errno == EINTR) {}
}
static int write_all(int fd, const char *data, size_t count) {
    while (count) {
        ssize_t n = write(fd, data, count);
        if (n < 0 && errno == EINTR) continue;
        if (n <= 0) return -1;
        data += n; count -= (size_t)n;
    }
    return 0;
}
static int trace_identity(const char *path) {
    uint64_t sec = 0, usec = 0;
    if (pear_process_identity(getpid(), &sec, &usec) != 0) return -1;
    int fd = open(path, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC, 0600);
    if (fd < 0) return -1;
    char data[256];
    int n = snprintf(data, sizeof(data),
        "{\"pid\":%d,\"pgid\":%d,\"started_sec\":%llu,\"started_usec\":%llu,\"native\":true}\n",
        getpid(), getpgrp(), (unsigned long long)sec, (unsigned long long)usec);
    int status = n > 0 && (size_t)n < sizeof(data) ? write_all(fd, data, (size_t)n) : -1;
    close(fd);
    return status;
}
static int success(void) {
    static const char out[] = "{\"fixture\":1,\"ok\":true}\n";
    return write_all(STDOUT_FILENO, out, sizeof(out) - 1) ? 65 : 0;
}
int main(int argc, char **argv) {
    if (!native_host()) return 66;
    if (argc == 5 && strcmp(argv[1], "--probe-identity") == 0) {
        char *end = NULL;
        long raw_pid = strtol(argv[2], &end, 10);
        if (!end || *end || raw_pid <= 0 || raw_pid > INT32_MAX) return 2;
        unsigned long long sec = strtoull(argv[3], &end, 10);
        if (!end || *end) return 2;
        unsigned long long usec = strtoull(argv[4], &end, 10);
        if (!end || *end) return 2;
        uint64_t actual_sec = 0, actual_usec = 0;
        int error = pear_process_identity((int32_t)raw_pid, &actual_sec, &actual_usec);
        if (error == ESRCH) return 0;
        if (error) return 2;
        return actual_sec == sec && actual_usec == usec ? 1 : 0;
    }
    if (argc == 2 && strcmp(argv[1], "sentinel") == 0) { delay_ms(120000); return 0; }
    if (argc < 2 || trace_identity("state/prefix/child.json") != 0) return 64;
    const char *mode = argv[1];
    if (!strcmp(mode, "success")) return success();
    if (!strcmp(mode, "args")) {
        if (argc != 4 || strcmp(argv[2], "value with spaces") ||
            strcmp(argv[3], "Unicode-\xce\xbb-\xf0\x9f\x8d\x90")) return 42;
        return success();
    }
    if (!strcmp(mode, "environment")) {
        const char *allowed = getenv("PEAR_FIXTURE_VALUE");
        if (getenv("PEAR_SECRET_SENTINEL") || !allowed || strcmp(allowed, "allowed")) return 43;
        return success();
    }
    if (!strcmp(mode, "stdin")) { char c; return read(STDIN_FILENO, &c, 1) == 0 ? success() : 44; }
    if (!strcmp(mode, "nonzero")) return 7;
    if (!strcmp(mode, "signal")) { raise(SIGTERM); return 45; }
    if (!strcmp(mode, "delay")) { delay_ms(5000); return success(); }
    if (!strcmp(mode, "excess_stdout") || !strcmp(mode, "excess_stderr")) {
        char block[4096]; memset(block, 'x', sizeof(block));
        int fd = !strcmp(mode, "excess_stdout") ? STDOUT_FILENO : STDERR_FILENO;
        for (int i = 0; i < 64; ++i) if (write_all(fd, block, sizeof(block))) return 46;
        return success();
    }
    if (!strcmp(mode, "malformed")) { (void)write_all(STDOUT_FILENO, "not-json\n", 9); return 0; }
    if (!strcmp(mode, "secret")) {
        static const char marker[] = "PRIVATE_FIXTURE_MARKER_93c8\n";
        (void)write_all(STDERR_FILENO, marker, sizeof(marker) - 1);
        return success();
    }
    if (!strcmp(mode, "descendant_pipe")) {
        pid_t child = fork();
        if (child < 0) return 47;
        if (child == 0) {
            if (trace_identity("state/prefix/descendant.json")) _exit(48);
            delay_ms(10000); _exit(0);
        }
        /* Give the independent harness identity evidence before the leader exits. */
        for (int i = 0; i < 100 && access("state/prefix/descendant.json", F_OK); ++i) delay_ms(1);
        return success();
    }
    return 49;
}
