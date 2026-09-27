#ifndef PEAR_BASELINE_H
#define PEAR_BASELINE_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* Private same-build, same-host protocol; never a persisted cross-host ABI. */
#define PEAR_BASELINE_MAGIC UINT32_C(0x50425232)
#define PEAR_BASELINE_VERSION 1
#define PEAR_BASELINE_STEPS 6
#define PEAR_BASELINE_STDERR_LIMIT 1024

typedef enum {
    PEAR_PROBE_MEMORY = 1, PEAR_PROBE_PROTECTION, PEAR_PROBE_LOW_ADDRESS,
    PEAR_PROBE_JIT, PEAR_PROBE_GEOMETRY, PEAR_PROBE_SUBPAGE,
    PEAR_PROBE_SUBPAGE_FAULT, PEAR_PROBE_RECOMMIT, PEAR_PROBE_RECOMMIT_FAULT
} pear_probe_id;
typedef enum { PEAR_PACKET_COMPLETE = 1, PEAR_PACKET_ARMED = 2 } pear_packet_phase;
typedef enum {
    PEAR_STEP_NOT_RUN = 0, PEAR_STEP_PASSED, PEAR_STEP_UNAVAILABLE, PEAR_STEP_FAILED
} pear_step_status;
typedef enum {
    PEAR_DOMAIN_NONE = 0, PEAR_DOMAIN_ERRNO, PEAR_DOMAIN_MACH, PEAR_DOMAIN_INTERNAL
} pear_baseline_domain;
typedef struct {
    uint32_t status;
    uint32_t error_domain;
    int64_t error_code;
    int64_t value;
} pear_baseline_step;
typedef struct {
    uint32_t magic;
    uint32_t version;
    uint32_t probe;
    uint32_t phase;
    pear_baseline_step steps[PEAR_BASELINE_STEPS];
} pear_baseline_packet;
_Static_assert(sizeof(pear_baseline_step) == 24, "Unexpected step layout");
_Static_assert(sizeof(pear_baseline_packet) == 160, "Unexpected packet layout");

typedef enum {
    PEAR_RUN_EXITED = 0, PEAR_RUN_SIGNALED, PEAR_RUN_TIMED_OUT,
    PEAR_RUN_OUTPUT_LIMIT, PEAR_RUN_SPAWN_ERROR, PEAR_RUN_IO_ERROR,
    PEAR_RUN_INVALID_OUTPUT
} pear_run_outcome;
typedef struct {
    pear_run_outcome outcome;
    int exit_code;
    int term_signal;
    int error_code;
    uint64_t elapsed_ms;
    size_t stdout_bytes;
    size_t stderr_bytes;
    bool packet_valid;
    bool child_reaped;
    pear_baseline_packet packet;
    bool page_attribute_called;
    int page_attribute_error;
} pear_child_result;

/* Spawns one owned process group; caps pipes/deadline and reaps its leader.
 * Cleanup has a separate one-second budget. A cleanup failure is explicit and
 * may leave child_reaped false; this function never waits indefinitely.
 * argv is an explicit NULL-terminated array, not shell text. The caller must
 * not concurrently reap the child; this is lifecycle control, not a sandbox.
 * timeout_ms must be 1..60000. Return 0 when a result was collected, -1 for
 * invalid arguments. All launch/runtime errors are also represented in result.
 */
int pear_run_child(const char *path, char *const argv[], pear_probe_id expected,
                   unsigned timeout_ms, pear_child_result *result);

typedef enum { PEAR_SPAWN_DEFAULT = 0, PEAR_SPAWN_PAGES_4K } pear_spawn_mode;
int pear_run_child_mode(const char *path, char *const argv[], pear_probe_id expected,
                       unsigned timeout_ms, pear_spawn_mode mode,
                       pear_child_result *result);

/* Internal child entry points used by the provisioned self-spawning probe. */
int pear_baseline_child_main(int argc, char **argv);
int pear_process_child_main(pear_probe_id probe);

typedef enum {
    PEAR_BASELINE_PASSED = 0, PEAR_BASELINE_UNAVAILABLE, PEAR_BASELINE_FAILED
} pear_baseline_outcome;
/* Evaluate only a runner-validated packet and its actual termination evidence. */
pear_baseline_outcome pear_assess_baseline(pear_probe_id probe,
                                          const pear_child_result *result);
pear_baseline_outcome pear_assess_process(pear_probe_id probe,
                                         const pear_child_result *result,
                                         pear_spawn_mode mode);

#endif
