	.file	"transpose.c"
	.option nopic
	.attribute arch, "rv32i2p0"
	.attribute unaligned_access, 0
	.attribute stack_align, 16
	.text
	.globl	A
	.bss
	.align	2
	.type	A, @object
	.size	A, 3600
A:
	.zero	3600
	.globl	B
	.align	2
	.type	B, @object
	.size	B, 3600
B:
	.zero	3600
	.text
	.align	2
	.globl	transpose
	.type	transpose, @function
transpose:
	addi	sp,sp,-32
	sw	s0,28(sp)
	addi	s0,sp,32
	sw	zero,-20(s0)
	j	.L2
.L5:
	sw	zero,-24(s0)
	j	.L3
.L4:
	lui	a5,%hi(A)
	addi	a3,a5,%lo(A)
	lw	a4,-20(s0)
	mv	a5,a4
	slli	a5,a5,4
	sub	a5,a5,a4
	slli	a5,a5,1
	lw	a4,-24(s0)
	add	a5,a5,a4
	slli	a5,a5,2
	add	a5,a3,a5
	lw	a3,0(a5)
	lui	a5,%hi(B)
	addi	a2,a5,%lo(B)
	lw	a4,-24(s0)
	mv	a5,a4
	slli	a5,a5,4
	sub	a5,a5,a4
	slli	a5,a5,1
	lw	a4,-20(s0)
	add	a5,a5,a4
	slli	a5,a5,2
	add	a5,a2,a5
	sw	a3,0(a5)
	lw	a5,-24(s0)
	addi	a5,a5,1
	sw	a5,-24(s0)
.L3:
	lw	a4,-24(s0)
	li	a5,29
	ble	a4,a5,.L4
	lw	a5,-20(s0)
	addi	a5,a5,1
	sw	a5,-20(s0)
.L2:
	lw	a4,-20(s0)
	li	a5,29
	ble	a4,a5,.L5
	nop
	nop
	lw	s0,28(sp)
	addi	sp,sp,32
	jr	ra
	.size	transpose, .-transpose
	.align	2
	.globl	main
	.type	main, @function
main:
	addi	sp,sp,-16
	sw	ra,12(sp)
	sw	s0,8(sp)
	addi	s0,sp,16
	call	transpose
	li	a5,0
	mv	a0,a5
	lw	ra,12(sp)
	lw	s0,8(sp)
	addi	sp,sp,16
	jr	ra
	.size	main, .-main
	.ident	"GCC: (GNU) 10.1.0"
