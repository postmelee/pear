#include "baseline.h"

#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdlib.h>
#include <string.h>
#include <sys/resource.h>
#include <unistd.h>

static void passed(pear_baseline_packet *packet, size_t index, int64_t value)
{
    packet->steps[index].status = PEAR_STEP_PASSED;
    packet->steps[index].value = value;
}

int main(int argc, char **argv)
{
    if (argc != 4)
        return 64;
    char *end;
    long identifier = strtol(argv[1], &end, 10);
    if (*end != '\0' || identifier < PEAR_PROBE_GEOMETRY ||
        identifier > PEAR_PROBE_RECOMMIT_FAULT)
        return 65;
    const struct rlimit no_core = {0, 0};
    if (setrlimit(RLIMIT_CORE, &no_core) != 0)
        return 66;
    int marker = open(argv[3], O_WRONLY | O_CREAT | O_EXCL, 0600);
    if (marker < 0)
        return 67;
    if (write(marker, "started\n", 8) != 8 || close(marker) != 0)
        return 68;

    pear_baseline_packet packet = {0};
    packet.magic = PEAR_BASELINE_MAGIC;
    packet.version = PEAR_BASELINE_VERSION;
    packet.probe = (uint32_t)identifier;
    packet.phase = PEAR_PACKET_COMPLETE;
    bool fault = identifier == PEAR_PROBE_SUBPAGE_FAULT ||
                 identifier == PEAR_PROBE_RECOMMIT_FAULT;
    if (identifier == PEAR_PROBE_GEOMETRY) {
        int64_t page_size = strcmp(argv[2], "geometry4k") == 0 ? 4096 : 16384;
        passed(&packet, 0, page_size);
        passed(&packet, 1, page_size);
        passed(&packet, 2, 16384);
    } else {
        const int64_t values[PEAR_BASELINE_STEPS] = {
            12288, 7, 0, identifier == PEAR_PROBE_SUBPAGE ? 84 : 3,
            identifier == PEAR_PROBE_SUBPAGE ? 3 : 42, 0
        };
        for (size_t i = 0; i < (fault ? 3 : PEAR_BASELINE_STEPS); ++i)
            passed(&packet, i, values[i]);
        if (fault)
            packet.phase = PEAR_PACKET_ARMED;
    }
    if (strcmp(argv[2], "early-unavailable") == 0) {
        memset(packet.steps, 0, sizeof(packet.steps));
        packet.phase = PEAR_PACKET_COMPLETE;
        packet.steps[0].status = PEAR_STEP_UNAVAILABLE;
        packet.steps[0].error_domain = PEAR_DOMAIN_ERRNO;
        packet.steps[0].error_code = EPERM;
    } else if (strcmp(argv[2], "early-failure-cleanup") == 0) {
        memset(packet.steps, 0, sizeof(packet.steps));
        packet.phase = PEAR_PACKET_COMPLETE;
        passed(&packet, 0, 12288);
        packet.steps[1].status = PEAR_STEP_FAILED;
        packet.steps[1].error_domain = PEAR_DOMAIN_ERRNO;
        packet.steps[1].error_code = EIO;
        passed(&packet, 5, 0);
    } else if (strcmp(argv[2], "geometry-extra") == 0)
        passed(&packet, 3, 0);
    else if (strcmp(argv[2], "missing-prerequisite") == 0)
        memset(&packet.steps[1], 0, sizeof(packet.steps[1]));
    else if (strcmp(argv[2], "armed-incomplete") == 0)
        memset(&packet.steps[2], 0, sizeof(packet.steps[2]));
    else if (strcmp(argv[2], "armed-extra") == 0)
        passed(&packet, 3, 0);
    else if (strcmp(argv[2], "unexpected-armed") == 0)
        packet.phase = PEAR_PACKET_ARMED;
    else if (strcmp(argv[2], "wrong-identity") == 0)
        packet.probe = PEAR_PROBE_MEMORY;

    const unsigned char *bytes = (const unsigned char *)&packet;
    size_t offset = 0;
    while (offset < sizeof(packet)) {
        ssize_t count = write(STDOUT_FILENO, bytes + offset, sizeof(packet) - offset);
        if (count < 0 && errno == EINTR)
            continue;
        if (count <= 0)
            return 69;
        offset += (size_t)count;
    }
    if (fault && packet.phase == PEAR_PACKET_ARMED &&
        strcmp(argv[2], "armed-exit") != 0) {
        int wanted = strcmp(argv[2], "wrong-signal") == 0 ? SIGTERM :
                     strcmp(argv[2], "sigsegv") == 0 ? SIGSEGV : SIGBUS;
        if (raise(wanted) != 0)
            return 70;
        return 71;
    }
    return 0;
}
