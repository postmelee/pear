#include "thread_probe.h"

#include <dlfcn.h>
#include <errno.h>
#include <pthread.h>
#include <sched.h>
#include <stdatomic.h>
#include <stdbool.h>
#include <stdlib.h>
#include <time.h>

#define WORKERS 2U
#define WORK_MILLISECONDS 6000U
#define CLEANUP_MILLISECONDS 2000U

enum { POLICY_SEQUENCE_INVALID = 1, LITMUS_FORBIDDEN, LITMUS_VALUE_INVALID };

typedef struct thread_trial thread_trial;

typedef struct {
    thread_trial *trial;
    unsigned index;
    pthread_t thread;
    bool created, joined;
    _Atomic bool done;
    _Atomic unsigned ready_phase;
    _Atomic unsigned completed_epoch;
    kern_return_t initial, enabled, restored;
    bool initial_called, enabled_called, restore_called;
    uint64_t result;
} trial_worker;

struct thread_trial {
    pear_thread_policy_function policy;
    bool litmus;
    _Atomic bool stop;
    _Atomic unsigned epoch;
    _Atomic unsigned phase;
    /* Separate cache lines reduce accidental coupling between the payload words. */
    _Alignas(128) uint32_t data;
    _Alignas(128) uint32_t flag;
    _Alignas(128) trial_worker workers[WORKERS];
};

typedef struct {
    pear_baseline_domain domain;
    int64_t code;
} trial_error;

static void step(pear_baseline_packet *packet, unsigned index,
                 pear_step_status status, trial_error error, int64_t value)
{
    packet->steps[index] = (pear_baseline_step){status, error.domain, error.code, value};
}

static void passed(pear_baseline_packet *packet, unsigned index, int64_t value)
{
    step(packet, index, PEAR_STEP_PASSED, (trial_error){PEAR_DOMAIN_NONE, 0}, value);
}

static void failed(pear_baseline_packet *packet, unsigned index,
                   trial_error error, int64_t value)
{
    step(packet, index, PEAR_STEP_FAILED, error, value);
}

static trial_error system_error(int code)
{
    return (trial_error){PEAR_DOMAIN_ERRNO, code};
}

static trial_error policy_error(kern_return_t code)
{
    return (trial_error){PEAR_DOMAIN_MACH, code};
}

static trial_error internal_error(int code)
{
    return (trial_error){PEAR_DOMAIN_INTERNAL, code};
}

static bool now_milliseconds(uint64_t *value)
{
    struct timespec now;
    if (clock_gettime(CLOCK_MONOTONIC, &now) != 0) return false;
    *value = (uint64_t)now.tv_sec * UINT64_C(1000) + (uint64_t)now.tv_nsec / UINT64_C(1000000);
    return true;
}

static trial_error within_deadline(uint64_t deadline)
{
    uint64_t now;
    if (!now_milliseconds(&now)) return system_error(errno);
    return now < deadline ? (trial_error){PEAR_DOMAIN_NONE, 0} : system_error(ETIMEDOUT);
}

static pear_thread_policy_function resolve_policy(void)
{
#ifdef PEAR_THREAD_PROBE_TEST
    return pear_test_thread_policy_resolve();
#else
    /* The SDK declares kern_return_t thread_set_x86_64_compat(uint32_t enable).
     * No getter is exposed; return codes are not reported as observed state. */
    return (pear_thread_policy_function)dlsym(RTLD_DEFAULT, "thread_set_x86_64_compat");
#endif
}

static void *run_worker(void *argument)
{
    trial_worker *worker = argument;
    thread_trial *trial = worker->trial;
    worker->initial_called = true;
    worker->initial = trial->policy(0);
    if (worker->initial != KERN_SUCCESS) goto cleanup;
    if (!trial->litmus) {
        worker->enabled_called = true;
        worker->enabled = trial->policy(1);
        goto cleanup;
    }
    atomic_store_explicit(&worker->ready_phase, 1, memory_order_release);
    unsigned previous_epoch = 0;
    unsigned spins = 0;
    while (!atomic_load_explicit(&trial->stop, memory_order_acquire)) {
        if (atomic_load_explicit(&trial->phase, memory_order_acquire) == 1 && !worker->enabled_called) {
            worker->enabled_called = true;
            worker->enabled = trial->policy(1);
            if (worker->enabled != KERN_SUCCESS) goto cleanup;
            atomic_store_explicit(&worker->ready_phase, 2, memory_order_release);
        }
        unsigned epoch = atomic_load_explicit(&trial->epoch, memory_order_acquire);
        if (epoch == previous_epoch) {
            if (++spins % 4096U == 0) (void)sched_yield();
            continue;
        }
        /* All potentially conflicting payload accesses are in standalone
         * assembly. C atomics synchronize setup and result collection only. */
        if (worker->index == 0) pear_litmus_write(&trial->data, &trial->flag);
        else worker->result = pear_litmus_read(&trial->data, &trial->flag);
        previous_epoch = epoch;
        atomic_store_explicit(&worker->completed_epoch, epoch, memory_order_release);
    }
cleanup:
    worker->restore_called = true;
    worker->restored = trial->policy(0);
    atomic_store_explicit(&worker->done, true, memory_order_release);
    return NULL;
}

