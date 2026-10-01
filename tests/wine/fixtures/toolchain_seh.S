/* Original Pear assembler fixture. Compile and inspect; do not execute.
 * Wine configure.ac requires SEH directives for non-i386 PE targets.
 * i386 below is only an assembler/machine-type control, not an SEH test.
 */
#if !defined(_WIN32)
#error This fixture requires a Windows PE target.
#endif

.text
#if defined(__aarch64__) || defined(__arm64ec__) || defined(_M_ARM64) || defined(_M_ARM64EC)
.p2align 2
.globl pear_toolchain_seh
.def pear_toolchain_seh; .scl 2; .type 32; .endef
.seh_proc pear_toolchain_seh
pear_toolchain_seh:
    sub sp, sp, #16
    .seh_stackalloc 16
    .seh_endprologue
    mov w0, #42
    .seh_startepilogue
    add sp, sp, #16
    .seh_stackalloc 16
    .seh_endepilogue
    ret
.seh_endproc
#elif defined(__x86_64__) || defined(_M_X64)
.p2align 4
.globl pear_toolchain_seh
.def pear_toolchain_seh; .scl 2; .type 32; .endef
.seh_proc pear_toolchain_seh
pear_toolchain_seh:
    subq $40, %rsp
    .seh_stackalloc 40
    .seh_endprologue
    movl $42, %eax
    addq $40, %rsp
    ret
.seh_endproc
#elif defined(__i386__) || defined(_M_IX86)
.p2align 2
.globl _pear_toolchain_seh
.def _pear_toolchain_seh; .scl 2; .type 32; .endef
_pear_toolchain_seh:
    movl $42, %eax
    ret
#else
#error Unsupported PE architecture for this fixture.
#endif
