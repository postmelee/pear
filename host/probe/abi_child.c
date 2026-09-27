#include "abi.h"

#include <dlfcn.h>
#include <errno.h>
#include <fcntl.h>
#include <pthread.h>
#include <string.h>
#include <sys/resource.h>
#include <sys/ucontext.h>
#include <time.h>
#include <unistd.h>

/* Internal codes 20..24 identify missing APIs, state mismatches, callback
 * mismatches, signal evidence mismatches and incomplete signal delivery. */
enum {
    ABI_APIS_UNAVAILABLE = 20, ABI_STATE_MISMATCH, ABI_CALLBACK_MISMATCH,
    ABI_SIGNAL_MISMATCH, ABI_SIGNAL_INCOMPLETE
};
enum { ROUNDTRIPS = 64, CALLBACKS = 32, ERROR_CALLBACKS = 16 };
static const uint64_t outer_sentinel = UINT64_C(0x11223344);
static const uint64_t inner_sentinel = UINT64_C(0x55667788);

/* Initialized before installing the handler, then immutable until it is
 * restored. The handler and interrupted trial execute on the same thread. */
_Atomic(pear_abi_signal_state *) pear_abi_active_signal;

static void step(pear_baseline_packet *packet, unsigned index,
                 pear_step_status status, pear_baseline_domain domain,
                 int64_t error, int64_t value)
{
    packet->steps[index] = (pear_baseline_step){status, domain, error, value};
}

static void failed(pear_baseline_packet *packet, int code, int64_t value)
{
    step(packet, 0, PEAR_STEP_FAILED, PEAR_DOMAIN_INTERNAL, code, value);
}

static void passed_values(pear_baseline_packet *packet, const int64_t values[6])
{
    for (unsigned i = 0; i < 6; ++i)
        step(packet, i, PEAR_STEP_PASSED, PEAR_DOMAIN_NONE, 0, values[i]);
}

static int emit_packet(const pear_baseline_packet *packet)
{
    const unsigned char *bytes = (const unsigned char *)packet;
    size_t remaining = sizeof(*packet);
    while (remaining != 0) {
        ssize_t written = write(STDOUT_FILENO, bytes, remaining);
        if (written < 0 && errno == EINTR) continue;
        if (written <= 0) return 3;
        bytes += (size_t)written;
        remaining -= (size_t)written;
    }
    return 0;
}

static bool context_passed(const pear_abi_context *context, unsigned completed)
{
    return context->failure == 0 && context->host_entry == 0 &&
        context->foreign_entry == 1 && context->guest_before == context->sentinel &&
        context->guest_after == context->sentinel && context->host_exit == 0 &&
        context->completed == completed;
}

static void roundtrip_probe(pear_baseline_packet *packet, pear_abi_context *context)
{
    for (unsigned i = 0; i < ROUNDTRIPS; ++i) {
        if (pear_abi_roundtrip_thunk(context) != 0 || !context_passed(context, i + 1)) {
            failed(packet, ABI_STATE_MISMATCH, (int64_t)context->completed);
            return;
        }
    }
    const int64_t values[] = {
        context->host_entry, context->foreign_entry, context->guest_before,
        context->guest_after, context->host_exit, context->completed
    };
    passed_values(packet, values);
}

/* This entire C function runs in verified host mode. The inner thunk uses a
 * different sentinel so a mistaken global save slot cannot preserve both. */
static int host_callback(pear_abi_context *context, int inject_error)
{
    if (context->getter() || getpid() <= 0) {
        context->failure = 1;
        return 99;
    }
    ++context->callbacks;
    pear_abi_context nested = {.getter = context->getter, .setter = context->setter,
                               .sentinel = inner_sentinel};
    if (pear_abi_roundtrip_thunk(&nested) != 0 || !context_passed(&nested, 1)) {
        context->failure = 1;
        return 99;
    }
    ++context->nested;
    if (context->getter()) {
        context->failure = 1;
        return 99;
    }
    return inject_error ? -7 : 42;
}

