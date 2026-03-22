"""Reusable parser utilities for textual RISC-V assembly."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Set, Tuple


REGISTER_ALIASES = {
    "zero",
    "ra",
    "sp",
    "gp",
    "tp",
    "t0",
    "t1",
    "t2",
    "s0",
    "fp",
    "s1",
    "a0",
    "a1",
    "a2",
    "a3",
    "a4",
    "a5",
    "a6",
    "a7",
    "s2",
    "s3",
    "s4",
    "s5",
    "s6",
    "s7",
    "s8",
    "s9",
    "s10",
    "s11",
    "t3",
    "t4",
    "t5",
    "t6",
}

BRANCH_OPS = {
    "beq",
    "bne",
    "blt",
    "bge",
    "bltu",
    "bgeu",
    "ble",
    "bleu",
    "bgt",
    "bgtu",
    "beqz",
    "bnez",
    "blez",
    "bgez",
    "bltz",
    "bgtz",
}

JUMP_OPS = {"jal", "jalr", "j", "jr", "ret", "call", "tail"}

LOAD_OPS = {
    "lb",
    "lh",
    "lw",
    "lbu",
    "lhu",
    "lwu",
    "ld",
    "flw",
    "fld",
}

STORE_OPS = {
    "sb",
    "sh",
    "sw",
    "sd",
    "fsw",
    "fsd",
}

UNSCHEDULABLE_OPS = {
    "ecall",
    "ebreak",
    "fence",
    "fence.i",
}

TOKEN_REG_RE = re.compile(r"\b([a-z][a-z0-9]*)\b")


@dataclass
class Instruction:
    original_line: str
    opcode: str
    operands: List[str]
    reads: Set[str]
    writes: Set[str]
    is_load: bool
    is_store: bool


@dataclass
class ParsedLine:
    kind: str  # comment|blank|directive|label|instruction|other
    text: str
    inst: Optional[Instruction] = None


def is_register(token: str) -> bool:
    if token in REGISTER_ALIASES:
        return True
    if re.fullmatch(r"x([0-9]|[12][0-9]|3[01])", token):
        return True
    return bool(re.fullmatch(r"f([0-9]|[12][0-9]|3[01])", token))


def extract_registers(text: str) -> Set[str]:
    regs: Set[str] = set()
    for tok in TOKEN_REG_RE.findall(text.lower()):
        if is_register(tok):
            regs.add(tok)
    return regs


def split_opcode_operands(code_text: str) -> Tuple[str, List[str]]:
    parts = code_text.strip().split(None, 1)
    if not parts:
        return "", []
    opcode = parts[0].lower()
    if len(parts) == 1:
        return opcode, []
    operands = [op.strip() for op in parts[1].split(",") if op.strip()]
    return opcode, operands


def parse_instruction_reads_writes(opcode: str, operands: List[str]) -> Tuple[Set[str], Set[str], bool, bool]:
    reads: Set[str] = set()
    writes: Set[str] = set()
    is_load = opcode in LOAD_OPS
    is_store = opcode in STORE_OPS

    if opcode in LOAD_OPS:
        if operands:
            writes |= extract_registers(operands[0])
        if len(operands) > 1:
            reads |= extract_registers(operands[1])
    elif opcode in STORE_OPS:
        if operands:
            reads |= extract_registers(operands[0])
        if len(operands) > 1:
            reads |= extract_registers(operands[1])
    elif opcode in BRANCH_OPS:
        if operands:
            reads |= extract_registers(operands[0])
        if len(operands) > 1:
            reads |= extract_registers(operands[1])
    elif opcode in {"lui", "auipc"}:
        if operands:
            writes |= extract_registers(operands[0])
    elif opcode in {"jal", "j", "call", "tail"}:
        if operands:
            if len(operands) >= 2:
                writes |= extract_registers(operands[0])
            elif opcode == "jal":
                writes.add("ra")
    elif opcode in {"jalr", "jr", "ret"}:
        if opcode == "jalr":
            if operands:
                writes |= extract_registers(operands[0])
            if len(operands) > 1:
                reads |= extract_registers(operands[1])
        elif opcode == "jr":
            if operands:
                reads |= extract_registers(operands[0])
        elif opcode == "ret":
            reads.add("ra")
    else:
        # RISC-V ALU and pseudo-instructions are mostly dest-first.
        if operands:
            writes |= extract_registers(operands[0])
        for op in operands[1:]:
            reads |= extract_registers(op)

    writes.discard("zero")
    reads.discard("zero")
    return reads, writes, is_load, is_store


def parse_line(line: str) -> ParsedLine:
    stripped = line.strip()
    if not stripped:
        return ParsedLine(kind="blank", text=line)
    if stripped.startswith("#"):
        return ParsedLine(kind="comment", text=line)
    if stripped.startswith("."):
        return ParsedLine(kind="directive", text=line)
    if stripped.endswith(":"):
        return ParsedLine(kind="label", text=line)

    code = line.split("#", 1)[0].strip()
    if not code:
        return ParsedLine(kind="comment", text=line)

    opcode, operands = split_opcode_operands(code)
    if not opcode:
        return ParsedLine(kind="other", text=line)

    reads, writes, is_load, is_store = parse_instruction_reads_writes(opcode, operands)
    inst = Instruction(
        original_line=line,
        opcode=opcode,
        operands=operands,
        reads=reads,
        writes=writes,
        is_load=is_load,
        is_store=is_store,
    )
    return ParsedLine(kind="instruction", text=line, inst=inst)


def parse_assembly_lines(lines: List[str]) -> List[ParsedLine]:
    return [parse_line(line) for line in lines]


def is_control_or_barrier(inst: Instruction) -> bool:
    if inst.opcode in BRANCH_OPS or inst.opcode in JUMP_OPS:
        return True
    return inst.opcode in UNSCHEDULABLE_OPS
