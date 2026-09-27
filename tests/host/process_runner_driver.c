#include "baseline.h"

#include <dirent.h>
#include <errno.h>
#include <signal.h>
#include <spawn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>

/* Linked only to a separately compiled runner object. No restricted setter is
 * looked up or called by this fixture, including the simulated-success case.
 */
static const char *lookup_mode;
static unsigned lookup_calls, setter_calls;
static bool attributes_ready;

static int fake_page_attribute(const posix_spawnattr_t *attributes)
{
    ++setter_calls;
    short flags = 0;
    pid_t group = -1;
    int wanted = POSIX_SPAWN_SETPGROUP | POSIX_SPAWN_SETSIGMASK |
                 POSIX_SPAWN_SETSIGDEF | POSIX_SPAWN_CLOEXEC_DEFAULT;
    attributes_ready = posix_spawnattr_getflags(attributes, &flags) == 0 &&
                       posix_spawnattr_getpgroup(attributes, &group) == 0 &&
                       flags == wanted && group == 0;
    if (!attributes_ready)
        return EINVAL;
    return strcmp(lookup_mode, "reject") == 0 ? EPERM : 0;
}

void *pear_fixture_dlsym(void *handle, const char *symbol)
{
    (void)handle;
    ++lookup_calls;
    if (strcmp(symbol, "posix_spawnattr_set_4k_page_size_np") != 0 ||
        strcmp(lookup_mode, "missing") == 0)
        return NULL;
    return (void *)fake_page_attribute;
}

static int count_descriptors(void)
{
    DIR *directory = opendir("/dev/fd");
    if (directory == NULL)
        return -1;
    int count = 0;
    struct dirent *entry;
    errno = 0;
    while ((entry = readdir(directory)) != NULL)
        if (entry->d_name[0] >= '0' && entry->d_name[0] <= '9')
            ++count;
    int read_error = errno;
    if (closedir(directory) != 0 || read_error != 0)
        return -1;
    return count;
}

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

