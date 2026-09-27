#include "baseline.h"

#include <signal.h>

static bool values_match(pear_probe_id probe, const pear_baseline_packet *packet)
{
    const int64_t memory[] = {-1, 42, 0, 0, 84, 0};
    const int64_t protection[] = {-1, 42, 0};
    const int64_t low[] = {0x20000000, 42, 0};
    const int64_t jit[] = {-1, 8, 0, 8, 42, 0};
    const int64_t *expected = probe == PEAR_PROBE_MEMORY ? memory :
                              probe == PEAR_PROBE_PROTECTION ? protection :
                              probe == PEAR_PROBE_LOW_ADDRESS ? low : jit;
    unsigned count = (probe == PEAR_PROBE_PROTECTION ||
                      probe == PEAR_PROBE_LOW_ADDRESS) ? 3 : PEAR_BASELINE_STEPS;
    for (unsigned i = 0; i < count; ++i) {
        if (packet->steps[i].status != PEAR_STEP_PASSED) continue;
        if (expected[i] == -1) {
            if (packet->steps[i].value <= 0) return false;
        } else if (packet->steps[i].value != expected[i]) return false;
    }
    return true;
}

pear_baseline_outcome pear_assess_baseline(pear_probe_id probe,
                                          const pear_child_result *result)
{
    if (result == NULL || probe < PEAR_PROBE_MEMORY || probe > PEAR_PROBE_JIT ||
        !result->packet_valid || !result->child_reaped ||
        result->packet.probe != (uint32_t)probe || !values_match(probe, &result->packet))
        return PEAR_BASELINE_FAILED;
    const pear_baseline_packet *packet = &result->packet;
    if (probe == PEAR_PROBE_PROTECTION && packet->phase == PEAR_PACKET_ARMED) {
        if (result->outcome != PEAR_RUN_SIGNALED ||
            (result->term_signal != SIGBUS && result->term_signal != SIGSEGV))
            return PEAR_BASELINE_FAILED;
        for (unsigned i = 0; i < 3; ++i)
            if (packet->steps[i].status != PEAR_STEP_PASSED) return PEAR_BASELINE_FAILED;
        return PEAR_BASELINE_PASSED;
    }
    if (result->outcome != PEAR_RUN_EXITED || result->exit_code != 0 ||
        packet->phase != PEAR_PACKET_COMPLETE) return PEAR_BASELINE_FAILED;
    bool unavailable = false, incomplete = false;
    unsigned count = probe == PEAR_PROBE_LOW_ADDRESS ? 3 : PEAR_BASELINE_STEPS;
    for (unsigned i = 0; i < count; ++i) {
        if (packet->steps[i].status == PEAR_STEP_FAILED) return PEAR_BASELINE_FAILED;
        if (packet->steps[i].status == PEAR_STEP_UNAVAILABLE) unavailable = true;
        if (packet->steps[i].status == PEAR_STEP_NOT_RUN) incomplete = true;
    }
    if (unavailable) return PEAR_BASELINE_UNAVAILABLE;
    /* A protection trial completes positively only by the expected fault. */
    if (incomplete || probe == PEAR_PROBE_PROTECTION) return PEAR_BASELINE_FAILED;
    return PEAR_BASELINE_PASSED;
}
