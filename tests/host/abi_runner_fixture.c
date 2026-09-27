#include "baseline.h"

#include <errno.h>
#include <signal.h>
#include <stdlib.h>
#include <string.h>
#include <sys/resource.h>
#include <unistd.h>

/* Synthetic packets exercise protocol handling, never x18 or thread policy. */
static const int64_t success_values[][PEAR_BASELINE_STEPS] = {
    {0, 1, 0x11223344, 0x11223344, 0, 64},
    {0, 32, 32, 32, 16, 0},
    {2, 0, 1, 2, 1, 0},
    {1, 2, 2, 2, 2, 2},
    {2, 10000, 0, 10000, 0, 2}
};

int main(int argc, char **argv)
{
    if (argc != 3)
        return 64;
    char *end;
    long identifier = strtol(argv[1], &end, 10);
    if (*end != '\0' || identifier < PEAR_PROBE_X18_ROUNDTRIP ||
        identifier > PEAR_PROBE_THREAD_LITMUS)
        return 65;
    const struct rlimit no_core = {0, 0};
    if (setrlimit(RLIMIT_CORE, &no_core) != 0)
        return 66;
    pear_baseline_packet packet = {0};
    packet.magic = PEAR_BASELINE_MAGIC;
    packet.version = PEAR_BASELINE_VERSION;
    packet.probe = (uint32_t)identifier;
    packet.phase = PEAR_PACKET_COMPLETE;
    for (size_t i = 0; i < PEAR_BASELINE_STEPS; ++i) {
        packet.steps[i].status = PEAR_STEP_PASSED;
        packet.steps[i].value = success_values[identifier - PEAR_PROBE_X18_ROUNDTRIP][i];
    }
    if (strcmp(argv[2], "armed") == 0) {
        packet.phase = PEAR_PACKET_ARMED;
        memset(&packet.steps[3], 0, 3 * sizeof(packet.steps[0]));
    } else if (strcmp(argv[2], "missing-prerequisite") == 0)
        memset(&packet.steps[2], 0, sizeof(packet.steps[2]));
    else if (strcmp(argv[2], "wrong-identity") == 0)
        packet.probe = PEAR_PROBE_MEMORY;
    else if (strcmp(argv[2], "failed-with-cleanup") == 0) {
        memset(&packet.steps[3], 0, 3 * sizeof(packet.steps[0]));
        packet.steps[3].status = PEAR_STEP_FAILED;
        packet.steps[3].error_domain = PEAR_DOMAIN_ERRNO;
        packet.steps[3].error_code = EPERM;
        packet.steps[5].status = PEAR_STEP_PASSED;
        packet.steps[5].value = 2;
    } else if (strcmp(argv[2], "unavailable") == 0) {
        memset(packet.steps, 0, sizeof(packet.steps));
        packet.steps[0].status = PEAR_STEP_UNAVAILABLE;
        packet.steps[0].error_domain = PEAR_DOMAIN_ERRNO;
        packet.steps[0].error_code = ENOSYS;
    } else if (strcmp(argv[2], "cleanup-failed") == 0) {
        packet.steps[5].status = PEAR_STEP_FAILED;
        packet.steps[5].error_domain = PEAR_DOMAIN_ERRNO;
        packet.steps[5].error_code = EIO;
    } else if (strcmp(argv[2], "baseline-reordered") == 0)
        packet.steps[2].value = 17;
    else if (strcmp(argv[2], "policy-partial") == 0)
        packet.steps[3].value = 1;
    else if (strcmp(argv[2], "enabled-reordered") == 0)
        packet.steps[4].value = 1;

    const unsigned char *bytes = (const unsigned char *)&packet;
    size_t offset = 0;
    while (offset < sizeof(packet)) {
        ssize_t count = write(STDOUT_FILENO, bytes + offset, sizeof(packet) - offset);
        if (count < 0 && errno == EINTR)
            continue;
        if (count <= 0)
            return 67;
        offset += (size_t)count;
    }
    if (strcmp(argv[2], "signal") == 0) {
        (void)raise(SIGTERM);
        return 68;
    }
    return strcmp(argv[2], "nonzero") == 0 ? 7 : 0;
}
