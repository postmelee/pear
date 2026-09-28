#ifndef PEAR_ABI_H
#define PEAR_ABI_H

/* Fixed offsets shared with the hand-written, same-build ARM64 thunks. */
#define ABI_GETTER 0
#define ABI_SETTER 8
#define ABI_CALLBACK 16
#define ABI_SENTINEL 24
#define ABI_HOST_ENTRY 32
#define ABI_FOREIGN_ENTRY 40
#define ABI_GUEST_BEFORE 48
#define ABI_GUEST_AFTER 56
#define ABI_HOST_EXIT 64
#define ABI_COMPLETED 72
#define ABI_CALLBACKS 80
#define ABI_NESTED 88
#define ABI_RESTORES 96
#define ABI_ERRORS 104
#define ABI_FAILURE 112

#define SIG_GETTER 0
#define SIG_SETTER 8
#define SIG_BODY 16
#define SIG_GUEST 24
#define SIG_HOST_ENTRY 32
#define SIG_FOREIGN_ENTRY 40
#define SIG_BODY_CALLS 48
#define SIG_FAILURE 56
#define SIG_READY 64
#define SIG_DONE 68
#define SIG_RESUMED 72
#define SIG_HOST_EXIT 80
#define SIG_EXPECT_FOREIGN 88

#ifndef __ASSEMBLER__
#include "baseline.h"
#include <signal.h>
#include <stdatomic.h>
#include <sys/types.h>

typedef bool (*pear_abi_getter)(void);
typedef void (*pear_abi_setter)(bool);

typedef struct pear_abi_context {
    pear_abi_getter getter;
    pear_abi_setter setter;
    int (*callback)(struct pear_abi_context *, int);
    uint64_t sentinel;
    uint64_t host_entry, foreign_entry, guest_before, guest_after, host_exit;
    uint64_t completed, callbacks, nested, restores, errors, failure;
} pear_abi_context;

typedef struct pear_abi_signal_state {
    pear_abi_getter getter;
    pear_abi_setter setter;
    void (*body)(struct pear_abi_signal_state *, int, void *, int);
    uint64_t guest;
    _Atomic uint64_t host_entry, foreign_entry, body_calls, failure;
    _Atomic uint32_t ready, done;
    uint64_t resumed, host_exit;
    _Atomic uint64_t expect_foreign;
    int write_fd;
    int *errno_location;
    ssize_t (*writer)(int, const void *, size_t);
} pear_abi_signal_state;

#define ABI_ASSERT(type, field, offset) \
    _Static_assert(offsetof(type, field) == (offset), "Assembly offset mismatch: " #field)
ABI_ASSERT(pear_abi_context, getter, ABI_GETTER);
ABI_ASSERT(pear_abi_context, setter, ABI_SETTER);
ABI_ASSERT(pear_abi_context, callback, ABI_CALLBACK);
ABI_ASSERT(pear_abi_context, sentinel, ABI_SENTINEL);
ABI_ASSERT(pear_abi_context, host_entry, ABI_HOST_ENTRY);
ABI_ASSERT(pear_abi_context, foreign_entry, ABI_FOREIGN_ENTRY);
ABI_ASSERT(pear_abi_context, guest_before, ABI_GUEST_BEFORE);
ABI_ASSERT(pear_abi_context, guest_after, ABI_GUEST_AFTER);
ABI_ASSERT(pear_abi_context, host_exit, ABI_HOST_EXIT);
ABI_ASSERT(pear_abi_context, completed, ABI_COMPLETED);
ABI_ASSERT(pear_abi_context, callbacks, ABI_CALLBACKS);
ABI_ASSERT(pear_abi_context, nested, ABI_NESTED);
ABI_ASSERT(pear_abi_context, restores, ABI_RESTORES);
ABI_ASSERT(pear_abi_context, errors, ABI_ERRORS);
ABI_ASSERT(pear_abi_context, failure, ABI_FAILURE);
ABI_ASSERT(pear_abi_signal_state, getter, SIG_GETTER);
ABI_ASSERT(pear_abi_signal_state, setter, SIG_SETTER);
ABI_ASSERT(pear_abi_signal_state, body, SIG_BODY);
ABI_ASSERT(pear_abi_signal_state, guest, SIG_GUEST);
ABI_ASSERT(pear_abi_signal_state, host_entry, SIG_HOST_ENTRY);
ABI_ASSERT(pear_abi_signal_state, foreign_entry, SIG_FOREIGN_ENTRY);
ABI_ASSERT(pear_abi_signal_state, body_calls, SIG_BODY_CALLS);
ABI_ASSERT(pear_abi_signal_state, failure, SIG_FAILURE);
ABI_ASSERT(pear_abi_signal_state, ready, SIG_READY);
ABI_ASSERT(pear_abi_signal_state, done, SIG_DONE);
ABI_ASSERT(pear_abi_signal_state, resumed, SIG_RESUMED);
ABI_ASSERT(pear_abi_signal_state, host_exit, SIG_HOST_EXIT);
ABI_ASSERT(pear_abi_signal_state, expect_foreign, SIG_EXPECT_FOREIGN);
_Static_assert(ATOMIC_INT_LOCK_FREE == 2, "Signal handshake requires lock-free integers");
_Static_assert(ATOMIC_LONG_LOCK_FREE == 2 && ATOMIC_LLONG_LOCK_FREE == 2,
               "Signal observations require lock-free 64-bit values");
_Static_assert(ATOMIC_POINTER_LOCK_FREE == 2, "Signal publication requires lock-free pointers");
#undef ABI_ASSERT

extern _Atomic(pear_abi_signal_state *) pear_abi_active_signal;
int pear_abi_roundtrip_thunk(pear_abi_context *context);
int pear_abi_callback_thunk(pear_abi_context *context, int inject_error);
int pear_abi_signal_wait_thunk(pear_abi_signal_state *state);
void pear_abi_signal_gateway(int number, siginfo_t *info, void *ucontext);
int pear_abi_child_main(pear_probe_id probe);
#endif

#endif