static thread_trial *prepare(pear_baseline_packet *packet, bool litmus,
                             uint64_t *deadline)
{
    pear_thread_policy_function policy = resolve_policy();
    if (policy == NULL) {
        step(packet, 0, PEAR_STEP_UNAVAILABLE, internal_error(ENOSYS), 0);
        return NULL;
    }
    uint64_t now;
    if (!now_milliseconds(&now)) {
        failed(packet, 0, system_error(errno), 0);
        return NULL;
    }
    /* C11 aligned_alloc keeps the over-aligned payload words correctly aligned. */
    thread_trial *trial = aligned_alloc(_Alignof(thread_trial), sizeof(thread_trial));
    if (trial == NULL) {
        failed(packet, 0, system_error(errno ? errno : ENOMEM), 0);
        return NULL;
    }
    *trial = (thread_trial){0};
    trial->policy = policy;
    trial->litmus = litmus;
    atomic_init(&trial->stop, false);
    atomic_init(&trial->epoch, 0);
    atomic_init(&trial->phase, 0);
    for (unsigned i = 0; i < WORKERS; ++i) {
        trial->workers[i].trial = trial;
        trial->workers[i].index = i;
        atomic_init(&trial->workers[i].done, false);
        atomic_init(&trial->workers[i].ready_phase, 0);
        atomic_init(&trial->workers[i].completed_epoch, 0);
    }
    *deadline = now + WORK_MILLISECONDS;
    return trial;
}

static trial_error create_workers(thread_trial *trial, unsigned *created)
{
    *created = 0;
    for (unsigned i = 0; i < WORKERS; ++i) {
        trial_worker *worker = &trial->workers[i];
        int error = pthread_create(&worker->thread, NULL, run_worker, worker);
        if (error != 0) return system_error(error);
        worker->created = true;
        ++*created;
    }
    return (trial_error){PEAR_DOMAIN_NONE, 0};
}

static trial_error wait_ready(thread_trial *trial, unsigned phase, uint64_t deadline)
{
    unsigned spins = 0;
    for (;;) {
        bool ready = true;
        for (unsigned i = 0; i < WORKERS; ++i) {
            trial_worker *worker = &trial->workers[i];
            if (atomic_load_explicit(&worker->ready_phase, memory_order_acquire) >= phase) continue;
            ready = false;
            if (atomic_load_explicit(&worker->done, memory_order_acquire)) {
                kern_return_t result = phase == 1 ? worker->initial : worker->enabled;
                return result != KERN_SUCCESS ? policy_error(result) : internal_error(POLICY_SEQUENCE_INVALID);
            }
        }
        if (ready) return (trial_error){PEAR_DOMAIN_NONE, 0};
        trial_error error = within_deadline(deadline);
        if (error.code != 0) return error;
        if (++spins % 4096U == 0) (void)sched_yield();
    }
}

static trial_error wait_completed(thread_trial *trial, unsigned epoch, uint64_t deadline)
{
    unsigned spins = 0;
    for (;;) {
        bool ready = true;
        for (unsigned i = 0; i < WORKERS; ++i) {
            trial_worker *worker = &trial->workers[i];
            if (atomic_load_explicit(&worker->completed_epoch, memory_order_acquire) != epoch) ready = false;
            if (atomic_load_explicit(&worker->done, memory_order_acquire)) return internal_error(POLICY_SEQUENCE_INVALID);
        }
        if (ready) return (trial_error){PEAR_DOMAIN_NONE, 0};
        trial_error error = within_deadline(deadline);
        if (error.code != 0) return error;
        if (++spins % 4096U == 0) (void)sched_yield();
    }
}

static trial_error run_phase(thread_trial *trial, unsigned first_epoch,
                              uint64_t deadline, unsigned *completed, unsigned *forbidden)
{
    *completed = 0;
    *forbidden = 0;
    for (unsigned i = 0; i < PEAR_THREAD_LITMUS_TRIALS; ++i) {
        pear_litmus_reset(&trial->data, &trial->flag);
        unsigned epoch = first_epoch + i;
        atomic_store_explicit(&trial->epoch, epoch, memory_order_release);
        trial_error error = wait_completed(trial, epoch, deadline);
        if (error.code != 0) return error;
        uint64_t result = trial->workers[1].result;
        uint32_t observed_flag = (uint32_t)result;
        uint32_t observed_data = (uint32_t)(result >> 32);
        if (observed_flag > 1 || observed_data > 1) return internal_error(LITMUS_VALUE_INVALID);
        ++*completed;
        if (observed_flag == 1 && observed_data == 0) ++*forbidden;
    }
    return (trial_error){PEAR_DOMAIN_NONE, 0};
}

