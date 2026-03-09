# test_program.s
# Sample RISC-V assembly with deliberate hazards to test instruction reordering.
# Annotated with expected hazards so results can be verified by inspection.

.text
.global main

main:
    # -----------------------------------------------------------------------
    # Example 1: Load-use hazard
    # lw loads into t0, then the very next instruction uses t0 (RAW stall).
    # An independent add (a1 + a2) should be moved between them.
    # -----------------------------------------------------------------------
    lw      t0, 0(a0)        # load from memory into t0
    add     t1, t0, t2       # RAW hazard: reads t0 immediately after load
    add     a1, a2, a3       # independent: no dependency on t0

    # -----------------------------------------------------------------------
    # Example 2: Back-to-back ALU dependency
    # add writes t3, and the next instruction immediately reads t3.
    # The sub below is independent and should be moved between them.
    # -----------------------------------------------------------------------
    add     t3, a0, a1       # writes t3
    mul     t4, t3, a2       # RAW hazard: reads t3
    sub     a4, a5, a6       # independent

    # -----------------------------------------------------------------------
    # Example 3: Load followed by store using the loaded value
    # lw writes t5; sw to a different address reads t5 (RAW stall).
    # The addi below is independent and should slip between them.
    # -----------------------------------------------------------------------
    lw      t5, 4(a0)        # load into t5
    sw      t5, 8(a1)        # RAW hazard: reads t5 right after load
    addi    a7, a7, 1        # independent counter increment

    # -----------------------------------------------------------------------
    # Example 4: No hazard — reordering should leave these alone
    # -----------------------------------------------------------------------
    addi    s0, zero, 10     # writes s0
    addi    s1, zero, 20     # writes s1, independent of s0
    add     s2, s0, s1       # reads s0 and s1 (both available, no stall)

    # -----------------------------------------------------------------------
    # Example 5: Multiple sequential load-use pairs
    # -----------------------------------------------------------------------
    lw      t0, 0(sp)        # load 1
    add     a0, t0, zero     # RAW on t0
    lw      t1, 4(sp)        # load 2  — independent of above pair
    add     a1, t1, zero     # RAW on t1

    # -----------------------------------------------------------------------
    # Control flow barrier — reordering must not cross this boundary
    # -----------------------------------------------------------------------
    beq     s0, s1, end

loop:
    # -----------------------------------------------------------------------
    # Example 6: Loop body with a load-use hazard
    # -----------------------------------------------------------------------
    lw      t2, 0(a0)        # load element
    addi    a0, a0, 4        # advance pointer (independent of t2)
    add     t3, t2, t3       # accumulate — RAW on t2, but addi above can fill stall

    addi    s0, s0, -1       # decrement counter
    bne     s0, zero, loop   # loop-back branch (barrier)

end:
    # Return value already in a0
    ret
