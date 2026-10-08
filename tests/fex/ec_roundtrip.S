/* SPDX-License-Identifier: MIT
 * Original Pear x64 fixture: guest -> native NT API -> guest, twice.
 * Verify stack and representative nonvolatile integer/SIMD state before 42.
 * No CRT, game content, network or deliberate fault is required.
 */
.text
.globl pear_first_dispatch
pear_first_dispatch:
    subq $136, %rsp
    movq %rsp, %rbp
    movabsq $0x1122334455667788, %rbx
    movabsq $0x2233445566778899, %r12
    movabsq $0x33445566778899aa, %r15
    movq %rbx, %xmm6
    movq %r15, %xmm15
    movl $2, 64(%rsp)
roundtrip:
    leaq 32(%rsp), %rcx
    leaq 40(%rsp), %rdx
    callq *__imp_NtQueryPerformanceCounter(%rip)
    testl %eax, %eax
    jne fail_status
    cmpq %rsp, %rbp
    jne fail_state
    cmpq $0, 40(%rsp)
    jle fail_result
    movabsq $0x1122334455667788, %rax
    cmpq %rax, %rbx
    jne fail_state
    movq %xmm6, %rcx
    cmpq %rax, %rcx
    jne fail_state
    movabsq $0x2233445566778899, %rax
    cmpq %rax, %r12
    jne fail_state
    movabsq $0x33445566778899aa, %rax
    cmpq %rax, %r15
    jne fail_state
    movq %xmm15, %rcx
    cmpq %rax, %rcx
    jne fail_state
    subl $1, 64(%rsp)
    jnz roundtrip
    movl $6, %eax
    imull $7, %eax
    movl %eax, %edx
    jmp terminate
fail_status:
    movl $72, %edx
    jmp terminate
fail_state:
    movl $73, %edx
    jmp terminate
fail_result:
    movl $74, %edx
terminate:
    movq $-1, %rcx
    callq *__imp_NtTerminateProcess(%rip)
    movl $71, %eax
    addq $136, %rsp
    retq