static trial_error cleanup_workers(thread_trial *trial, unsigned *joined)
{
    atomic_store_explicit(&trial->stop, true, memory_order_release);
    *joined = 0;
    trial_error first = {PEAR_DOMAIN_NONE, 0};
    uint64_t now, deadline = 0;
    if (now_milliseconds(&now)) deadline = now + CLEANUP_MILLISECONDS;
    else first = system_error(errno);
    for (unsigned i = 0; i < WORKERS; ++i) {
        trial_worker *worker = &trial->workers[i];
        if (!worker->created) continue;
        while (!atomic_load_explicit(&worker->done, memory_order_acquire)) {
            trial_error error = within_deadline(deadline);
            if (error.code != 0) {
                if (first.code == 0) first = error;
                break;
            }
            (void)sched_yield();
        }
        if (!atomic_load_explicit(&worker->done, memory_order_acquire)) continue;
        int error = pthread_join(worker->thread, NULL);
        if (error != 0) {
            if (first.code == 0) first = system_error(error);
            continue;
        }
        worker->joined = true;
        ++*joined;
        if (!worker->restore_called) {
            if (first.code == 0) first = internal_error(POLICY_SEQUENCE_INVALID);
        } else if (worker->restored != KERN_SUCCESS && first.code == 0) {
            first = policy_error(worker->restored);
        }
    }
    return first;
}

static void release_trial(thread_trial *trial)
{
    for (unsigned i = 0; i < WORKERS; ++i)
        if (trial->workers[i].created && !trial->workers[i].joined) return;
    free(trial);
    /* Unconfirmed workers retain their storage until this disposable child
     * exits. The outer owned-process deadline remains the final containment. */
}

void pear_thread_probe(pear_baseline_packet *packet)
{
    uint64_t deadline;
    thread_trial *trial = prepare(packet, false, &deadline);
    if (trial == NULL) return;
    passed(packet, 0, 1);
    unsigned created = 0, joined = 0;
    trial_error error = create_workers(trial, &created);
    if (error.code != 0) failed(packet, 1, error, created);
    else passed(packet, 1, WORKERS);
    if (error.code == 0) {
        bool all_done = false;
        while (!all_done) {
            all_done = true;
            for (unsigned i = 0; i < WORKERS; ++i)
                if (!atomic_load_explicit(&trial->workers[i].done, memory_order_acquire)) all_done = false;
            if (all_done) break;
            error = within_deadline(deadline);
            if (error.code != 0) break;
            (void)sched_yield();
        }
        if (error.code != 0) failed(packet, 2, error, 0);
        else {
            for (unsigned phase = 0; phase < 3; ++phase) {
                unsigned successful = 0;
                trial_error phase_error = {PEAR_DOMAIN_NONE, 0};
                for (unsigned i = 0; i < WORKERS; ++i) {
                    trial_worker *worker = &trial->workers[i];
                    bool called = phase == 0 ? worker->initial_called : phase == 1 ? worker->enabled_called : worker->restore_called;
                    kern_return_t result = phase == 0 ? worker->initial : phase == 1 ? worker->enabled : worker->restored;
                    if (!called) {
                        if (phase_error.code == 0) phase_error = internal_error(POLICY_SEQUENCE_INVALID);
                    } else if (result != KERN_SUCCESS) {
                        if (phase_error.code == 0) phase_error = policy_error(result);
                    } else ++successful;
                }
                if (phase_error.code != 0) {
                    failed(packet, 2 + phase, phase_error, successful);
                    break;
                }
                passed(packet, 2 + phase, successful);
            }
        }
    }
    trial_error cleanup = cleanup_workers(trial, &joined);
    if (cleanup.code != 0) failed(packet, 5, cleanup, joined);
    else passed(packet, 5, joined);
    release_trial(trial);
}

void pear_thread_litmus_probe(pear_baseline_packet *packet)
{
    uint64_t deadline;
    thread_trial *trial = prepare(packet, true, &deadline);
    if (trial == NULL) return;
    unsigned created = 0, joined = 0, completed = 0, forbidden = 0;
    trial_error error = create_workers(trial, &created);
    if (error.code == 0) error = wait_ready(trial, 1, deadline);
    if (error.code != 0) {
        failed(packet, 0, error, created);
        goto cleanup;
    }
    passed(packet, 0, WORKERS);
    error = run_phase(trial, 1, deadline, &completed, &forbidden);
    if (error.code != 0) {
        failed(packet, 1, error, completed);
        goto cleanup;
    }
    passed(packet, 1, completed);
    passed(packet, 2, forbidden);
    atomic_store_explicit(&trial->phase, 1, memory_order_release);
    error = wait_ready(trial, 2, deadline);
    if (error.code != 0) {
        failed(packet, 3, error, 0);
        goto cleanup;
    }
    error = run_phase(trial, PEAR_THREAD_LITMUS_TRIALS + 1, deadline, &completed, &forbidden);
    if (error.code != 0) {
        failed(packet, 3, error, completed);
        goto cleanup;
    }
    passed(packet, 3, completed);
    if (forbidden != 0) failed(packet, 4, internal_error(LITMUS_FORBIDDEN), forbidden);
    else passed(packet, 4, 0);
cleanup:
    error = cleanup_workers(trial, &joined);
    if (error.code != 0) failed(packet, 5, error, joined);
    else passed(packet, 5, joined);
    release_trial(trial);
}
