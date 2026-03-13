	.text
	.globl	_start
_start:
	call	main
	li	a7, 10
	ecall
	.text
	.globl	fib
	.bss
	.align	2
fib:
	.zero	400
	.text
	.align	2
	.globl	compute
compute:
	addi	sp,sp,-32
	sw	ra,28(sp)
	sw	s0,24(sp)
	addi	s0,sp,32
	lui	a5,%hi(fib)
	li	a4,1
	addi	a5,a5,%lo(fib)
	sw	zero,0(a5)
	lui	a5,%hi(fib)
	addi	a5,a5,%lo(fib)
	sw	a4,4(a5)
	li	a5,2
	sw	a5,-20(s0)
	j	L2
L3:
	lw	a5,-20(s0)
	lui	a4,%hi(fib)
	addi	a5,a5,-1
	addi	a4,a4,%lo(fib)
	slli	a5,a5,2
	lui	a3,%hi(fib)
	add	a5,a4,a5
	addi	a3,a3,%lo(fib)
	lw	a4,0(a5)
	lw	a5,-20(s0)
	addi	a5,a5,-2
	slli	a5,a5,2
	add	a5,a3,a5
	lw	a5,0(a5)
	add	a4,a4,a5
	lui	a5,%hi(fib)
	addi	a3,a5,%lo(fib)
	lw	a5,-20(s0)
	slli	a5,a5,2
	add	a5,a3,a5
	sw	a4,0(a5)
	lw	a5,-20(s0)
	addi	a5,a5,1
	sw	a5,-20(s0)
L2:
	lw	a4,-20(s0)
	li	a5,99
	nop
	ble	a4,a5,L3
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
	call	compute
	li	a5,0
	lw	ra,12(sp)
	mv	a0,a5
	lw	s0,8(sp)
	addi	sp,sp,16
	jr	ra
