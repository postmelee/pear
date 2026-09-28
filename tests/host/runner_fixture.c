#include "baseline.h"

#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/resource.h>
#include <sys/types.h>
#include <time.h>
#include <unistd.h>

static void pause_for_test(void) {
    struct timespec delay = {10, 0};
    while (nanosleep(&delay, &delay) != 0 && errno == EINTR) {}
}

static void send_bytes(int fd, const void *bytes, size_t size) {
    const unsigned char *cursor = bytes;
    while (size != 0) {
        ssize_t count = write(fd, cursor, size);
        if (count > 0) {
            cursor += count;
            size -= (size_t)count;
        } else if (count < 0 && errno == EINTR) {
            continue;
        } else {
            _exit(90);
        }
    }
}

static void write_descendant_pid(const char *path, pid_t pid) {
    FILE *file = fopen(path, "w");
    if (file == NULL) _exit(91);
    if (fprintf(file, "%ld\n", (long)pid) < 0 || fclose(file) != 0) _exit(92);
}

int main(int argc, char **argv) {
    if (argc < 2) return 64;
    const char *mode = argv[1];
    const struct rlimit no_core = {0, 0};
    if (setrlimit(RLIMIT_CORE, &no_core) != 0) return 93;
    pear_baseline_packet packet = {
        .magic = PEAR_BASELINE_MAGIC,
        .version = PEAR_BASELINE_VERSION,
        .probe = PEAR_PROBE_MEMORY,
        .phase = PEAR_PACKET_COMPLETE,
    };
    for (size_t index = 0; index < PEAR_BASELINE_STEPS; ++index)
        packet.steps[index].status = PEAR_STEP_PASSED;
    packet.steps[0].value = 16384;
    packet.steps[1].value = 42;
    packet.steps[4].value = 84;
    if (strncmp(mode, "protection-", 11) == 0) {
        packet.probe = PEAR_PROBE_PROTECTION;
        packet.phase = PEAR_PACKET_ARMED;
        memset(&packet.steps[3], 0, 3 * sizeof(packet.steps[0]));
    } else if (strncmp(mode, "jit-", 4) == 0) {
        packet.probe = PEAR_PROBE_JIT;
        packet.steps[1].value = 8;
        packet.steps[3].value = 8;
        packet.steps[4].value = strcmp(mode, "jit-wrong-return") == 0 ? 43 : 42;
    }

    if (strcmp(mode, "closed-stdin") == 0) {
        char byte;
        if (read(STDIN_FILENO, &byte, 1) != 0) return 97;
    }
    if (strcmp(mode, "check-inherited") == 0) {
        if (argc != 3) return 64;
        int inherited_fd = atoi(argv[2]);
        errno = 0;
        if (inherited_fd < 3 || fcntl(inherited_fd, F_GETFD) != -1 || errno != EBADF)
            return 98;
    }
    if (strcmp(mode, "denied-cleanup") == 0) {
        if (argc != 3 || argv[2][0] == '\0') return 64;
        write_descendant_pid(argv[2], getpid());
        struct timespec delay = {2, 0};
        while (nanosleep(&delay, &delay) != 0 && errno == EINTR) {}
        return 0;
    }
    if (strcmp(mode, "missing") == 0) return 0;
    if (strcmp(mode, "signal") == 0 || strcmp(mode, "protection-before-armed") == 0) {
        signal(SIGTERM, SIG_DFL);
        raise(SIGTERM);
        return 94;
    }
    if (strcmp(mode, "timeout") == 0) {
        pause_for_test();
        return 95;
    }
    if (strcmp(mode, "partial-timeout") == 0) {
        send_bytes(STDOUT_FILENO, &packet, sizeof(packet) / 2);
        pause_for_test();
        return 95;
    }
    if (strcmp(mode, "grandchild") == 0 ||
        strcmp(mode, "leader-exit") == 0) {
        if (argc != 3) return 64;
        pid_t descendant = fork();
        if (descendant < 0) return 96;
        if (descendant == 0) {
            pause_for_test();
            _exit(0);
        }
        write_descendant_pid(argv[2], descendant);
        send_bytes(STDOUT_FILENO, &packet, sizeof(packet));
        if (strcmp(mode, "grandchild") == 0) pause_for_test();
        return 0;
    }
    if (strcmp(mode, "cleanup-failure") == 0) {
        packet.steps[5].status = PEAR_STEP_FAILED;
        packet.steps[5].error_domain = PEAR_DOMAIN_ERRNO;
        packet.steps[5].error_code = EINVAL;
    } else if (strcmp(mode, "jit-unavailable") == 0) {
        memset(packet.steps, 0, sizeof(packet.steps));
        packet.steps[0].status = PEAR_STEP_UNAVAILABLE;
        packet.steps[0].error_domain = PEAR_DOMAIN_ERRNO;
        packet.steps[0].error_code = EPERM;
    } else if (strcmp(mode, "protection-missing-prerequisite") == 0) {
        memset(&packet.steps[1], 0, sizeof(packet.steps[1]));
    } else if (strcmp(mode, "bad-magic") == 0) packet.magic ^= 1;
    else if (strcmp(mode, "bad-version") == 0) packet.version += 1;
    else if (strcmp(mode, "wrong-probe") == 0) packet.probe = PEAR_PROBE_JIT;
    else if (strcmp(mode, "bad-phase") == 0) packet.phase = 99;
    else if (strcmp(mode, "unexpected-armed") == 0) packet.phase = PEAR_PACKET_ARMED;
    else if (strcmp(mode, "bad-status") == 0) packet.steps[0].status = 99;
    else if (strcmp(mode, "bad-domain") == 0) packet.steps[0].error_domain = 99;
    else if (strcmp(mode, "pass-with-error") == 0) {
        packet.steps[0].error_domain = PEAR_DOMAIN_ERRNO;
        packet.steps[0].error_code = EACCES;
    } else if (strcmp(mode, "not-run-with-value") == 0) {
        packet.steps[0].status = PEAR_STEP_NOT_RUN;
        packet.steps[0].value = 1;
    } else if (strcmp(mode, "failure-without-error") == 0) {
        packet.steps[0].status = PEAR_STEP_FAILED;
    } else if (strcmp(mode, "negative-errno") == 0) {
        packet.steps[0].status = PEAR_STEP_UNAVAILABLE;
        packet.steps[0].error_domain = PEAR_DOMAIN_ERRNO;
        packet.steps[0].error_code = -EACCES;
    } else if (strcmp(mode, "after-unavailable") == 0) {
        packet.steps[0].status = PEAR_STEP_UNAVAILABLE;
        packet.steps[0].error_domain = PEAR_DOMAIN_ERRNO;
        packet.steps[0].error_code = ENOMEM;
        packet.steps[0].value = 0;
    } else if (strcmp(mode, "after-not-run") == 0) {
        packet.steps[1].status = PEAR_STEP_NOT_RUN;
        packet.steps[1].value = 0;
    }

    if (strcmp(mode, "stderr-first") == 0)
        send_bytes(STDERR_FILENO, "x", 1);
    size_t length = strcmp(mode, "truncated") == 0 ? sizeof(packet) - 1 : sizeof(packet);
    send_bytes(STDOUT_FILENO, &packet, length);
    if (strcmp(mode, "trailing") == 0)
        send_bytes(STDOUT_FILENO, "x", 1);
    if (strcmp(mode, "stdout-flood") == 0 ||
        strcmp(mode, "stderr-flood") == 0) {
        unsigned char bytes[4096];
        memset(bytes, 'x', sizeof(bytes));
        int fd = strcmp(mode, "stdout-flood") == 0 ? STDOUT_FILENO : STDERR_FILENO;
        for (;;) send_bytes(fd, bytes, sizeof(bytes));
    }
    if (strcmp(mode, "protection-wrong-signal") == 0) {
        signal(SIGTERM, SIG_DFL);
        raise(SIGTERM);
    }
    if (strcmp(mode, "nonzero") == 0) return 7;
    return 0;
}
