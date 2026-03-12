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
	.globl	A
	.bss
	.align	2
A:
	.zero	800
	.globl	B
	.align	2
B:
	.zero	800
	.text
	.align	2
	.globl	compute
compute:
	addi	sp,sp,-32
	sw	s0,28(sp)
	addi	s0,sp,32
	lui	a5,%hi(A)
	addi	a5,a5,%lo(A)
	lw	a4,0(a5)
	lui	a5,%hi(B)
	addi	a5,a5,%lo(B)
	sw	a4,0(a5)
	li	a5,1
	sw	a5,-20(s0)
	j	.L2
.L3:
	lw	a5,-20(s0)
	addi	a5,a5,-1
	lui	a4,%hi(B)
	addi	a4,a4,%lo(B)
	slli	a5,a5,2
	add	a5,a4,a5
	lw	a4,0(a5)
	lui	a5,%hi(A)
	addi	a3,a5,%lo(A)
	lw	a5,-20(s0)
	slli	a5,a5,2
	add	a5,a3,a5
	lw	a5,0(a5)
	add	a4,a4,a5
	lui	a5,%hi(B)
	addi	a3,a5,%lo(B)
	lw	a5,-20(s0)
	slli	a5,a5,2
	add	a5,a3,a5
	sw	a4,0(a5)
	lw	a5,-20(s0)
	addi	a5,a5,1
	sw	a5,-20(s0)
.L2:
	lw	a4,-20(s0)
	li	a5,199
	ble	a4,a5,.L3
	nop
	nop
	lw	s0,28(sp)
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
