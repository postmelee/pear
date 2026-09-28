#include "baseline.h"
#include "thread_probe.h"

#include <errno.h>
#include <string.h>
#include <sys/resource.h>
#include <unistd.h>

int pear_thread_child_main(pear_probe_id probe)
{
    if (probe != PEAR_PROBE_THREAD_POLICY && probe != PEAR_PROBE_THREAD_LITMUS)
        return 2;
    const struct rlimit core_limit = {0, 0};
    if (setrlimit(RLIMIT_CORE, &core_limit) != 0) return 3;
    pear_baseline_packet packet;
    memset(&packet, 0, sizeof(packet));
    packet.magic = PEAR_BASELINE_MAGIC;
    packet.version = PEAR_BASELINE_VERSION;
    packet.probe = probe;
    packet.phase = PEAR_PACKET_COMPLETE;
    if (probe == PEAR_PROBE_THREAD_POLICY) pear_thread_probe(&packet);
    else pear_thread_litmus_probe(&packet);
    const unsigned char *cursor = (const unsigned char *)&packet;
    size_t remaining = sizeof(packet);
    while (remaining != 0) {
        ssize_t amount = write(STDOUT_FILENO, cursor, remaining);
        if (amount < 0 && errno == EINTR) continue;
        if (amount <= 0) return 3;
        cursor += (size_t)amount;
        remaining -= (size_t)amount;
    }
    return 0;
}
