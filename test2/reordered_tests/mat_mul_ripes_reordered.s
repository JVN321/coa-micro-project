	.text
	.globl	A
	.bss
	.align	2
A:
	.zero	36
	.globl	B
	.align	2
B:
	.zero	36
	.globl	C
	.align	2
C:
	.zero	36
	.text
	.align	2
	.globl	init
init:
	addi	sp,sp,-32
	sw	s0,28(sp)
	addi	s0,sp,32
	sw	zero,-20(s0)
	j	.L2
.L5:
	sw	zero,-24(s0)
	j	.L3
.L4:
	lw	a4,-20(s0)
	lw	a5,-24(s0)
	add	a3,a4,a5
	lui	a5,%hi(A)
	lw	a4,-20(s0)
	addi	a2,a5,%lo(A)
	mv	a5,a4
	slli	a5,a5,1
	add	a5,a5,a4
	lw	a4,-24(s0)
	add	a5,a5,a4
	slli	a5,a5,2
	lw	a4,-20(s0)
	add	a5,a2,a5
	sw	a3,0(a5)
	lw	a5,-24(s0)
	sub	a3,a4,a5
	lui	a5,%hi(B)
	lw	a4,-20(s0)
	addi	a2,a5,%lo(B)
	mv	a5,a4
	slli	a5,a5,1
	add	a5,a5,a4
	lw	a4,-24(s0)
	add	a5,a5,a4
	slli	a5,a5,2
	add	a5,a2,a5
	sw	a3,0(a5)
	lw	a5,-24(s0)
	addi	a5,a5,1
	sw	a5,-24(s0)
.L3:
	lw	a4,-24(s0)
	li	a5,2
	ble	a4,a5,.L4
	lw	a5,-20(s0)
	addi	a5,a5,1
	sw	a5,-20(s0)
.L2:
	lw	a4,-20(s0)
	li	a5,2
	nop
	ble	a4,a5,.L5
	nop
	lw	s0,28(sp)
	addi	sp,sp,32
	jr	ra
	.globl	__mulsi3
	.align	2
	.globl	multiply
multiply:
	addi	sp,sp,-32
	sw	ra,28(sp)
	sw	s0,24(sp)
	addi	s0,sp,32
	sw	zero,-20(s0)
	j	.L7
.L12:
	sw	zero,-24(s0)
	j	.L8
.L11:
	sw	zero,-32(s0)
	sw	zero,-28(s0)
	j	.L9
.L10:
	lui	a5,%hi(A)
	lw	a4,-20(s0)
	addi	a3,a5,%lo(A)
	mv	a5,a4
	slli	a5,a5,1
	add	a5,a5,a4
	lw	a4,-28(s0)
	add	a5,a5,a4
	slli	a5,a5,2
	lw	a4,-28(s0)
	add	a5,a3,a5
	lw	a4,-24(s0)
	lw	a2,0(a5)
	lui	a5,%hi(B)
	addi	a3,a5,%lo(B)
	mv	a0,a2
	mv	a5,a4
	slli	a5,a5,1
	add	a5,a5,a4
	add	a5,a5,a4
	slli	a5,a5,2
	add	a5,a3,a5
	lw	a5,0(a5)
	mv	a1,a5
	call	__mulsi3
	mv	a5,a0
	mv	a4,a5
	lw	a5,-32(s0)
	add	a5,a5,a4
	sw	a5,-32(s0)
	lw	a5,-28(s0)
	addi	a5,a5,1
	sw	a5,-28(s0)
.L9:
	lw	a4,-28(s0)
	li	a5,2
	ble	a4,a5,.L10
	lui	a5,%hi(C)
	lw	a4,-20(s0)
	addi	a3,a5,%lo(C)
	mv	a5,a4
	slli	a5,a5,1
	add	a5,a5,a4
	lw	a4,-24(s0)
	add	a5,a5,a4
	slli	a5,a5,2
	lw	a4,-32(s0)
	add	a5,a3,a5
	sw	a4,0(a5)
	lw	a5,-24(s0)
	addi	a5,a5,1
	sw	a5,-24(s0)
.L8:
	lw	a4,-24(s0)
	li	a5,2
	ble	a4,a5,.L11
	lw	a5,-20(s0)
	addi	a5,a5,1
	sw	a5,-20(s0)
.L7:
	lw	a4,-20(s0)
	li	a5,2
	nop
	ble	a4,a5,.L12
	nop
	lw	ra,28(sp)
	lw	s0,24(sp)
	addi	sp,sp,32
	jr	ra
	.align	2
	.globl	main
main:
	addi	sp,sp,-16
	sw	ra,12(sp)
	sw	s0,8(sp)
	addi	s0,sp,16
	call	init
	call	multiply
	li	a5,0
	lw	ra,12(sp)
	mv	a0,a5
	lw	s0,8(sp)
	addi	sp,sp,16
	jr	ra
	.text
__mulsi3:
	mv	t0, a0
	li	a0, 0
__mulsi3_loop:
	andi	t1, a1, 1
	beq	t1, zero, __mulsi3_skip
	add	a0, a0, t0
__mulsi3_skip:
	slli	t0, t0, 1
	srli	a1, a1, 1
	bne	a1, zero, __mulsi3_loop
	jr	ra