static void passed(pear_baseline_packet *packet, size_t index, int64_t value)
{
    packet->steps[index].status = PEAR_STEP_PASSED;
    packet->steps[index].value = value;
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
    bool fault = probe == PEAR_PROBE_SUBPAGE_FAULT ||
                 probe == PEAR_PROBE_RECOMMIT_FAULT;
    if (probe == PEAR_PROBE_GEOMETRY) {
        int64_t page_size = mode == PEAR_SPAWN_PAGES_4K ? 4096 : 16384;
        passed(&result.packet, 0, page_size);
        passed(&result.packet, 1, page_size);
        passed(&result.packet, 2, 16384);
    } else {
        const int64_t values[PEAR_BASELINE_STEPS] = {
            12288, 7, 0, probe == PEAR_PROBE_SUBPAGE ? 84 : 3,
            probe == PEAR_PROBE_SUBPAGE ? 3 : 42, 0
        };
        for (size_t i = 0; i < (fault ? 3 : PEAR_BASELINE_STEPS); ++i)
            passed(&result.packet, i, values[i]);
        if (fault) {
            result.outcome = PEAR_RUN_SIGNALED;
            result.exit_code = -1;
            result.term_signal = SIGBUS;
            result.packet.phase = PEAR_PACKET_ARMED;
        }
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
    else if (strcmp(mutation, "nonzero-exit") == 0)
        result->exit_code = 7;
    else if (strcmp(mutation, "timeout") == 0)
        result->outcome = PEAR_RUN_TIMED_OUT;
    else if (strcmp(mutation, "io-error") == 0) {
        result->outcome = PEAR_RUN_IO_ERROR;
        result->error_code = EIO;
    } else if (strcmp(mutation, "wrong-phase") == 0)
        result->packet.phase = result->packet.phase == PEAR_PACKET_ARMED ?
                               PEAR_PACKET_COMPLETE : PEAR_PACKET_ARMED;
    else if (strcmp(mutation, "wrong-signal") == 0)
        result->term_signal = SIGTERM;
    else if (strcmp(mutation, "sigsegv") == 0)
        result->term_signal = SIGSEGV;
    else if (strcmp(mutation, "armed-exit") == 0) {
        result->outcome = PEAR_RUN_EXITED;
        result->exit_code = 0;
        result->term_signal = 0;
    } else if (strcmp(mutation, "cleanup-failed") == 0) {
        result->packet.steps[5].status = PEAR_STEP_FAILED;
        result->packet.steps[5].error_domain = PEAR_DOMAIN_ERRNO;
        result->packet.steps[5].error_code = EIO;
    } else if (strcmp(mutation, "cleanup-not-run") == 0)
        memset(&result->packet.steps[5], 0, sizeof(result->packet.steps[5]));
    else if (strcmp(mutation, "allocation-unavailable") == 0) {
        memset(result->packet.steps, 0, sizeof(result->packet.steps));
        result->packet.steps[0].status = PEAR_STEP_UNAVAILABLE;
        result->packet.steps[0].error_domain = PEAR_DOMAIN_ERRNO;
        result->packet.steps[0].error_code = EPERM;
    } else if (strncmp(mutation, "value-", 6) == 0 && mutation[6] >= '0' &&
               mutation[6] <= '5' && mutation[7] == '\0')
        result->packet.steps[mutation[6] - '0'].value += 1;
    else if (strcmp(mutation, "geometry-zero-kernel") == 0)
        result->packet.steps[2].value = 0;
    else if (strcmp(mutation, "geometry-negative-kernel") == 0)
        result->packet.steps[2].value = -1;
    else if (strcmp(mutation, "geometry-mismatched-pages") == 0)
        result->packet.steps[1].value = 8192;
}

int main(int argc, char **argv)
{
    if (argc < 2)
        return 64;
    if (strcmp(argv[1], "assess") == 0) {
        if (argc != 5)
            return 65;
        pear_probe_id probe = (pear_probe_id)atoi(argv[2]);
        pear_spawn_mode mode = (pear_spawn_mode)atoi(argv[3]);
        pear_child_result result = successful_result(probe, mode);
        mutate(&result, argv[4]);
        printf("{\"assessment\":\"%s\"}\n",
               assessment_name(pear_assess_process(probe, &result, mode)));
        return 0;
    }
    if (strcmp(argv[1], "spawn") != 0 || argc != 7)
        return 66;
    lookup_mode = argv[3];
    pear_spawn_mode mode = strcmp(lookup_mode, "default") == 0 ?
        PEAR_SPAWN_DEFAULT : strcmp(lookup_mode, "invalid") == 0 ?
        (pear_spawn_mode)99 : PEAR_SPAWN_PAGES_4K;
    pear_probe_id probe = (pear_probe_id)atoi(argv[4]);
    char *child_argv[] = {argv[2], argv[4], argv[5], argv[6], NULL};
    pear_child_result result;
    int before = count_descriptors();
    int returned = pear_run_child_mode(argv[2], child_argv, probe, 1500, mode, &result);
    int after = count_descriptors();
    int status;
    errno = 0;
    pid_t extra = waitpid(-1, &status, WNOHANG);
    bool no_children = extra < 0 && errno == ECHILD;
    printf("{\"returned\":%d,\"outcome\":\"%s\",\"error_code\":%d,"
           "\"page_attribute_called\":%s,\"page_attribute_error\":%d,"
           "\"lookup_calls\":%u,\"setter_calls\":%u,\"attributes_ready\":%s,"
           "\"child_reaped\":%s,\"packet_valid\":%s,\"no_children\":%s,"
           "\"exit_code\":%d,\"term_signal\":%d,\"fd_before\":%d,\"fd_after\":%d,"
           "\"assessment\":\"%s\"}\n",
           returned, outcome_name(result.outcome), result.error_code,
           result.page_attribute_called ? "true" : "false", result.page_attribute_error,
           lookup_calls, setter_calls, attributes_ready ? "true" : "false",
           result.child_reaped ? "true" : "false", result.packet_valid ? "true" : "false",
           no_children ? "true" : "false", result.exit_code, result.term_signal, before, after,
           assessment_name(pear_assess_process(probe, &result, mode)));
    return 0;
}
