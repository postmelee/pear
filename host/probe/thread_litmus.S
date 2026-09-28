.text
.p2align 2

.globl _pear_litmus_reset
_pear_litmus_reset:
    str wzr, [x0]
    str wzr, [x1]
    dmb ish
    ret

/* No fence or compiler-generated acquire/release operation in the payload. */
.globl _pear_litmus_write
_pear_litmus_write:
    mov w2, #1
    str w2, [x0]
    str w2, [x1]
    ret

.globl _pear_litmus_read
_pear_litmus_read:
    ldr w2, [x1]
    ldr w3, [x0]
    orr x0, x2, x3, lsl #32
    ret