static void callback_probe(pear_baseline_packet *packet, pear_abi_context *context)
{
    context->callback = host_callback;
    for (unsigned i = 0; i < CALLBACKS; ++i) {
        int inject_error = i >= CALLBACKS - ERROR_CALLBACKS;
        int expected = inject_error ? -7 : 42;
        int observed = pear_abi_callback_thunk(context, inject_error);
        if (observed != expected || context->failure != 0 || context->getter()) {
            failed(packet, ABI_CALLBACK_MISMATCH, observed);
            return;
        }
        if (inject_error) ++context->errors;
    }
    if (context->host_entry != 0 || context->callbacks != CALLBACKS ||
        context->nested != CALLBACKS || context->restores != CALLBACKS ||
        context->errors != ERROR_CALLBACKS || context->host_exit != 0) {
        failed(packet, ABI_CALLBACK_MISMATCH, context->callbacks);
        return;
    }
    const int64_t values[] = {
        context->host_entry, context->callbacks, context->nested,
        context->restores, context->errors, context->host_exit
    };
    passed_values(packet, values);
}

/* The assembly gateway has switched to host mode before reaching this body.
 * Only the documented getter, local loads/stores and async-signal-safe write
 * are used. No allocation, logging, mutex, TLS helper or context modification. */
static void signal_body(pear_abi_signal_state *state, int number,
                         void *context_pointer, int entry_mode)
{
    int saved_errno = *state->errno_location;
    ucontext_t *context = context_pointer;
    uint64_t expect_foreign = atomic_load_explicit(&state->expect_foreign, memory_order_relaxed);
    if (expect_foreign)
        atomic_store_explicit(&state->foreign_entry, (uint64_t)entry_mode, memory_order_relaxed);
    else atomic_store_explicit(&state->host_entry, (uint64_t)entry_mode, memory_order_relaxed);
    bool valid = !state->getter() && number == SIGUSR1 && context != NULL &&
                 context->uc_mcontext != NULL &&
                 entry_mode == (int)expect_foreign;
    if (valid && expect_foreign)
        valid = context->uc_mcontext->__ss.__x[18] == state->guest;
    if (valid) {
        const char marker = entry_mode ? 'F' : 'H';
        ssize_t count = state->writer(state->write_fd, &marker, 1);
        if (count == 1) {
            uint64_t calls = atomic_load_explicit(&state->body_calls, memory_order_relaxed);
            atomic_store_explicit(&state->body_calls, calls + 1, memory_order_relaxed);
        } else atomic_store_explicit(&state->failure, ABI_SIGNAL_INCOMPLETE, memory_order_relaxed);
    } else atomic_store_explicit(&state->failure, ABI_SIGNAL_MISMATCH, memory_order_relaxed);
    *state->errno_location = saved_errno;
}

typedef struct {
    pear_abi_signal_state *state;
    pthread_t target;
    int error;
} sender_context;

static void *send_signal(void *opaque)
{
    sender_context *sender = opaque;
    struct timespec start, now;
    if (clock_gettime(CLOCK_MONOTONIC, &start) != 0) {
        sender->error = errno;
        return NULL;
    }
    for (;;) {
        uint32_t ready = atomic_load_explicit(&sender->state->ready, memory_order_acquire);
        if (ready == 1) {
            sender->error = pthread_kill(sender->target, SIGUSR1);
            return NULL;
        }
        if (ready == 2) {
            sender->error = ECANCELED;
            return NULL;
        }
        if (clock_gettime(CLOCK_MONOTONIC, &now) != 0) {
            sender->error = errno;
            return NULL;
        }
        int64_t elapsed = ((int64_t)now.tv_sec - start.tv_sec) * INT64_C(1000000000) +
                           now.tv_nsec - start.tv_nsec;
        if (elapsed >= INT64_C(1000000000)) {
            sender->error = ETIMEDOUT;
            return NULL;
        }
        const struct timespec delay = {.tv_nsec = 1000000};
        if (nanosleep(&delay, NULL) != 0 && errno != EINTR) {
            sender->error = errno;
            return NULL;
        }
    }
}

