#include "baseline.h"

#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>

/* No production ABI thunk is linked into this packet/evaluator test binary. */
static const int64_t success_values[][PEAR_BASELINE_STEPS] = {
    {0, 1, 0x11223344, 0x11223344, 0, 64},
    {0, 32, 32, 32, 16, 0},
    {2, 0, 1, 2, 1, 0},
    {1, 2, 2, 2, 2, 2},
    {2, 10000, 0, 10000, 0, 2}
};

static const char *assessment_name(pear_baseline_outcome value)
{
    if (value == PEAR_BASELINE_PASSED)
        return "passed";
    if (value == PEAR_BASELINE_UNAVAILABLE)
        return "unavailable";
    return "failed";
}

static const char *outcome_name(pear_run_outcome value)
{
    switch (value) {
        case PEAR_RUN_EXITED: return "exited";
        case PEAR_RUN_SIGNALED: return "signaled";
        case PEAR_RUN_TIMED_OUT: return "timed_out";
        case PEAR_RUN_OUTPUT_LIMIT: return "output_limit";
        case PEAR_RUN_SPAWN_ERROR: return "spawn_error";
        case PEAR_RUN_IO_ERROR: return "io_error";
        case PEAR_RUN_INVALID_OUTPUT: return "invalid_output";
    }
    return "unknown";
}

static pear_child_result successful_result(pear_probe_id probe, pear_spawn_mode mode)
{
    pear_child_result result = {0};
    result.outcome = PEAR_RUN_EXITED;
    result.child_reaped = true;
    result.packet_valid = true;
    result.stdout_bytes = sizeof(result.packet);
    result.page_attribute_called = mode == PEAR_SPAWN_PAGES_4K;
    result.packet.magic = PEAR_BASELINE_MAGIC;
    result.packet.version = PEAR_BASELINE_VERSION;
    result.packet.probe = probe;
    result.packet.phase = PEAR_PACKET_COMPLETE;
    for (size_t i = 0; i < PEAR_BASELINE_STEPS; ++i) {
        result.packet.steps[i].status = PEAR_STEP_PASSED;
        result.packet.steps[i].value = success_values[probe - PEAR_PROBE_X18_ROUNDTRIP][i];
    }
    return result;
}

static void mutate(pear_child_result *result, const char *mutation)
{
    if (strcmp(mutation, "no-attribute") == 0)
        result->page_attribute_called = false;
    else if (strcmp(mutation, "unexpected-attribute") == 0)
        result->page_attribute_called = true;
    else if (strcmp(mutation, "attribute-error") == 0)
        result->page_attribute_error = EPERM;
    else if (strcmp(mutation, "not-reaped") == 0)
        result->child_reaped = false;
    else if (strcmp(mutation, "invalid-packet") == 0)
        result->packet_valid = false;
    else if (strcmp(mutation, "wrong-identity") == 0)
        result->packet.probe = PEAR_PROBE_MEMORY;
    else if (strcmp(mutation, "nonzero-exit") == 0)
        result->exit_code = 7;
    else if (strcmp(mutation, "timeout") == 0)
        result->outcome = PEAR_RUN_TIMED_OUT;
    else if (strcmp(mutation, "signal") == 0) {
        result->outcome = PEAR_RUN_SIGNALED;
        result->term_signal = SIGBUS;
        result->exit_code = -1;
    } else if (strcmp(mutation, "error-code") == 0)
        result->error_code = EIO;
    else if (strcmp(mutation, "armed") == 0)
        result->packet.phase = PEAR_PACKET_ARMED;
    else if (strcmp(mutation, "cleanup-failed") == 0) {
        result->packet.steps[5].status = PEAR_STEP_FAILED;
        result->packet.steps[5].error_domain = PEAR_DOMAIN_ERRNO;
        result->packet.steps[5].error_code = EIO;
    } else if (strcmp(mutation, "cleanup-not-run") == 0)
        memset(&result->packet.steps[5], 0, sizeof(result->packet.steps[5]));
    else if (strncmp(mutation, "value-", 6) == 0 && mutation[6] >= '0' &&
             mutation[6] <= '5' && mutation[7] == '\0')
        result->packet.steps[mutation[6] - '0'].value += 1;
    else if (strncmp(mutation, "missing-", 8) == 0 && mutation[8] >= '0' &&
             mutation[8] <= '5' && mutation[9] == '\0')
        memset(&result->packet.steps[mutation[8] - '0'], 0, sizeof(result->packet.steps[0]));
    else if (strcmp(mutation, "baseline-observed") == 0)
        result->packet.steps[2].value = 17;
    else if (strcmp(mutation, "baseline-all") == 0)
        result->packet.steps[2].value = 10000;
    else if (strcmp(mutation, "baseline-negative") == 0)
        result->packet.steps[2].value = -1;
    else if (strcmp(mutation, "baseline-overflow") == 0)
        result->packet.steps[2].value = 10001;
    else if (strcmp(mutation, "partial-workers") == 0)
        result->packet.steps[0].value = 1;
    else if (strcmp(mutation, "partial-enable") == 0)
        result->packet.steps[3].value = 1;
}

int main(int argc, char **argv)
{
    if (argc != 5)
        return 64;
    if (strcmp(argv[1], "assess") == 0) {
        pear_probe_id probe = (pear_probe_id)atoi(argv[2]);
        if (probe < PEAR_PROBE_X18_ROUNDTRIP || probe > PEAR_PROBE_THREAD_LITMUS)
            return 65;
        pear_spawn_mode mode = (pear_spawn_mode)atoi(argv[3]);
        pear_child_result result = successful_result(probe, mode);
        mutate(&result, argv[4]);
        printf("{\"assessment\":\"%s\"}\n", assessment_name(
            pear_assess_abi(probe, strcmp(argv[4], "null") == 0 ? NULL : &result, mode)));
        return 0;
    }
    if (strcmp(argv[1], "spawn") != 0)
        return 66;
    pear_probe_id probe = (pear_probe_id)atoi(argv[3]);
    char *child_argv[] = {argv[2], argv[3], argv[4], NULL};
    pear_child_result result;
    int returned = pear_run_child(argv[2], child_argv, probe, 1500, &result);
    int status;
    errno = 0;
    pid_t extra = waitpid(-1, &status, WNOHANG);
    bool no_children = extra < 0 && errno == ECHILD;
    printf("{\"returned\":%d,\"outcome\":\"%s\",\"error_code\":%d,"
           "\"child_reaped\":%s,\"packet_valid\":%s,\"no_children\":%s,"
           "\"exit_code\":%d,\"term_signal\":%d,\"assessment\":\"%s\"}\n",
           returned, outcome_name(result.outcome), result.error_code,
           result.child_reaped ? "true" : "false", result.packet_valid ? "true" : "false",
           no_children ? "true" : "false", result.exit_code, result.term_signal,
           assessment_name(pear_assess_abi(probe, &result, PEAR_SPAWN_DEFAULT)));
    return 0;
}
