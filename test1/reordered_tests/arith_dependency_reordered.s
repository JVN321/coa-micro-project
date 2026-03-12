.text
.globl main
main:
    addi x5,  x0,  1
    sub  x11, x10, x7
    add  x6,  x5,  x5
    sub  x9,  x8,  x5
    add  x7,  x6,  x5
    add  x10, x9,  x6
    add  x8,  x7,  x6
    add  x14, x13, x10
    add  x12, x11, x8
    sub  x15, x14, x11
    sub  x13, x12, x9
    add  x16, x15, x12
    sub  x19, x18, x15
    sub  x17, x16, x13
    add  x20, x19, x16
    add  x18, x17, x14
    sub  x21, x20, x17
    add  x24, x23, x20
    add  x22, x21, x18
    addi a7,  x0,  10
    sub  x23, x22, x19
    ecall
