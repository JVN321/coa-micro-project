# Reorder Pass README (`riscv_reorder.py`)

`riscv_reorder.py` performs conservative local instruction scheduling on RISC-V assembly to improve performance on a 5-stage in-order pipeline.

## Goal

Reduce avoidable pipeline stalls (especially load-use hazards) while preserving behavior.

## Usage

```bash
python riscv_reorder.py input.s output.s
```

## High-Level Algorithm

1. Parse source lines using `riscv_parser.parse_assembly_lines(...)`.
2. Build local scheduling regions by accumulating instruction lines until a boundary:
- label, directive, comment/blank transitions, control flow instruction, or barrier.
3. For each region (block), build dependency constraints.
4. Schedule instructions with a list-scheduling strategy.
5. Re-emit original text lines in new order.

## Dependency Model

Within each block, the pass enforces hard dependencies:

- `RAW` (Read After Write)
- `WAR` (Write After Read)
- `WAW` (Write After Write)

Plus conservative memory ordering:

- All load/store operations keep original relative order (prevents unsafe alias reordering).

## Performance Heuristic

The pass uses a soft latency preference for load-use:

- If instruction `A` is a load and instruction `B` reads its destination register,
- prefer at least one independent instruction between them (modeled as latency distance).

When multiple instructions are ready, the scheduler:

- prefers ones that satisfy current latency constraints,
- falls back to earliest-ready,
- uses original order as tie-breaker for stable output.

## Why This Is Safe (Conservative)

- Never reorders across control/barrier instructions.
- Never violates register dependence constraints.
- Never changes memory op order.

This may miss some legal optimizations, but strongly reduces risk of semantic changes.

## Function Map

- `build_dependency_graph(block)`:
- builds hard predecessor edges and soft latency hints.

- `schedule_block(block)`:
- list-schedules one block using constraints.

- `reorder_lines(parsed)`:
- identifies blocks and applies scheduling per block.

- `optimize_assembly_text(text)`:
- parse -> reorder -> render pipeline.

## Known Limitations

- No global scheduling across basic blocks.
- No branch-delay modeling beyond boundaries.
- No advanced alias analysis.
- Assumes textual assembly is already valid and reasonably canonical.

## Suggested Next Extensions

1. Add optional NOP insertion when no suitable instruction exists for load-use gaps.
2. Add architecture configuration (latency table per pipeline variant).
3. Add unit tests with before/after assembly snippets.
4. Add optional "aggressive" mode with limited memory disambiguation hints.
