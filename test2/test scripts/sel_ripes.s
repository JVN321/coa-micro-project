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
	.globl	arr
	.bss
	.align	2
arr:
	.zero	200
	.text
	.align	2
	.globl	init
init:
	addi	sp,sp,-32
	sw	s0,28(sp)
	addi	s0,sp,32
	sw	zero,-20(s0)
	j	.L2
.L3:
	li	a4,50
	lw	a5,-20(s0)
	sub	a4,a4,a5
	lui	a5,%hi(arr)
	addi	a3,a5,%lo(arr)
	lw	a5,-20(s0)
	slli	a5,a5,2
	add	a5,a3,a5
	sw	a4,0(a5)
	lw	a5,-20(s0)
	addi	a5,a5,1
	sw	a5,-20(s0)
.L2:
	lw	a4,-20(s0)
	li	a5,49
	ble	a4,a5,.L3
	nop
	nop
	lw	s0,28(sp)
	addi	sp,sp,32
	jr	ra
	.align	2
	.globl	selection_sort
selection_sort:
	addi	sp,sp,-32
	sw	s0,28(sp)
	addi	s0,sp,32
	sw	zero,-20(s0)
	j	.L5
.L9:
	lw	a5,-20(s0)
	sw	a5,-24(s0)
	lw	a5,-20(s0)
	addi	a5,a5,1
	sw	a5,-28(s0)
	j	.L6
.L8:
	lui	a5,%hi(arr)
	addi	a4,a5,%lo(arr)
	lw	a5,-28(s0)
	slli	a5,a5,2
	add	a5,a4,a5
	lw	a4,0(a5)
	lui	a5,%hi(arr)
	addi	a3,a5,%lo(arr)
	lw	a5,-24(s0)
	slli	a5,a5,2
	add	a5,a3,a5
	lw	a5,0(a5)
	bge	a4,a5,.L7
	lw	a5,-28(s0)
	sw	a5,-24(s0)
.L7:
	lw	a5,-28(s0)
	addi	a5,a5,1
	sw	a5,-28(s0)
.L6:
	lw	a4,-28(s0)
	li	a5,49
	ble	a4,a5,.L8
	lui	a5,%hi(arr)
	addi	a4,a5,%lo(arr)
	lw	a5,-20(s0)
	slli	a5,a5,2
	add	a5,a4,a5
	lw	a5,0(a5)
	sw	a5,-32(s0)
	lui	a5,%hi(arr)
	addi	a4,a5,%lo(arr)
	lw	a5,-24(s0)
	slli	a5,a5,2
	add	a5,a4,a5
	lw	a4,0(a5)
	lui	a5,%hi(arr)
	addi	a3,a5,%lo(arr)
	lw	a5,-20(s0)
	slli	a5,a5,2
	add	a5,a3,a5
	sw	a4,0(a5)
	lui	a5,%hi(arr)
	addi	a4,a5,%lo(arr)
	lw	a5,-24(s0)
	slli	a5,a5,2
	add	a5,a4,a5
	lw	a4,-32(s0)
	sw	a4,0(a5)
	lw	a5,-20(s0)
	addi	a5,a5,1
	sw	a5,-20(s0)
.L5:
	lw	a4,-20(s0)
	li	a5,48
	ble	a4,a5,.L9
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
	call	init
	call	selection_sort
	li	a5,0
	mv	a0,a5
	lw	ra,12(sp)
	lw	s0,8(sp)
	addi	sp,sp,16
	jr	ra
