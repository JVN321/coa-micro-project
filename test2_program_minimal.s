.data
arr: .word 5, 10, 15, 20, 25, 30, 35, 40
.text
.globl main
main:
    la t0, arr
    li t1, 0
    li t2, 8
loop:
    lw t3, 0(t0)
    lw t4, 4(t0)
    add t1, t1, t3
    lw t5, 8(t0)
    add t1, t1, t4
    lw t6, 12(t0)
    add t1, t1, t5
    addi t0, t0, 16
    add t1, t1, t6
    addi t2, t2, -1
    bnez t2, loop
end:
    li a7, 10
    ecall
