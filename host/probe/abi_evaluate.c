#include "baseline.h"

pear_baseline_outcome pear_assess_abi(pear_probe_id probe,
                                     const pear_child_result *result,
                                     pear_spawn_mode mode)
{
    if (probe == PEAR_PROBE_GEOMETRY)
        return pear_assess_process(probe, result, mode);
    if (result == NULL || probe < PEAR_PROBE_X18_ROUNDTRIP ||
        probe > PEAR_PROBE_THREAD_LITMUS ||
        (mode != PEAR_SPAWN_DEFAULT && mode != PEAR_SPAWN_PAGES_4K) ||
        result->page_attribute_called != (mode == PEAR_SPAWN_PAGES_4K) ||
        result->page_attribute_error != 0 || !result->packet_valid ||
        !result->child_reaped || result->error_code != 0 ||
        result->packet.probe != (uint32_t)probe ||
        result->packet.phase != PEAR_PACKET_COMPLETE ||
        result->outcome != PEAR_RUN_EXITED || result->exit_code != 0 ||
        result->term_signal != 0)
        return PEAR_BASELINE_FAILED;
    bool unavailable = false, incomplete = false;
    for (unsigned i = 0; i < PEAR_BASELINE_STEPS; ++i) {
        const pear_baseline_step *step = &result->packet.steps[i];
        if (step->status == PEAR_STEP_FAILED) return PEAR_BASELINE_FAILED;
        if (step->status == PEAR_STEP_UNAVAILABLE) unavailable = true;
        else if (step->status != PEAR_STEP_PASSED) incomplete = true;
        else if (step->error_domain != PEAR_DOMAIN_NONE || step->error_code != 0)
            return PEAR_BASELINE_FAILED;
    }
    if (unavailable) return PEAR_BASELINE_UNAVAILABLE;
    if (incomplete) return PEAR_BASELINE_FAILED;
    const int64_t expected[][PEAR_BASELINE_STEPS] = {
        {0, 1, 0x11223344, 0x11223344, 0, 64},
        {0, 32, 32, 32, 16, 0},
        {2, 0, 1, 2, 1, 0},
        {1, 2, 2, 2, 2, 2},
        {2, 10000, 0, 10000, 0, 2}
    };
    for (unsigned i = 0; i < PEAR_BASELINE_STEPS; ++i) {
        int64_t value = result->packet.steps[i].value;
        if (probe == PEAR_PROBE_THREAD_LITMUS && i == 2) {
            if (value < 0 || value > 10000) return PEAR_BASELINE_FAILED;
        } else if (value != expected[probe - PEAR_PROBE_X18_ROUNDTRIP][i]) {
            return PEAR_BASELINE_FAILED;
        }
    }
    return PEAR_BASELINE_PASSED;
}
