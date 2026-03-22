	.text
	.globl	_start
_start:
	call	main
	li	a7, 10
	ecall
	.text
	.globl	A
	.text
	.align	2
	.globl	transpose
transpose:
	addi	sp,sp,-32
	sw	s0,28(sp)
	addi	s0,sp,32
	sw	zero,-20(s0)
	j	L2
L5:
	sw	zero,-24(s0)
	j	L3
L4:
	lui	a5,%hi(A)
	lw	a4,-20(s0)
	addi	a3,a5,%lo(A)
	mv	a5,a4
	slli	a5,a5,2
	add	a5,a5,a4
	slli	a5,a5,2
	lw	a4,-24(s0)
	add	a5,a5,a4
	slli	a5,a5,2
	lw	a4,-24(s0)
	add	a5,a3,a5
	lw	a4,-20(s0)
	lw	a3,0(a5)
	lui	a5,%hi(B)
	addi	a2,a5,%lo(B)
	mv	a5,a4
	slli	a5,a5,2
	add	a5,a5,a4
	slli	a5,a5,2
	add	a5,a5,a4
	slli	a5,a5,2
	add	a5,a2,a5
	sw	a3,0(a5)
	lw	a5,-24(s0)
	addi	a5,a5,1
	sw	a5,-24(s0)
L3:
	lw	a4,-24(s0)
	li	a5,19
	ble	a4,a5,L4
	lw	a5,-20(s0)
	addi	a5,a5,1
	sw	a5,-20(s0)
L2:
	lw	a4,-20(s0)
	li	a5,19
	nop
	ble	a4,a5,L5
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
	call	transpose
	li	a5,0
	lw	ra,12(sp)
	mv	a0,a5
	lw	s0,8(sp)
	addi	sp,sp,16
	jr	ra
	.bss
	.align	2
A:
	.zero	1600
	.globl	B
	.align	2
B:
	.zero	1600
