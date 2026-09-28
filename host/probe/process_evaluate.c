#include "baseline.h"

#include <signal.h>

pear_baseline_outcome pear_assess_process(pear_probe_id probe,
                                         const pear_child_result *result,
                                         pear_spawn_mode mode)
{
    if (result == NULL || (mode != PEAR_SPAWN_DEFAULT && mode != PEAR_SPAWN_PAGES_4K) ||
        result->page_attribute_called != (mode == PEAR_SPAWN_PAGES_4K) ||
        result->page_attribute_error != 0)
        return PEAR_BASELINE_FAILED;
    if (probe >= PEAR_PROBE_MEMORY && probe <= PEAR_PROBE_JIT)
        return pear_assess_baseline(probe, result);
    if (probe < PEAR_PROBE_GEOMETRY || probe > PEAR_PROBE_RECOMMIT_FAULT ||
        !result->packet_valid || !result->child_reaped || result->error_code != 0 ||
        result->packet.probe != (uint32_t)probe)
        return PEAR_BASELINE_FAILED;
    if (probe >= PEAR_PROBE_SUBPAGE && mode != PEAR_SPAWN_PAGES_4K)
        return PEAR_BASELINE_FAILED;
    const pear_baseline_packet *packet = &result->packet;
    bool fault = probe == PEAR_PROBE_SUBPAGE_FAULT || probe == PEAR_PROBE_RECOMMIT_FAULT;
    if (fault && packet->phase == PEAR_PACKET_ARMED) {
        const int64_t expected[] = {12288, 7, 0};
        if (result->outcome != PEAR_RUN_SIGNALED ||
            (result->term_signal != SIGBUS && result->term_signal != SIGSEGV))
            return PEAR_BASELINE_FAILED;
        for (unsigned i = 0; i < 3; ++i)
            if (packet->steps[i].status != PEAR_STEP_PASSED ||
                packet->steps[i].value != expected[i]) return PEAR_BASELINE_FAILED;
        return PEAR_BASELINE_PASSED;
    }
    if (packet->phase != PEAR_PACKET_COMPLETE || result->outcome != PEAR_RUN_EXITED ||
        result->exit_code != 0) return PEAR_BASELINE_FAILED;
    unsigned count = probe == PEAR_PROBE_GEOMETRY ? 3 : PEAR_BASELINE_STEPS;
    bool unavailable = false, incomplete = false;
    for (unsigned i = 0; i < count; ++i) {
        if (packet->steps[i].status == PEAR_STEP_FAILED) return PEAR_BASELINE_FAILED;
        if (packet->steps[i].status == PEAR_STEP_UNAVAILABLE) unavailable = true;
        if (packet->steps[i].status == PEAR_STEP_NOT_RUN) incomplete = true;
    }
    if (unavailable) return PEAR_BASELINE_UNAVAILABLE;
    if (fault || incomplete) return PEAR_BASELINE_FAILED;
    if (probe == PEAR_PROBE_GEOMETRY) {
        int64_t expected = mode == PEAR_SPAWN_PAGES_4K ? 4096 : 16384;
        return packet->steps[0].value == expected && packet->steps[1].value == expected &&
               packet->steps[2].value > 0 ? PEAR_BASELINE_PASSED : PEAR_BASELINE_FAILED;
    }
    const int64_t subpage[] = {12288, 7, 0, 84, 3, 0};
    const int64_t recommit[] = {12288, 7, 0, 3, 42, 0};
    const int64_t *expected = probe == PEAR_PROBE_SUBPAGE ? subpage : recommit;
    for (unsigned i = 0; i < PEAR_BASELINE_STEPS; ++i)
        if (packet->steps[i].value != expected[i]) return PEAR_BASELINE_FAILED;
    return PEAR_BASELINE_PASSED;
}
