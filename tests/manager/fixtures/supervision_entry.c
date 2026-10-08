/* Self-owned Stage 3 fixture adapter; original #3 child is linked unchanged.
 * The native manager selects this entry from immutable media. Only this finite
 * test adapter consumes the manager-provided work FD; no game identity branch. */
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include "native_bridge.h"
extern int pear_state_fixture(int argc, char **argv);
extern int pear_original_main(int argc, char **argv);
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
int main(int argc, char **argv) {
    const char *raw = getenv("PEAR_FIXTURE_WORK_FD");
    if (raw) {
        char *end = NULL; long fd = strtol(raw, &end, 10);
        if (!end || *end || fd < 3 || fd > 1024 || fchdir((int)fd)) return 61;
        close((int)fd); unsetenv("PEAR_FIXTURE_WORK_FD");
    } else return 62;
    if (argc > 1 && !strcmp(argv[1], "state")) return pear_state_fixture(argc, argv);
    if (argc > 1 && (!strcmp(argv[1], "early_eof") || !strcmp(argv[1], "final_burst") || !strcmp(argv[1], "detached_helper"))) {
        char *mode = argv[1]; argv[1] = "trace_only";
        int traced = pear_original_main(argc, argv); argv[1] = mode;
        if (traced != 49) return 64;
    }
    if (argc > 1 && !strcmp(argv[1], "early_eof")) {
        close(STDOUT_FILENO); close(STDERR_FILENO); delay_ms(100); return 0;
    }
    if (argc > 1 && !strcmp(argv[1], "final_burst")) {
        char output[4096]; memset(output, 'z', sizeof(output));
        return write(STDOUT_FILENO, output, sizeof(output)) == sizeof(output) ? 0 : 63;
    }
    if (argc > 1 && !strcmp(argv[1], "detached_helper")) {
        pid_t child = fork();
        if (child < 0) return 67;
        if (child == 0) {
            if (setsid() < 0 || trace_identity("state/prefix/detached.json")) _exit(68);
            close(STDOUT_FILENO); close(STDERR_FILENO);
            delay_ms(1500); _exit(0);
        }
        for (int i = 0; i < 500 && access("state/prefix/detached.json", F_OK); ++i) delay_ms(1);
        return access("state/prefix/detached.json", F_OK) ? 69 : 0;
    }
    return pear_original_main(argc, argv);
}
