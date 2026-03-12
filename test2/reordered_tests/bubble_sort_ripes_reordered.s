	.text
	.globl	_start
_start:
	call	main
	li	a7, 10
	ecall
	.text
	.globl	arr
	.bss
	.align	2
arr:
	.zero	400
	.text
	.align	2
	.globl	bubble_sort
bubble_sort:
	addi	sp,sp,-48
	sw	s0,44(sp)
	addi	s0,sp,48
	sw	a0,-36(s0)
	sw	zero,-20(s0)
	j	.L2
.L6:
	sw	zero,-24(s0)
	j	.L3
.L5:
	lui	a5,%hi(arr)
	lui	a3,%hi(arr)
	addi	a4,a5,%lo(arr)
	addi	a3,a3,%lo(arr)
	lw	a5,-24(s0)
	slli	a5,a5,2
	add	a5,a4,a5
	lw	a4,0(a5)
	lw	a5,-24(s0)
	addi	a5,a5,1
	slli	a5,a5,2
	add	a5,a3,a5
	lw	a5,0(a5)
	ble	a4,a5,.L4
	lui	a5,%hi(arr)
	addi	a4,a5,%lo(arr)
	lw	a5,-24(s0)
	lui	a4,%hi(arr)
	slli	a5,a5,2
	add	a5,a4,a5
	lw	a5,0(a5)
	sw	a5,-28(s0)
	lw	a5,-24(s0)
	addi	a4,a4,%lo(arr)
	addi	a5,a5,1
	slli	a5,a5,2
	add	a5,a4,a5
	lw	a4,0(a5)
	lui	a5,%hi(arr)
	lui	a4,%hi(arr)
	addi	a3,a5,%lo(arr)
	addi	a4,a4,%lo(arr)
	lw	a5,-24(s0)
	lw	a4,-28(s0)
	slli	a5,a5,2
	add	a5,a3,a5
	sw	a4,0(a5)
	lw	a5,-24(s0)
	addi	a5,a5,1
	slli	a5,a5,2
	add	a5,a4,a5
	sw	a4,0(a5)
.L4:
	lw	a5,-24(s0)
	addi	a5,a5,1
	sw	a5,-24(s0)
.L3:
	lw	a4,-36(s0)
	lw	a5,-20(s0)
	sub	a5,a4,a5
	addi	a5,a5,-1
	lw	a4,-24(s0)
	blt	a4,a5,.L5
	lw	a5,-20(s0)
	addi	a5,a5,1
	sw	a5,-20(s0)
.L2:
	lw	a5,-36(s0)
	lw	a4,-20(s0)
	addi	a5,a5,-1
	blt	a4,a5,.L6
	nop
	nop
	lw	s0,44(sp)
	addi	sp,sp,48
	jr	ra
	.align	2
	.globl	main
main:
	addi	sp,sp,-16
	sw	ra,12(sp)
	sw	s0,8(sp)
	addi	s0,sp,16
	li	a0,100
	call	bubble_sort
	li	a5,0
	lw	ra,12(sp)
	mv	a0,a5
	lw	s0,8(sp)
	addi	sp,sp,16
	jr	ra
