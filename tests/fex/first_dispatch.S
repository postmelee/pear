/* SPDX-License-Identifier: MIT
 * Original Pear x64 PE fixture. Expected process exit: 42.
 * Integer work runs in the guest before crossing into native ntdll.
 * No CRT, graphics, network, game files or deliberate fault is required.
 */
.text
.globl pear_first_dispatch
pear_first_dispatch:
    subq $40, %rsp
    movl $6, %eax
    imull $7, %eax
    movl %eax, %edx
    movq $-1, %rcx
    callq *__imp_NtTerminateProcess(%rip)
    /* A failed termination is a distinct result, not guest success. */
    movl $71, %eax
    addq $40, %rsp
    retq
