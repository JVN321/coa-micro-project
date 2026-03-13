# -----------------------------------------------------------------------
# _start: Ripes entry point — calls main, then exits via ecall
# -----------------------------------------------------------------------
	.text
	.globl	_start
_start:
	call	main
	li	a7, 10		# Ripes exit ecall (terminate simulation)
	ecall


	.text
	.globl	input
	.bss
	.align	2
input:
	.zero	400
	.globl	kernel
	.data
	.align	2
kernel:
	.word	1
	.word	2
	.word	1
	.globl	output
	.bss
	.align	2
output:
	.zero	400
	.text
	.align	2
	.globl	compute
compute:
	addi	sp,sp,-32
	sw	ra,28(sp)
	sw	s0,24(sp)
	sw	s1,20(sp)
	addi	s0,sp,32
	li	a5,1
	sw	a5,-20(s0)
	j	L2
L3:
	lw	a5,-20(s0)
	addi	a5,a5,-1
	lui	a4,%hi(input)
	addi	a4,a4,%lo(input)
	slli	a5,a5,2
	add	a5,a4,a5
	lw	a4,0(a5)
	lui	a5,%hi(kernel)
	addi	a5,a5,%lo(kernel)
	lw	a5,0(a5)
	mv	a1,a5
	mv	a0,a4
	call	__mulsi3
	mv	a5,a0
	mv	s1,a5
	lui	a5,%hi(input)
	addi	a4,a5,%lo(input)
	lw	a5,-20(s0)
	slli	a5,a5,2
	add	a5,a4,a5
	lw	a4,0(a5)
	lui	a5,%hi(kernel)
	addi	a5,a5,%lo(kernel)
	lw	a5,4(a5)
	mv	a1,a5
	mv	a0,a4
	call	__mulsi3
	mv	a5,a0
	add	s1,s1,a5
	lw	a5,-20(s0)
	addi	a5,a5,1
	lui	a4,%hi(input)
	addi	a4,a4,%lo(input)
	slli	a5,a5,2
	add	a5,a4,a5
	lw	a4,0(a5)
	lui	a5,%hi(kernel)
	addi	a5,a5,%lo(kernel)
	lw	a5,8(a5)
	mv	a1,a5
	mv	a0,a4
	call	__mulsi3
	mv	a5,a0
	add	a4,s1,a5
	lui	a5,%hi(output)
	addi	a3,a5,%lo(output)
	lw	a5,-20(s0)
	slli	a5,a5,2
	add	a5,a3,a5
	sw	a4,0(a5)
	lw	a5,-20(s0)
	addi	a5,a5,1
	sw	a5,-20(s0)
L2:
	lw	a4,-20(s0)
	li	a5,98
	ble	a4,a5,L3
	nop
	nop
	lw	ra,28(sp)
	lw	s0,24(sp)
	lw	s1,20(sp)
	addi	sp,sp,32
	jr	ra
	.align	2
	.globl	main
main:
	addi	sp,sp,-16
	sw	ra,12(sp)
	sw	s0,8(sp)
	addi	s0,sp,16
	call	compute
	li	a5,0
	mv	a0,a5
	lw	ra,12(sp)
	lw	s0,8(sp)
	addi	sp,sp,16
	jr	ra
	.globl	__mulsi3

	.text
# -----------------------------------------------------------------------
# __mulsi3: software 32-bit multiply (rv32i, shift-and-add)
# a0 = a0 * a1   clobbers: t0, t1
# -----------------------------------------------------------------------
__mulsi3:
	mv	t0, a0		# t0 = multiplicand
	li	a0, 0		# a0 = accumulator (result)
__mulsi3_loop:
	andi	t1, a1, 1	# test LSB of multiplier
	beq	t1, zero, __mulsi3_skip
	add	a0, a0, t0	# accumulate
__mulsi3_skip:
	slli	t0, t0, 1	# multiplicand <<= 1
	srli	a1, a1, 1	# multiplier >>= 1  (logical shift: handles sign via wrap)
	bne	a1, zero, __mulsi3_loop
	jr	ra