static void signal_probe(pear_baseline_packet *packet, const pear_abi_context *context)
{
    int descriptors[2] = {-1, -1};
    int error = 0, cleanup_error = 0;
    bool mask_installed = false, handler_installed = false, thread_created = false;
    bool sender_started = false;
    sigset_t previous_mask, trial_mask, only_signal;
    struct sigaction previous_action, action;
    pthread_t sender_thread;
    pear_abi_signal_state state = {
        .getter = context->getter, .setter = context->setter, .body = signal_body,
        .guest = outer_sentinel, .host_entry = 2, .foreign_entry = 2,
        .errno_location = &errno,
        .writer = (ssize_t (*)(int, const void *, size_t))dlsym(RTLD_DEFAULT, "write"),
    };
    sender_context sender = {.state = &state, .target = pthread_self(), .error = 0};
    if (state.writer == NULL) {
        failed(packet, ABI_APIS_UNAVAILABLE, 0);
        goto cleanup;
    }
    if (sigemptyset(&only_signal) != 0 || sigaddset(&only_signal, SIGUSR1) != 0) {
        error = errno;
        goto cleanup;
    }
    if (pipe(descriptors) != 0) {
        error = errno;
        goto cleanup;
    }
    int flags = fcntl(descriptors[0], F_GETFL);
    if (flags < 0 || fcntl(descriptors[0], F_SETFL, flags | O_NONBLOCK) != 0) {
        error = errno;
        goto cleanup;
    }
    state.write_fd = descriptors[1];
    if (sigfillset(&trial_mask) != 0 || sigdelset(&trial_mask, SIGUSR1) != 0) {
        error = errno;
        goto cleanup;
    }
    error = pthread_sigmask(SIG_SETMASK, &trial_mask, &previous_mask);
    if (error != 0) goto cleanup;
    mask_installed = true;
    memset(&action, 0, sizeof(action));
    action.sa_sigaction = pear_abi_signal_gateway;
    action.sa_flags = SA_SIGINFO;
    if (sigfillset(&action.sa_mask) != 0) {
        error = errno;
        goto cleanup;
    }
    atomic_store_explicit(&pear_abi_active_signal, &state, memory_order_release);
    if (sigaction(SIGUSR1, &action, &previous_action) != 0) {
        error = errno;
        goto cleanup;
    }
    handler_installed = true;
    if (raise(SIGUSR1) != 0) {
        error = errno;
        goto cleanup;
    }
    if (state.host_entry != 0 || state.body_calls != 1 || state.failure != 0) {
        failed(packet, ABI_SIGNAL_MISMATCH, state.host_entry);
        goto cleanup;
    }
    atomic_store_explicit(&state.done, 0, memory_order_relaxed);
    state.expect_foreign = 1;
    error = pthread_create(&sender_thread, NULL, send_signal, &sender);
    if (error != 0) goto cleanup;
    thread_created = true;
    sender_started = true;
    int result = pear_abi_signal_wait_thunk(&state);
    atomic_store_explicit(&state.ready, 2, memory_order_release);
    error = pthread_join(sender_thread, NULL);
    if (error != 0) goto cleanup;
    thread_created = false;
    if (sender.error != 0) {
        error = sender.error;
        goto cleanup;
    }
    if (result != 0 || state.foreign_entry != 1 || state.body_calls != 2 ||
        state.resumed != 1 || state.host_exit != 0 || state.failure != 0) {
        failed(packet, ABI_SIGNAL_MISMATCH, state.failure);
        goto cleanup;
    }
    char markers[2];
    ssize_t count = read(descriptors[0], markers, sizeof(markers));
    if (count != 2 || markers[0] != 'H' || markers[1] != 'F') {
        failed(packet, ABI_SIGNAL_INCOMPLETE, count);
        goto cleanup;
    }
    const int64_t values[] = {2, state.host_entry, state.foreign_entry,
                              state.body_calls, state.resumed, state.host_exit};
    passed_values(packet, values);

cleanup:
    /* Stop delivery before changing the handler/global pointer. A sender that
     * passed the handshake just before a spin timeout may still have queued
     * SIGUSR1. Join it, then drain that owned pending signal while blocked. */
    if (mask_installed) {
        int blocked = pthread_sigmask(SIG_BLOCK, &only_signal, NULL);
        if (blocked != 0) cleanup_error = blocked;
    }
    if (thread_created) {
        atomic_store_explicit(&state.ready, 2, memory_order_release);
        int joined = pthread_join(sender_thread, NULL);
        /* Returning would leave a thread with a pointer into this stack. A
         * missing packet and exit 3 are deliberate failed-child evidence. */
        if (joined != 0) _exit(3);
    }
    if (cleanup_error != 0) _exit(3);
    if (sender_started && sender.error == 0 && mask_installed) {
        sigset_t pending;
        if (sigpending(&pending) != 0) _exit(3);
        int queued = sigismember(&pending, SIGUSR1);
        if (queued < 0) _exit(3);
        if (queued) {
            int received = 0;
            if (sigwait(&only_signal, &received) != 0 || received != SIGUSR1) _exit(3);
        }
    }
    if (handler_installed && sigaction(SIGUSR1, &previous_action, NULL) != 0)
        _exit(3);
    atomic_store_explicit(&pear_abi_active_signal, NULL, memory_order_release);
    if (mask_installed) {
        int restored = pthread_sigmask(SIG_SETMASK, &previous_mask, NULL);
        if (restored != 0) cleanup_error = restored;
    }
    for (unsigned i = 0; i < 2; ++i)
        if (descriptors[i] >= 0 && close(descriptors[i]) != 0) cleanup_error = errno;
    if (error != 0) step(packet, 0, PEAR_STEP_FAILED, PEAR_DOMAIN_ERRNO, error, 0);
    if (cleanup_error != 0)
        step(packet, 5, PEAR_STEP_FAILED, PEAR_DOMAIN_ERRNO, cleanup_error, 0);
}

