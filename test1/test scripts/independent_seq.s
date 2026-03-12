# independent_seq.s
# Fully independent instruction sequences – no data hazards.
# Each instruction reads/writes a distinct register, so a scheduler
# cannot improve this further.  Serves as a baseline / control case.

.text
.globl main
main:
    addi x5,  x0, 1         # x5  = 1   (independent)
    addi x6,  x0, 2         # x6  = 2   (independent)
    addi x7,  x0, 3         # x7  = 3   (independent)
    addi x8,  x0, 4         # x8  = 4   (independent)
    addi x9,  x0, 5         # x9  = 5   (independent)
    addi x10, x0, 6         # x10 = 6   (independent)
    addi x11, x0, 7         # x11 = 7   (independent)
    addi x12, x0, 8         # x12 = 8   (independent)
    addi x13, x0, 9         # x13 = 9   (independent)
    addi x14, x0, 10        # x14 = 10  (independent)
    addi x15, x0, 11        # x15 = 11  (independent)
    addi x16, x0, 12        # x16 = 12  (independent)
    addi x17, x0, 13        # x17 = 13  (independent)
    addi x18, x0, 14        # x18 = 14  (independent)
    addi x19, x0, 15        # x19 = 15  (independent)
    addi x20, x0, 16        # x20 = 16  (independent)
    addi x21, x0, 17        # x21 = 17  (independent)
    addi x22, x0, 18        # x22 = 18  (independent)
    addi x23, x0, 19        # x23 = 19  (independent)
    addi x24, x0, 20        # x24 = 20  (independent)

    addi a7,  x0, 10        # exit syscall
    ecall
