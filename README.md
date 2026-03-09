# RISC-V Assembly Optimizer (5-Stage Pipeline)

This project contains a simple, conservative optimization flow for textual RISC-V assembly:

- `riscv_parser.py`: reusable parser and instruction metadata extractor
- `riscv_reorder.py`: local instruction reordering pass to reduce pipeline stalls

The reordering pass is designed for a classic in-order RISC-V 5-stage pipeline (`IF/ID/EX/MEM/WB`) and focuses on preserving correctness first, then improving schedule quality where safe.

## Files

- `riscv_parser.py`
- `riscv_reorder.py`
- `README_parser.md`
- `README_reorder.md`

## Quick Start

```bash
python riscv_reorder.py input.s output.s
```

This reads `input.s`, applies conservative scheduling inside local regions, and writes `output.s`.

## Design Goals

- Keep parser reusable for multiple optimization algorithms.
- Keep each optimization pass independent from parsing internals.
- Prefer conservative correctness constraints over aggressive transformations.

## Notes

- Reordering is local (within basic-block-like regions) and avoids crossing barriers (labels/directives/control flow).
- Memory operations are kept in original order conservatively.
- The code is intended as a foundation for coursework/experimentation, not as a full production compiler backend.
