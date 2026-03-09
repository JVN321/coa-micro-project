# RISC-V Assembly Optimizer (5-Stage Pipeline)

A conservative optimization toolchain for textual RISC-V assembly targeting a classic in-order 5-stage pipeline (`IF → ID → EX → MEM → WB`). The pipeline focuses on preserving correctness first, then improving schedule quality where safe.

---

## Project Structure

```
.
├── riscv_parser.py           # Reusable parser and instruction metadata extractor
├── riscv_reorder.py          # Full list-scheduling reorder pass
├── riscv_reorder_minimal.py  # Lightweight sliding-window reorder pass
├── reorder_all.py            # Batch-reorder every .s file in tests/
├── run_benchmarks.py         # Run Ripes CLI and collect JSON performance data
├── analyze_results.py        # Parse JSON results and produce analysis CSV
├── tests/                    # Original assembly test programs
├── reordered_tests/          # Output from reorder_all.py
├── results/                  # JSON outputs from Ripes + analysis.csv
└── documentation/
    ├── README_parser.md
    ├── README_reorder.md
    └── README_reorder_minimal.md
```

---

## Quick Start

### 1. Reorder a single file (full list-scheduling pass)

```bash
python riscv_reorder.py input.s output.s
```

Parses `input.s`, applies conservative list-scheduling inside local basic-block regions, and writes the reordered result to `output.s`.

### 2. Reorder a single file (lightweight sliding-window pass)

```bash
python riscv_reorder_minimal.py input.s output.s
```

Uses a sliding window of configurable size (`WINDOW_SIZE`, default `10`) to move independent instructions into load-use hazard slots. Simpler and faster than the full pass, with the same correctness guarantees.

### 3. Batch-reorder all test programs

```bash
python reorder_all.py
```

Reads every `*.s` file from `tests/`, applies the minimal reorder pass to each one, and writes the results to `reordered_tests/<stem>_reordered.s`. Creates the output directory automatically if it does not exist.

### 4. Run Ripes benchmarks

```bash
python run_benchmarks.py
```

**Prerequisites:** Ripes CLI must be installed. Edit the `RIPES_EXE` path near the top of `run_benchmarks.py` to point to your installation, then run `reorder_all.py` first so that `reordered_tests/` is populated.

What it does:
1. Runs every `*.s` in `tests/` → `results/<stem>_original.json`
2. Runs every `*.s` in `reordered_tests/` → `results/<stem>_reordered.json`
3. Prints a side-by-side comparison table (cycles, IPC, CPI).
4. Writes `results/benchmark_summary.csv`.

### 5. Analyze benchmark results

```bash
python analyze_results.py
```

No Ripes installation required — operates entirely on the JSON files already produced by `run_benchmarks.py`.

- Reads every `*_original.json` / `*_reordered.json` pair from `results/`.
- Computes performance metrics: cycles, instructions retired, IPC, CPI, and pipeline stall counts.
- Prints a formatted analysis table to the terminal.
- Writes/overwrites `results/analysis.csv`.

---

## Recommended Workflow

```
reorder_all.py          ← generate reordered_tests/
       │
       ▼
run_benchmarks.py       ← simulate both versions with Ripes, save JSON
       │
       ▼
analyze_results.py      ← parse JSON, compute stall counts, write analysis.csv
```

---

## Reordering Passes

### `riscv_reorder.py` — Full List Scheduler

Builds a complete dependency graph for each local scheduling region and applies a list-scheduling strategy:

- Enforces hard `RAW`, `WAR`, and `WAW` register dependencies.
- Keeps all load/store operations in their original relative order (conservative alias handling).
- Uses a soft latency preference to place at least one independent instruction between a load and its consumer.
- When multiple instructions are ready, prefers those that satisfy latency constraints, falling back to original-order tie-breaking.

### `riscv_reorder_minimal.py` — Sliding-Window Scheduler

Uses a simpler approach suitable for quick experimentation:

- Scans instructions one at a time.
- When instruction `i` depends on instruction `i-1`, searches up to `WINDOW_SIZE - 2` instructions ahead for an independent candidate.
- If found, moves that candidate between `i-1` and `i` to fill the hazard slot.
- Same dependency model (`RAW`, `WAW`, `WAR`, memory ordering) as the full pass.

---

## Scheduling Boundaries

Both passes only reorder within **safe local regions**. A region ends at:

- A **label** (e.g., `loop:`) — other code may jump here.
- A **directive** (e.g., `.section`, `.word`).
- A **branch / jump / call / return** — control flow leaves the region.
- A **barrier** instruction (`ecall`, `ebreak`, `fence`, ...).

Instructions are never moved across these boundaries.

---

## Design Goals

- Keep the parser reusable across multiple optimization algorithms.
- Keep each optimization pass independent from parsing internals.
- Prefer conservative correctness constraints over aggressive transformations.

## Notes

- All reordering is local (within basic-block-like regions).
- Memory operations are kept in original relative order.
- The code is intended as a foundation for coursework/experimentation, not as a full production compiler backend.
- See `documentation/` for detailed per-module documentation.
