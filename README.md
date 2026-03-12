# RISC-V Assembly Optimizer (5-Stage Pipeline)

A conservative optimization toolchain for textual RISC-V assembly targeting a classic in-order 5-stage pipeline (`IF → ID → EX → MEM → WB`). The pipeline focuses on preserving correctness first, then improving schedule quality where safe.

---

## Project Structure

```
.
├── riscv_parser.py           # Reusable parser and instruction metadata extractor
├── riscv_reorder.py          # Full list-scheduling reorder pass
├── riscv_reorder_minimal.py  # Lightweight sliding-window reorder pass
├── reorder_all.py            # Batch-reorder every .s file in a tests directory
├── run_benchmarks.py         # Run Ripes CLI and collect JSON performance data
├── analyse_results.py        # Parse JSON results and produce analysis CSV
├── run.py                    # Top-level runner: reorder → benchmark → analyse
├── compile_c_for_ripes.py    # Compile C programs and convert them for Ripes
├── convert_for_ripes.py      # Convert a GCC .s file to a Ripes-compatible .s file
├── tests/                    # Default original assembly test programs
├── reordered_tests/          # Default output from reorder_all.py
├── results/                  # Default JSON outputs from Ripes + analysis.csv
└── documentation/
    ├── README_parser.md
    ├── README_reorder.md
    └── README_reorder_minimal.md
```

---

## Quick Start

### Recommended: run everything at once

```bash
# Default — uses tests/, reordered_tests/, results/
python run.py

# Custom test folder (see "Multiple Test Sets" below)
python run.py "path/to/my_test_folder"
```

`run.py` runs all three pipeline stages in order:
`reorder_all.py` → `run_benchmarks.py` → `analyse_results.py`

---

## Compiling C Programs for Ripes

If your test set contains C source files, use `compile_c_for_ripes.py` to compile
them and produce Ripes-ready `.s` files automatically.

### Test set layout

Your test folder must contain a `programs/` sub-folder with the `.c` files:

```
my_test_set/
└── programs/
    ├── foo.c
    └── bar.c
```

### One command to compile and convert

```bash
python compile_c_for_ripes.py my_test_set --start-stub
```

What happens:

| Step | Action |
|------|--------|
| 1 | Each `.c` file in `programs/` is compiled with `riscv32-unknown-elf-gcc -march=rv32i -mabi=ilp32 -O0 -nostdlib -S` to a raw `.s` file (kept in `programs/`). |
| 2 | `convert_for_ripes.py` strips GCC-only directives, inlines `__mulsi3` if needed, and (with `--start-stub`) prepends a `_start` entry point that calls `main` and exits via `ecall`. |
| 3 | The `*_ripes.s` files are moved to `my_test_set/test scripts/`, ready to load in Ripes. |

After running:

```
my_test_set/
├── programs/
│   ├── foo.c
│   ├── foo.s          ← raw GCC output (kept for reference)
│   └── bar.c
│   └── bar.s
└── test scripts/
    ├── foo_ripes.s    ← ready to open in Ripes
    └── bar_ripes.s
```

### CLI options

```
python compile_c_for_ripes.py <folder> [options]

positional:
  folder          Test folder containing a programs/ sub-folder (e.g. test2)

options:
  --start-stub    Prepend a _start label (calls main, then ecall exit).
                  Required when Ripes is set to start at _start (recommended).
  --gcc PATH      Override the RISC-V GCC executable name / path.
                  Defaults: tries riscv32-unknown-elf-gcc, then
                  riscv64-unknown-elf-gcc.
```

### Installing a RISC-V GCC cross-compiler (Windows)

Download a pre-built toolchain from
[stnolting/riscv-gcc-prebuilt](https://github.com/stnolting/riscv-gcc-prebuilt)
and add its `bin/` directory to your `PATH`.

---

## Ripes Conversion (single file)

To convert a single GCC-compiled `.s` file without recompiling:

```bash
python convert_for_ripes.py input.s [output.s] [--start-stub]
```

If no output path is given the result is written next to the input as `<name>_ripes.s`.

What `convert_for_ripes.py` does:

- Strips unsupported GCC-only directives (`.file`, `.option`, `.attribute`, `.ident`, `.type`, `.size`).
- Detects any `call __mulsi3` (GCC's software-multiply helper) and appends a
  pure rv32i shift-and-add implementation so the file is self-contained.
- With `--start-stub`: prepends a `_start` label that calls `main` then issues
  `ecall` (a7 = 10) to terminate the Ripes simulation cleanly.

---

### Running stages individually

#### 1. Reorder a single file (full list-scheduling pass)

```bash
python riscv_reorder.py input.s output.s
```

#### 2. Reorder a single file (lightweight sliding-window pass)

```bash
python riscv_reorder_minimal.py input.s output.s
```

#### 3. Batch-reorder all test programs

```bash
# Default: reads tests/, writes reordered_tests/
python reorder_all.py

# Custom directories
python reorder_all.py --tests-dir "my_folder/test scripts" --reordered-dir "my_folder/reordered_tests"
```

#### 4. Run Ripes benchmarks

```bash
# Default directories
python run_benchmarks.py

# Custom directories
python run_benchmarks.py \
    --tests-dir     "my_folder/test scripts" \
    --reordered-dir "my_folder/reordered_tests" \
    --results-dir   "my_folder/results"
```

**Prerequisites:** Ripes CLI must be installed. Set `RIPES_EXE` in your `.env` file. Run `reorder_all.py` first so that the reordered directory is populated.

What it does:
1. Runs every `*.s` in `tests-dir` → `<results-dir>/<stem>_original.json`
2. Runs every `*.s` in `reordered-dir` → `<results-dir>/<stem>_reordered.json`
3. Prints a side-by-side comparison table (cycles, IPC, CPI).

#### 5. Analyse benchmark results

```bash
# Default
python analyse_results.py

# Custom
python analyse_results.py --results-dir "my_folder/results"
```

No Ripes installation required — operates entirely on JSON files already produced by `run_benchmarks.py`.

- Reads every `*_original.json` / `*_reordered.json` pair from the results directory.
- Computes performance metrics: cycles, instructions retired, IPC, CPI, and pipeline stall counts.
- Prints a formatted analysis table to the terminal.
- Writes/overwrites `<results-dir>/analysis.csv`.

---

## Multiple Test Sets

You can maintain independent sets of test scripts and results by passing a folder to `run.py`. The folder must contain a sub-folder named `test scripts` with your `.s` files:

```
my_test_set/
└── test scripts/
    ├── prog_a.s
    └── prog_b.s
```

Run it with:

```bash
python run.py "path/to/my_test_set"
```

The following folders are created automatically inside your test set folder:

```
my_test_set/
├── test scripts/       ← your source files (you provide this)
├── reordered_tests/    ← created by reorder_all.py
└── results/            ← created by run_benchmarks.py + analyse_results.py
    ├── prog_a_original.json
    ├── prog_a_reordered.json
    ├── prog_b_original.json
    ├── prog_b_reordered.json
    └── analysis.csv
```

Each test set is fully self-contained and does not affect the default `tests/` / `results/` directories.

---

## Recommended Workflow

```
python run.py [optional: "path/to/test_folder"]
        │
        ├─ reorder_all.py       ← generate reordered assembly
        │
        ├─ run_benchmarks.py    ← simulate both versions with Ripes, save JSON
        │
        └─ analyse_results.py   ← parse JSON, compute stall counts, write analysis.csv
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
