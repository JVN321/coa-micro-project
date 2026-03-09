# mixed_stream.s
# Mixed instruction stream – alternating hazardous and independent instructions.
# Independent instructions provide scheduling opportunities: a smart reorderer
# can sink them into the stall slots to hide latency.

.text
.globl main
main:
    # ── Cluster 1: RAW chain with independent instructions interspersed ──
    addi x5,  x0,  10       # x5  = 10  (independent init)
    addi x6,  x0,  20       # x6  = 20  (independent)
    addi x7,  x0,  30       # x7  = 30  (independent)
    add  x8,  x5,  x6       # x8  = x5 + x6   RAW on x5, x6
    addi x9,  x0,  40       # x9  = 40  (independent – can fill hazard slot)
    sub  x10, x8,  x7       # x10 = x8 - x7   RAW on x8

    # ── Cluster 2: load-use hazard with nearby independent instructions ──
    addi sp, sp, -16
    addi x5, x0, 100
    sw   x5, 0(sp)          # store 100
    addi x5, x0, 200
    sw   x5, 4(sp)          # store 200
    addi x5, x0, 300
    sw   x5, 8(sp)          # store 300

    lw   x11, 0(sp)         # LOAD  x11 = 100
    addi x12, x0,  50       # x12 = 50  (independent – can fill load-use slot)
    add  x13, x11, x10      # USE   RAW on x11 (load-use stall if not filled)

    lw   x14, 4(sp)         # LOAD  x14 = 200
    addi x15, x0,  60       # x15 = 60  (independent)
    sub  x16, x14, x13      # USE   RAW on x14

    lw   x17, 8(sp)         # LOAD  x17 = 300
    addi x18, x0,  70       # x18 = 70  (independent)
    add  x19, x17, x16      # USE   RAW on x17

    # ── Cluster 3: RAW chain followed by independent work ──
    add  x20, x19, x12      # x20 = x19 + x12  RAW on x19
    add  x21, x20, x15      # x21 = x20 + x15  RAW on x20
    addi x22, x0,  80       # independent
    addi x23, x0,  90       # independent
    sub  x24, x21, x18      # x24 = x21 - x18  RAW on x21
    add  x25, x24, x22      # x25 = x24 + x22  RAW on x24
    sub  x26, x25, x23      # x26 = x25 - x23  RAW on x25

    addi sp, sp, 16         # restore stack pointer

    addi a7,  x0,  10       # exit syscall
    ecall
