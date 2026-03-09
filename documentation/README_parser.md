# Parser README (`riscv_parser.py`)

`riscv_parser.py` provides reusable parsing utilities for textual RISC-V assembly files.

## What It Produces

The parser maps each source line into a `ParsedLine` object:

- `kind`: one of `comment`, `blank`, `directive`, `label`, `instruction`, `other`
- `text`: original line text (preserved)
- `inst`: `Instruction` object when `kind == instruction`

`Instruction` contains metadata useful for optimization passes:

- `original_line`: exact original line
- `opcode`: lowercased opcode/pseudo-op
- `operands`: comma-split operand list
- `reads`: registers read by this instruction
- `writes`: registers written by this instruction
- `is_load`: whether opcode is recognized as load
- `is_store`: whether opcode is recognized as store

## Public API

- `parse_line(line: str) -> ParsedLine`
- `parse_assembly_lines(lines: List[str]) -> List[ParsedLine]`
- `is_control_or_barrier(inst: Instruction) -> bool`

## Internal Parsing Flow

1. Classify line shape:
- blank, comment (`#`), directive (`.`), label (`...:`), or candidate instruction.

2. Strip trailing comments for instruction parsing:
- Uses the text before `#` to parse opcode/operands.

3. Split opcode and operands:
- `split_opcode_operands(...)` lowercases opcode and comma-splits operands.

4. Infer register read/write sets:
- `parse_instruction_reads_writes(...)` applies opcode-aware rules.
- Handles common load/store/branch/jump forms and generic dest-first ALU-like forms.

5. Preserve source fidelity:
- Original lines are stored so downstream passes can re-emit text exactly.

## Register Detection

Registers are detected using:

- ABI names: `ra`, `sp`, `a0`, `t0`, `s0`, etc.
- Integer names: `x0..x31`
- Floating-point names: `f0..f31`

`zero` is removed from dependency sets (`reads/writes`) because writing it has no effect.

## Control/Barrier Classification

`is_control_or_barrier(...)` returns true for:

- branch ops (`beq`, `bne`, ...)
- jump/call/return ops (`jal`, `jalr`, `ret`, ...)
- explicit barriers/system-like ops (`fence`, `ecall`, ...)

Optimizers can use this to define safe scheduling boundaries.

## Extending the Parser

To support more instructions or pseudo-ops:

1. Add opcode names to opcode sets (`LOAD_OPS`, `STORE_OPS`, etc.)
2. Update `parse_instruction_reads_writes(...)` for special operand semantics
3. Keep behavior conservative when uncertain

## Limitations

- Textual parser, not a full assembler grammar.
- Does not resolve symbols/macros/includes.
- Uses conservative heuristics for pseudo-instruction semantics.

This is intentional to keep the parser lightweight and reusable across custom analysis/optimization passes.
