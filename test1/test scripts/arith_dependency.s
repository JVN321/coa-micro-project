# arith_dependency.s
# Arithmetic dependency chains – back-to-back RAW (read-after-write) hazards.
# Every instruction depends on the result of the immediately preceding one,
# creating maximum pipeline stalls in a naive 5-stage in-order CPU.

.text
.globl main
main:
    addi x5,  x0,  1        # x5  = 1
    add  x6,  x5,  x5       # x6  = x5 + x5   RAW on x5
    add  x7,  x6,  x5       # x7  = x6 + x5   RAW on x6
    add  x8,  x7,  x6       # x8  = x7 + x6   RAW on x7
    sub  x9,  x8,  x5       # x9  = x8 - x5   RAW on x8
    add  x10, x9,  x6       # x10 = x9 + x6   RAW on x9
    sub  x11, x10, x7       # x11 = x10 - x7  RAW on x10
    add  x12, x11, x8       # x12 = x11 + x8  RAW on x11
    sub  x13, x12, x9       # x13 = x12 - x9  RAW on x12
    add  x14, x13, x10      # x14 = x13 + x10 RAW on x13
    sub  x15, x14, x11      # x15 = x14 - x11 RAW on x14
    add  x16, x15, x12      # x16 = x15 + x12 RAW on x15
    sub  x17, x16, x13      # x17 = x16 - x13 RAW on x16
    add  x18, x17, x14      # x18 = x17 + x14 RAW on x17
    sub  x19, x18, x15      # x19 = x18 - x15 RAW on x18
    add  x20, x19, x16      # x20 = x19 + x16 RAW on x19
    sub  x21, x20, x17      # x21 = x20 - x17 RAW on x20
    add  x22, x21, x18      # x22 = x21 + x18 RAW on x21
    sub  x23, x22, x19      # x23 = x22 - x19 RAW on x22
    add  x24, x23, x20      # x24 = x23 + x20 RAW on x23

    addi a7,  x0,  10       # exit syscall
    ecall
