import random

N = 500   # number of instruction blocks

regs = ["t0","t1","t2","t3","t4","t5","t6"]

print(".data")
print("arr: .word 1,2,3,4,5,6,7,8")

print(".text")
print(".globl main")
print("main:")

for i in range(N):

    r1 = random.choice(regs)
    r2 = random.choice(regs)
    r3 = random.choice(regs)

    print(f"    add {r1},{r2},{r3}")
    print(f"    add {r2},{r1},{r3}")
    print(f"    sub {r3},{r1},{r2}")

    print(f"    lw {r1},0(sp)")
    print(f"    add {r2},{r1},{r3}")

print("    nop")