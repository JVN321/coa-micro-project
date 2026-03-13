	.file	"mat_mul.c"
	.option nopic
	.attribute arch, "rv32i2p1"
	.attribute unaligned_access, 0
	.attribute stack_align, 16
	.text
	.globl	A
	.bss
	.align	2
	.type	A, @object
	.size	A, 36
A:
	.zero	36
	.globl	B
	.align	2
	.type	B, @object
	.size	B, 36
B:
	.zero	36
	.globl	C
	.align	2
	.type	C, @object
	.size	C, 36
C:
	.zero	36
	.text
	.align	2
	.globl	init
	.type	init, @function
init:
	addi	sp,sp,-32
	sw	ra,28(sp)
	sw	s0,24(sp)
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
	addi	a2,a5,%lo(A)
	lw	a4,-20(s0)
	mv	a5,a4
	slli	a5,a5,1
	add	a5,a5,a4
	lw	a4,-24(s0)
	add	a5,a5,a4
	slli	a5,a5,2
	add	a5,a2,a5
	sw	a3,0(a5)
	lw	a4,-20(s0)
	lw	a5,-24(s0)
	sub	a3,a4,a5
	lui	a5,%hi(B)
	addi	a2,a5,%lo(B)
	lw	a4,-20(s0)
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
	ble	a4,a5,.L5
	nop
	nop
	lw	ra,28(sp)
	lw	s0,24(sp)
	addi	sp,sp,32
	jr	ra
	.size	init, .-init
	.align	2
	.globl	multiply
	.type	multiply, @function
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
	addi	a3,a5,%lo(A)
	lw	a4,-20(s0)
	mv	a5,a4
	slli	a5,a5,1
	add	a5,a5,a4
	lw	a4,-28(s0)
	add	a5,a5,a4
	slli	a5,a5,2
	add	a5,a3,a5
	lw	a2,0(a5)
	lui	a5,%hi(B)
	addi	a3,a5,%lo(B)
	lw	a4,-28(s0)
	mv	a5,a4
	slli	a5,a5,1
	add	a5,a5,a4
	lw	a4,-24(s0)
	add	a5,a5,a4
	slli	a5,a5,2
	add	a5,a3,a5
	lw	a5,0(a5)
	mv	a1,a5
	mv	a0,a2
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
	addi	a3,a5,%lo(C)
	lw	a4,-20(s0)
	mv	a5,a4
	slli	a5,a5,1
	add	a5,a5,a4
	lw	a4,-24(s0)
	add	a5,a5,a4
	slli	a5,a5,2
	add	a5,a3,a5
	lw	a4,-32(s0)
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
	ble	a4,a5,.L12
	nop
	nop
	lw	ra,28(sp)
	lw	s0,24(sp)
	addi	sp,sp,32
	jr	ra
	.size	multiply, .-multiply
	.align	2
	.globl	main
	.type	main, @function
main:
	addi	sp,sp,-16
	sw	ra,12(sp)
	sw	s0,8(sp)
	addi	s0,sp,16
	call	init
	call	multiply
	li	a5,0
	mv	a0,a5
	lw	ra,12(sp)
	lw	s0,8(sp)
	addi	sp,sp,16
	jr	ra
	.size	main, .-main
	.globl	__mulsi3
	.ident	"GCC: (Arch User Repository) 14.2.0"
	.section	.note.GNU-stack,"",@progbits
