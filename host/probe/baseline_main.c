#include "baseline.h"
#include "observations.h"

#include <errno.h>
#include <inttypes.h>
#include <limits.h>
#include <mach-o/dyld.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHILD_TIMEOUT_MS 3000

typedef struct {
    pear_probe_id id;
    const char *name;
    const char *steps[PEAR_BASELINE_STEPS];
    unsigned count;
} probe_spec;

static const probe_spec probes[] = {
    {PEAR_PROBE_MEMORY, "memory", {"allocate", "write_read", "protect_read",
        "restore_write", "rewrite_read", "release"}, 6},
    {PEAR_PROBE_PROTECTION, "protection", {"allocate", "write_read", "protect_read",
        "unexpected_write", "unused", "release"}, 6},
    {PEAR_PROBE_LOW_ADDRESS, "low-address", {"allocate", "write_read", "release"}, 3},
    {PEAR_PROBE_JIT, "jit", {"allocate", "write", "publish", "icache_sync", "execute", "release"}, 6}
};

static int child_path(char path[PATH_MAX])
{
    char executable[PATH_MAX], resolved[PATH_MAX];
    uint32_t size = sizeof(executable);
    if (_NSGetExecutablePath(executable, &size) != 0) return ENAMETOOLONG;
    if (realpath(executable, resolved) == NULL) return errno;
    char *separator = strrchr(resolved, '/');
    if (separator == NULL) return EINVAL;
    *separator = '\0';
    int length = snprintf(path, PATH_MAX, "%s/pear-probe-child", resolved);
    return length < 0 || length >= PATH_MAX ? ENAMETOOLONG : 0;
}

static const char *run_name(pear_run_outcome outcome)
{
    switch (outcome) {
        case PEAR_RUN_EXITED: return "exited";
        case PEAR_RUN_SIGNALED: return "signaled";
        case PEAR_RUN_TIMED_OUT: return "timed_out";
        case PEAR_RUN_OUTPUT_LIMIT: return "output_limit";
        case PEAR_RUN_SPAWN_ERROR: return "spawn_error";
        case PEAR_RUN_IO_ERROR: return "io_error";
        case PEAR_RUN_INVALID_OUTPUT: return "invalid_output";
    }
    return "io_error";
}

static const char *assessment_name(pear_baseline_outcome outcome)
{
    return outcome == PEAR_BASELINE_PASSED ? "passed" :
           outcome == PEAR_BASELINE_UNAVAILABLE ? "unavailable" : "failed";
}

static void write_step(const pear_baseline_step *step)
{
    const char *status = step->status == PEAR_STEP_PASSED ? "passed" :
        step->status == PEAR_STEP_UNAVAILABLE ? "unavailable" :
        step->status == PEAR_STEP_FAILED ? "failed" : "not_run";
    printf("{\"status\":\"%s\",\"value\":", status);
    if (step->status == PEAR_STEP_NOT_RUN) fputs("null", stdout);
    else printf("%" PRId64, step->value);
    fputs(",\"error\":", stdout);
    if (step->error_domain == PEAR_DOMAIN_NONE) fputs("null", stdout);
    else {
        const char *domain = step->error_domain == PEAR_DOMAIN_ERRNO ? "errno" :
            step->error_domain == PEAR_DOMAIN_MACH ? "mach" : "internal";
        printf("{\"domain\":\"%s\",\"code\":%" PRId64 "}", domain, step->error_code);
    }
    fputc('}', stdout);
}

static void write_result(const probe_spec *spec, const pear_child_result *result,
                         pear_baseline_outcome assessment)
{
    printf("{\"name\":\"%s\",\"status\":\"%s\",\"execution\":{\"outcome\":\"%s\","
           "\"exit_code\":", spec->name, assessment_name(assessment), run_name(result->outcome));
    if (result->exit_code >= 0) printf("%d", result->exit_code);
    else fputs("null", stdout);
    fputs(",\"signal\":", stdout);
    if (result->term_signal > 0) printf("%d", result->term_signal);
    else fputs("null", stdout);
    printf(",\"error_code\":%d,\"elapsed_ms\":%" PRIu64
           ",\"stdout_bytes\":%zu,\"stderr_bytes\":%zu,\"packet_valid\":%s,\"child_reaped\":%s},"
           "\"expected_fault_observed\":%s,\"steps\":{",
           result->error_code, result->elapsed_ms, result->stdout_bytes, result->stderr_bytes,
           result->packet_valid ? "true" : "false", result->child_reaped ? "true" : "false",
           spec->id == PEAR_PROBE_PROTECTION && assessment == PEAR_BASELINE_PASSED ? "true" : "false");
    if (result->packet_valid) {
        for (unsigned i = 0; i < spec->count; ++i) {
            if (i > 0) fputc(',', stdout);
            printf("\"%s\":", spec->steps[i]);
            write_step(&result->packet.steps[i]);
        }
    }
    fputs("}}", stdout);
}

int main(int argc, char **argv)
{
    if (argc == 2 && strcmp(argv[1], "--help") == 0) {
        puts("Usage: pear-baseline-probe [--help]\n"
             "Run isolated native memory/protection, low-address and fixed JIT leaf trials.\n"
             "This does not qualify restricted capabilities or a game runtime.");
        return 0;
    }
    if (argc != 1) {
        fputs("Usage: pear-baseline-probe [--help]\n", stderr);
        return 2;
    }
    char path[PATH_MAX];
    int path_error = child_path(path);
    pear_report observations;
    pear_collect(pear_system_source(), &observations);
    fputs("{\"schema_version\":1,\"record_kind\":\"baseline_execution\","
          "\"scope\":\"owned_test_children\",\"timeout_ms\":3000,\"parent_observations\":", stdout);
    if (pear_write_json(stdout, &observations) != 0) return 1;
    fputs(",\"probes\":[", stdout);
    bool failed = false;
    for (unsigned i = 0; i < sizeof(probes) / sizeof(probes[0]); ++i) {
        pear_child_result result = {0};
        result.exit_code = -1;
        if (path_error != 0) {
            result.outcome = PEAR_RUN_SPAWN_ERROR;
            result.error_code = path_error;
        } else {
            char *arguments[] = {path, (char *)probes[i].name, NULL};
            if (pear_run_child(path, arguments, probes[i].id, CHILD_TIMEOUT_MS, &result) != 0) {
                result.outcome = PEAR_RUN_IO_ERROR;
                result.error_code = EINVAL;
            }
        }
        pear_baseline_outcome assessment = pear_assess_baseline(probes[i].id, &result);
        if (assessment == PEAR_BASELINE_FAILED) failed = true;
        if (i > 0) fputc(',', stdout);
        write_result(&probes[i], &result, assessment);
    }
    fputs("],\"qualification\":{\"runtime\":\"not_assessed\","
          "\"rosetta_free_game\":\"not_assessed\",\"distribution\":\"not_assessed\"}}\n", stdout);
    if (fflush(stdout) != 0 || ferror(stdout)) return 1;
    return failed ? 1 : 0;
}
