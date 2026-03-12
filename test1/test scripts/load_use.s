# load_use.s
# Load-use hazard stress test.
# Every load (lw) is immediately followed by an instruction that consumes
# the loaded value, triggering a pipeline stall each time a naive scheduler
# inserts a bubble between the MEM and EX stages.

.text
.globl main
main:
    # Allocate space on the stack and initialise 8 words.
    addi sp, sp, -32

    addi x5, x0, 10
    sw   x5, 0(sp)          # mem[sp+0]  = 10
    addi x5, x0, 20
    sw   x5, 4(sp)          # mem[sp+4]  = 20
    addi x5, x0, 30
    sw   x5, 8(sp)          # mem[sp+8]  = 30
    addi x5, x0, 40
    sw   x5, 12(sp)         # mem[sp+12] = 40
    addi x5, x0, 50
    sw   x5, 16(sp)         # mem[sp+16] = 50
    addi x5, x0, 60
    sw   x5, 20(sp)         # mem[sp+20] = 60
    addi x5, x0, 70
    sw   x5, 24(sp)         # mem[sp+24] = 70
    addi x5, x0, 80
    sw   x5, 28(sp)         # mem[sp+28] = 80

    # Load-use hazard pairs: each lw is immediately consumed.
    lw   x6,  0(sp)         # LOAD  x6 = 10
    add  x7,  x6,  x0       # USE   RAW on x6  (load-use stall)

    lw   x8,  4(sp)         # LOAD  x8 = 20
    sub  x9,  x8,  x6       # USE   RAW on x8  (load-use stall)

    lw   x10, 8(sp)         # LOAD  x10 = 30
    add  x11, x10, x7       # USE   RAW on x10 (load-use stall)

    lw   x12, 12(sp)        # LOAD  x12 = 40
    sub  x13, x12, x9       # USE   RAW on x12 (load-use stall)

    lw   x14, 16(sp)        # LOAD  x14 = 50
    add  x15, x14, x11      # USE   RAW on x14 (load-use stall)

    lw   x16, 20(sp)        # LOAD  x16 = 60
    sub  x17, x16, x13      # USE   RAW on x16 (load-use stall)

    lw   x18, 24(sp)        # LOAD  x18 = 70
    add  x19, x18, x15      # USE   RAW on x18 (load-use stall)

    lw   x20, 28(sp)        # LOAD  x20 = 80
    sub  x21, x20, x17      # USE   RAW on x20 (load-use stall)

    addi sp, sp, 32         # restore stack pointer

    addi a7, x0, 10         # exit syscall
    ecall
