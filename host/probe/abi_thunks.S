#include "abi.h"

#if !defined(__arm64__)
#error "The foreign ABI thunks require ARM64."
#endif

.text
.p2align 2

/* Every BLR in a foreign window targets an API address resolved in host mode.
 * Host callbacks are reachable only after the getter confirms host mode. */
.macro ENTER_FRAME
    stp x29, x30, [sp, #-96]!
    mov x29, sp
    stp x19, x20, [sp, #16]
    stp x21, x22, [sp, #32]
    stp x23, x24, [sp, #48]
    stp x25, x26, [sp, #64]
.endm
.macro LEAVE_FRAME
    ldp x25, x26, [sp, #64]
    ldp x23, x24, [sp, #48]
    ldp x21, x22, [sp, #32]
    ldp x19, x20, [sp, #16]
    ldp x29, x30, [sp], #96
    ret
.endm

.globl _pear_abi_roundtrip_thunk
.private_extern _pear_abi_roundtrip_thunk
_pear_abi_roundtrip_thunk:
    ENTER_FRAME
    mov x19, x0
    ldr x20, [x19, #ABI_GETTER]
    ldr x21, [x19, #ABI_SETTER]
    blr x20
    and w0, w0, #1
    str x0, [x19, #ABI_HOST_ENTRY]
    cbnz w0, Lround_fail
    mov w0, #1
    blr x21
    blr x20
    and w0, w0, #1
    str x0, [x19, #ABI_FOREIGN_ENTRY]
    cbz w0, Lround_fail
    ldr x22, [x19, #ABI_SENTINEL]
    mov x18, x22
    str x18, [x19, #ABI_GUEST_BEFORE]
    blr x20
    and w0, w0, #1
    cbz w0, Lround_fail
    str x18, [x19, #ABI_GUEST_AFTER]
    cmp x18, x22
    b.ne Lround_fail
    mov w0, #0
    blr x21
    blr x20
    and w0, w0, #1
    str x0, [x19, #ABI_HOST_EXIT]
    cbnz w0, Lround_fail
    ldr x0, [x19, #ABI_COMPLETED]
    add x0, x0, #1
    str x0, [x19, #ABI_COMPLETED]
    mov w0, #0
    LEAVE_FRAME
Lround_fail:
    mov x0, #1
    str x0, [x19, #ABI_FAILURE]
    blr x20
    and w0, w0, #1
    cbz w0, Lround_failed_host
    mov w0, #0
    blr x21
    blr x20
    and w0, w0, #1
    cbnz w0, Labi_contract_trap
Lround_failed_host:
    mov w0, #1
    LEAVE_FRAME

.globl _pear_abi_callback_thunk
.private_extern _pear_abi_callback_thunk
_pear_abi_callback_thunk:
    ENTER_FRAME
    mov x19, x0
    mov w23, w1
    ldr x20, [x19, #ABI_GETTER]
    ldr x21, [x19, #ABI_SETTER]
    blr x20
    and w0, w0, #1
    str x0, [x19, #ABI_HOST_ENTRY]
    cbnz w0, Lcallback_fail
    mov w0, #1
    blr x21
    blr x20
    and w0, w0, #1
    cbz w0, Lcallback_fail
    ldr x18, [x19, #ABI_SENTINEL]
    mov x22, x18
    mov w0, #0
    blr x21
    blr x20
    and w0, w0, #1
    cbnz w0, Lcallback_fail
    mov x0, x19
    mov w1, w23
    ldr x24, [x19, #ABI_CALLBACK]
    blr x24
    mov w25, w0
    blr x20
    and w0, w0, #1
    cbnz w0, Lcallback_fail
    mov w0, #1
    blr x21
    blr x20
    and w0, w0, #1
    cbz w0, Lcallback_fail
    mov x18, x22
    blr x20
    and w0, w0, #1
    cbz w0, Lcallback_fail
    cmp x18, x22
    b.ne Lcallback_fail
    ldr x0, [x19, #ABI_RESTORES]
    add x0, x0, #1
    str x0, [x19, #ABI_RESTORES]
    mov w0, #0
    blr x21
    blr x20
    and w0, w0, #1
    str x0, [x19, #ABI_HOST_EXIT]
    cbnz w0, Lcallback_fail
    mov w0, w25
    LEAVE_FRAME
Lcallback_fail:
    mov x0, #1
    str x0, [x19, #ABI_FAILURE]
    blr x20
    and w0, w0, #1
    cbz w0, Lcallback_failed_host
    mov w0, #0
    blr x21
    blr x20
    and w0, w0, #1
    cbnz w0, Labi_contract_trap
Lcallback_failed_host:
    mov w0, #99
    LEAVE_FRAME

.globl _pear_abi_signal_wait_thunk
.private_extern _pear_abi_signal_wait_thunk
_pear_abi_signal_wait_thunk:
    ENTER_FRAME
    mov x19, x0
    ldr x20, [x19, #SIG_GETTER]
    ldr x21, [x19, #SIG_SETTER]
    blr x20
    and w0, w0, #1
    cbnz w0, Lwait_fail
    mov w0, #1
    blr x21
    blr x20
    and w0, w0, #1
    cbz w0, Lwait_fail
    ldr x22, [x19, #SIG_GUEST]
    mov x18, x22
    /* Release/acquire handshake with the host-mode sender thread. No syscall,
     * scheduler helper or compiler-generated routine runs in this window. */
    add x24, x19, #SIG_READY
    mov w0, #1
    stlr w0, [x24]
    add x24, x19, #SIG_DONE
    mov w23, #0xca00
    movk w23, #0x3b9a, lsl #16
Lsignal_spin:
    ldar w0, [x24]
    cbnz w0, Lsignal_resumed
    subs w23, w23, #1
    b.ne Lsignal_spin
    b Lwait_fail
Lsignal_resumed:
    blr x20
    and w0, w0, #1
    cbz w0, Lwait_fail
    cmp x18, x22
    b.ne Lwait_fail
    mov x0, #1
    str x0, [x19, #SIG_RESUMED]
    mov w0, #0
    blr x21
    blr x20
    and w0, w0, #1
    str x0, [x19, #SIG_HOST_EXIT]
    cbnz w0, Lwait_fail
    mov w0, #0
    LEAVE_FRAME
Lwait_fail:
    mov x0, #1
    str x0, [x19, #SIG_FAILURE]
    blr x20
    and w0, w0, #1
    cbz w0, Lwait_failed_host
    mov w0, #0
    blr x21
    blr x20
    and w0, w0, #1
    cbnz w0, Labi_contract_trap
Lwait_failed_host:
    mov w0, #1
    LEAVE_FRAME

.globl _pear_abi_signal_gateway
.private_extern _pear_abi_signal_gateway
_pear_abi_signal_gateway:
    ENTER_FRAME
    mov w22, w0
    mov x23, x2
    adrp x19, _pear_abi_active_signal@PAGE
    add x19, x19, _pear_abi_active_signal@PAGEOFF
    ldar x19, [x19]
    ldr x20, [x19, #SIG_GETTER]
    ldr x21, [x19, #SIG_SETTER]
    blr x20
    and w25, w0, #1
    cbz w25, Lhandler_host
    mov x26, x18
    mov w0, #0
    blr x21
Lhandler_host:
    blr x20
    and w0, w0, #1
    cbnz w0, Lhandler_fail
    ldr x24, [x19, #SIG_BODY]
    mov x0, x19
    mov w1, w22
    mov x2, x23
    mov w3, w25
    blr x24
    blr x20
    and w0, w0, #1
    cbnz w0, Lhandler_fail
    cbz w25, Lhandler_done
    mov w0, #1
    blr x21
    blr x20
    and w0, w0, #1
    cbz w0, Lhandler_fail
    mov x18, x26
Lhandler_done:
    add x24, x19, #SIG_DONE
    mov w0, #1
    stlr w0, [x24]
    LEAVE_FRAME
Lhandler_fail:
    mov x0, #1
    str x0, [x19, #SIG_FAILURE]
    /* A violated setter contract cannot safely enter a C handler body. Restore
     * host mode before an intentional failing trap in this disposable child. */
    blr x20
    and w0, w0, #1
    cbz w0, Lhandler_failed_host
    mov w0, #0
    blr x21
Lhandler_failed_host:
Labi_contract_trap:
    /* No C return is safe when a mode transition violates its contract. */
    brk #0x504
