#include "thread_probe.h"

#include <stdatomic.h>
#include <stdio.h>
#include <string.h>

/* The production worker orchestration calls this local fake through its
 * test-only resolver. Payload stubs never access concurrently shared words.
 */
static const char *scenario;
static _Atomic unsigned initial_calls, enabled_calls, restored_calls;
static _Thread_local bool initialized, enabled;
static _Thread_local unsigned worker_number;

static kern_return_t fake_policy(uint32_t value)
{
    if (!initialized) {
        initialized = true;
        worker_number = atomic_fetch_add(&initial_calls, 1);
        if (value != 0)
            return KERN_INVALID_ARGUMENT;
        if (strcmp(scenario, "initial-failed") == 0 && worker_number == 1)
            return KERN_PROTECTION_FAILURE;
        return KERN_SUCCESS;
    }
    if (value == 1) {
        atomic_fetch_add(&enabled_calls, 1);
        if (strcmp(scenario, "enable-failed") == 0 && worker_number == 1)
            return KERN_PROTECTION_FAILURE;
        enabled = true;
        return KERN_SUCCESS;
    }
    atomic_fetch_add(&restored_calls, 1);
    enabled = false;
    if (strcmp(scenario, "restore-failed") == 0 && worker_number == 1)
        return KERN_PROTECTION_FAILURE;
    return KERN_SUCCESS;
}

pear_thread_policy_function pear_test_thread_policy_resolve(void)
{
    return strcmp(scenario, "missing") == 0 ? NULL : fake_policy;
}

void pear_litmus_reset(uint32_t *data, uint32_t *flag)
{
    (void)data;
    (void)flag;
}

void pear_litmus_write(uint32_t *data, uint32_t *flag)
{
    (void)data;
    (void)flag;
}

uint64_t pear_litmus_read(const uint32_t *data, const uint32_t *flag)
{
    (void)data;
    (void)flag;
    if (strcmp(scenario, "forbidden") == 0 ||
        (strcmp(scenario, "baseline-only-forbidden") == 0 && !enabled))
        return 1;
    if (strcmp(scenario, "invalid-payload") == 0)
        return 2;
    return (UINT64_C(1) << 32) | 1;
}

int main(int argc, char **argv)
{
    if (argc != 3 || (strcmp(argv[1], "policy") != 0 && strcmp(argv[1], "litmus") != 0))
        return 64;
    scenario = argv[2];
    pear_baseline_packet packet = {0};
    packet.magic = PEAR_BASELINE_MAGIC;
    packet.version = PEAR_BASELINE_VERSION;
    packet.probe = strcmp(argv[1], "policy") == 0 ?
                   PEAR_PROBE_THREAD_POLICY : PEAR_PROBE_THREAD_LITMUS;
    packet.phase = PEAR_PACKET_COMPLETE;
    if (packet.probe == PEAR_PROBE_THREAD_POLICY)
        pear_thread_probe(&packet);
    else
        pear_thread_litmus_probe(&packet);
    printf("{\"initial_calls\":%u,\"enabled_calls\":%u,\"restored_calls\":%u,\"steps\":[",
           atomic_load(&initial_calls), atomic_load(&enabled_calls), atomic_load(&restored_calls));
    for (size_t i = 0; i < PEAR_BASELINE_STEPS; ++i) {
        const pear_baseline_step *step = &packet.steps[i];
        printf("%s{\"status\":%u,\"domain\":%u,\"code\":%lld,\"value\":%lld}",
               i == 0 ? "" : ",", step->status, step->error_domain,
               (long long)step->error_code, (long long)step->value);
    }
    puts("]}");
    return 0;
}