int pear_abi_child_main(pear_probe_id probe)
{
    if (probe < PEAR_PROBE_X18_ROUNDTRIP || probe > PEAR_PROBE_X18_SIGNALS) return 2;
    const struct rlimit limit = {0, 0};
    if (setrlimit(RLIMIT_CORE, &limit) != 0) return 3;
    pear_baseline_packet packet = {.magic = PEAR_BASELINE_MAGIC,
        .version = PEAR_BASELINE_VERSION, .probe = probe, .phase = PEAR_PACKET_COMPLETE};
    /* Resolve both symbols in host mode before any foreign window. The thunks
     * use these addresses directly and never call the dynamic loader there. */
    pear_abi_context context = {
        .getter = (pear_abi_getter)dlsym(RTLD_DEFAULT, "os_custom_x18_abi_enabled"),
        .setter = (pear_abi_setter)dlsym(RTLD_DEFAULT, "os_set_custom_x18_abi_enabled"),
        .sentinel = outer_sentinel,
    };
    if (context.getter == NULL || context.setter == NULL) {
        step(&packet, 0, PEAR_STEP_UNAVAILABLE, PEAR_DOMAIN_INTERNAL, ABI_APIS_UNAVAILABLE, 0);
        return emit_packet(&packet);
    }
    switch (probe) {
        case PEAR_PROBE_X18_ROUNDTRIP: roundtrip_probe(&packet, &context); break;
        case PEAR_PROBE_X18_CALLBACKS: callback_probe(&packet, &context); break;
        case PEAR_PROBE_X18_SIGNALS: signal_probe(&packet, &context); break;
        default: return 2;
    }
    return emit_packet(&packet);
}
