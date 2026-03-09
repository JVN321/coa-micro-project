.text
.globl main
main:
    addi sp, sp, -32
    addi x5, x0, 10
    sw   x5, 0(sp)
    addi x5, x0, 20
    sw   x5, 4(sp)
    addi x5, x0, 30
    sw   x5, 8(sp)
    addi x5, x0, 40
    sw   x5, 12(sp)
    addi x5, x0, 50
    sw   x5, 16(sp)
    addi x5, x0, 60
    sw   x5, 20(sp)
    addi x5, x0, 70
    sw   x5, 24(sp)
    addi x5, x0, 80
    sw   x5, 28(sp)
    lw   x6,  0(sp)
    lw   x8,  4(sp)
    add  x7,  x6,  x0
    sub  x9,  x8,  x6
    lw   x10, 8(sp)
    lw   x12, 12(sp)
    add  x11, x10, x7
    sub  x13, x12, x9
    lw   x14, 16(sp)
    lw   x16, 20(sp)
    add  x15, x14, x11
    sub  x17, x16, x13
    lw   x18, 24(sp)
    lw   x20, 28(sp)
    add  x19, x18, x15
    sub  x21, x20, x17
    addi sp, sp, 32
    addi a7, x0, 10
    ecall
