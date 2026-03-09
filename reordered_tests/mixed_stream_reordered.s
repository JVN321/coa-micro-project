.text
.globl main
main:
    addi x5,  x0,  10
    addi x6,  x0,  20
    addi x7,  x0,  30
    add  x8,  x5,  x6
    addi x9,  x0,  40
    sub  x10, x8,  x7
    addi sp, sp, -16
    addi x5, x0, 100
    sw   x5, 0(sp)
    addi x5, x0, 200
    sw   x5, 4(sp)
    addi x5, x0, 300
    sw   x5, 8(sp)
    lw   x11, 0(sp)
    addi x12, x0,  50
    add  x13, x11, x10
    lw   x14, 4(sp)
    addi x15, x0,  60
    sub  x16, x14, x13
    lw   x17, 8(sp)
    addi x18, x0,  70
    add  x19, x17, x16
    addi x22, x0,  80
    add  x20, x19, x12
    addi x23, x0,  90
    add  x21, x20, x15
    sub  x26, x25, x23
    sub  x24, x21, x18
    addi sp, sp, 16
    add  x25, x24, x22
    addi a7,  x0,  10
    ecall
