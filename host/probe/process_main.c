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
#define ABI_TIMEOUT_MS 10000

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
    {PEAR_PROBE_JIT, "jit", {"allocate", "write", "publish", "icache_sync", "execute", "release"}, 6},
    {PEAR_PROBE_GEOMETRY, "geometry", {"user_page_size", "vm_page_size", "kernel_page_size"}, 3},
    {PEAR_PROBE_SUBPAGE, "subpage", {"allocate", "initial_sentinels", "protect_middle",
        "restore_middle", "verify_neighbors", "release"}, 6},
    {PEAR_PROBE_SUBPAGE_FAULT, "subpage-fault", {"allocate", "initial_sentinels", "protect_middle",
        "restore_middle", "verify_neighbors", "release"}, 6},
    {PEAR_PROBE_RECOMMIT, "recommit", {"allocate", "initial_sentinels", "replace_middle",
        "verify_neighbors", "recommit_zero_and_write", "release"}, 6},
    {PEAR_PROBE_RECOMMIT_FAULT, "recommit-fault", {"allocate", "initial_sentinels", "replace_middle",
        "verify_neighbors", "recommit_zero_and_write", "release"}, 6},
    {PEAR_PROBE_X18_ROUNDTRIP, "x18-roundtrip", {"host_entry", "foreign_entry", "guest_before",
        "guest_after_getter", "host_exit", "completed_roundtrips"}, 6},
    {PEAR_PROBE_X18_CALLBACKS, "x18-callbacks", {"host_entry", "host_callbacks", "nested_guest_returns",
        "outer_guest_restores", "injected_error_returns", "host_exit"}, 6},
    {PEAR_PROBE_X18_SIGNALS, "x18-signals", {"symbols_resolved", "host_handler_entry", "foreign_handler_entry",
        "host_handler_body_calls", "resumed_guest_preserved", "host_exit"}, 6},
    {PEAR_PROBE_THREAD_POLICY, "thread-policy", {"api_resolved", "created_threads", "initialized_threads",
        "enabled_threads", "restored_threads", "joined_threads"}, 6},
    {PEAR_PROBE_THREAD_LITMUS, "thread-litmus", {"initialized_workers", "baseline_trials", "baseline_forbidden",
        "enabled_trials", "enabled_forbidden", "restored_and_joined_workers"}, 6}
};

static int self_path(char path[PATH_MAX])
{
    char executable[PATH_MAX];
    uint32_t size = sizeof(executable);
    if (_NSGetExecutablePath(executable, &size) != 0) return ENAMETOOLONG;
    return realpath(executable, path) == NULL ? errno : 0;
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
           ",\"stdout_bytes\":%zu,\"stderr_bytes\":%zu,\"packet_valid\":%s,\"child_reaped\":%s,\"page_attribute_called\":%s,\"page_attribute_error\":%d},"
           "\"expected_fault_observed\":%s,\"steps\":{",
           result->error_code, result->elapsed_ms, result->stdout_bytes, result->stderr_bytes,
           result->packet_valid ? "true" : "false", result->child_reaped ? "true" : "false",
           result->page_attribute_called ? "true" : "false", result->page_attribute_error,
           (spec->id == PEAR_PROBE_PROTECTION || spec->id == PEAR_PROBE_SUBPAGE_FAULT ||
            spec->id == PEAR_PROBE_RECOMMIT_FAULT) && assessment == PEAR_BASELINE_PASSED ? "true" : "false");
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
    if (argc == 3 && strcmp(argv[1], "--child") == 0) {
        for (unsigned i = 0; i < sizeof(probes) / sizeof(probes[0]); ++i) {
            if (strcmp(argv[2], probes[i].name) != 0) continue;
            if (probes[i].id <= PEAR_PROBE_JIT) {
                char *arguments[] = {argv[0], argv[2], NULL};
                return pear_baseline_child_main(2, arguments);
            }
            if (probes[i].id >= PEAR_PROBE_THREAD_POLICY)
                return pear_thread_child_main(probes[i].id);
            if (probes[i].id >= PEAR_PROBE_X18_ROUNDTRIP)
                return pear_abi_child_main(probes[i].id);
            return pear_process_child_main(probes[i].id);
        }
        return 2;
    }
    if (argc == 2 && strcmp(argv[1], "--help") == 0) {
        puts("Usage: pear-process-probe --mode default|4k [--suite abi]\n"
             "Run only from the verified provisioned development bundle.\n"
             "Finite probe success does not qualify a runtime or game.");
        return 0;
    }
    if ((argc != 3 && argc != 5) || strcmp(argv[1], "--mode") != 0 ||
        (argc == 5 && (strcmp(argv[3], "--suite") != 0 || strcmp(argv[4], "abi") != 0)) ||
        (strcmp(argv[2], "default") != 0 && strcmp(argv[2], "4k") != 0)) {
        fputs("Usage: pear-process-probe --mode default|4k [--suite abi]\n", stderr);
        return 2;
    }
    bool abi = argc == 5;
    unsigned timeout = abi ? ABI_TIMEOUT_MS : CHILD_TIMEOUT_MS;
    pear_spawn_mode mode = strcmp(argv[2], "4k") == 0 ? PEAR_SPAWN_PAGES_4K : PEAR_SPAWN_DEFAULT;
    char path[PATH_MAX];
    int path_error = self_path(path);
    pear_report observations;
    pear_collect(pear_system_source(), &observations);
    printf("{\"schema_version\":1,\"record_kind\":\"%s\","
           "\"scope\":\"owned_test_children\",\"requested_mode\":\"%s\","
           "\"timeout_ms\":%u,\"parent_observations\":",
           abi ? "abi_capabilities" : "process_capabilities", argv[2], timeout);
    if (pear_write_json(stdout, &observations) != 0) return 1;
    fputs(",\"probes\":[", stdout);
    bool failed = false;
    unsigned count = abi ? 6 : mode == PEAR_SPAWN_PAGES_4K ? 9 : 5;
    for (unsigned i = 0; i < count; ++i) {
        const probe_spec *spec = &probes[abi ? (i == 0 ? 4 : i + 8) : i];
        pear_child_result result = {0};
        result.exit_code = -1;
        if (path_error != 0) {
            result.outcome = PEAR_RUN_SPAWN_ERROR;
            result.error_code = path_error;
        } else {
            char *arguments[] = {path, "--child", (char *)spec->name, NULL};
            if (pear_run_child_mode(path, arguments, spec->id, timeout,
                                    mode, &result) != 0) {
                result.outcome = PEAR_RUN_IO_ERROR;
                result.error_code = EINVAL;
            }
        }
        pear_baseline_outcome assessment = abi ? pear_assess_abi(spec->id, &result, mode) :
                                                pear_assess_process(spec->id, &result, mode);
        if (assessment == PEAR_BASELINE_FAILED) failed = true;
        if (i > 0) fputc(',', stdout);
        write_result(spec, &result, assessment);
    }
    fputs("],\"qualification\":{\"runtime\":\"not_assessed\","
          "\"rosetta_free_game\":\"not_assessed\",\"distribution\":\"not_assessed\"}}\n", stdout);
    if (fflush(stdout) != 0 || ferror(stdout)) return 1;
    return failed ? 1 : 0;
}
