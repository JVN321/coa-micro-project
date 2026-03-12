# Minimal RISC-V Reorder Pass (`riscv_reorder_minimal.py`)

A simple, readable instruction reordering script for RISC-V assembly targeting a classic 5-stage in-order pipeline (`IF → ID → EX → MEM → WB`).

## Purpose

In a 5-stage pipeline, a **pipeline stall** (bubble) is inserted when an instruction needs a result that the previous instruction has not yet produced. The most common case is a **load-use hazard**:

```asm
lw   t0, 0(a0)     # result available after MEM stage
add  t1, t0, t2    # needs t0 in EX stage — 1 cycle stall inserted by hardware
```

This script tries to eliminate such stalls by finding an independent instruction nearby and sliding it into the gap.

---

## Algorithm

```
WINDOW_SIZE = 3

for each instruction i (starting from i = 1):
    if instruction[i] depends on instruction[i-1]:
        for j in range(i+1, i + WINDOW_SIZE - 1):   # look 1 instruction ahead
            if instruction[j] is independent of both instruction[i-1] and instruction[i]:
                move instruction[j] to position i    # insert it between i-1 and i
                break
```

### Step-by-step walkthrough

Given this block before reordering:

```
[0]  lw   t0, 0(a0)      ← instruction i-1
[1]  add  t1, t0, t2     ← instruction i   (depends on i-1 via t0)
[2]  add  a1, a2, a3     ← candidate j     (independent of both)
```

1. `i = 1`: check if `add t1, t0, t2` depends on `lw t0` → **yes** (RAW on `t0`).
2. Search `j = 2`: candidate is `add a1, a2, a3`.
   - Does it depend on `lw t0`? No.
   - Does `add t1` depend on it? No.
   - → **Safe to move.**
3. Pop `[2]`, insert at position `1`:

```
[0]  lw   t0, 0(a0)      ← load
[1]  add  a1, a2, a3     ← moved here: fills load-use slot
[2]  add  t1, t0, t2     ← now 1 cycle later, t0 is ready
```

The hardware stall is eliminated.

---

## Dependency Checks

`depends_on(a, b)` returns `True` if reordering `a` and `b` would be unsafe:

| Check | Name | Meaning |
|-------|------|---------|
| `a.writes ∩ b.reads ≠ ∅` | RAW | b reads a value that a produces |
| `a.writes ∩ b.writes ≠ ∅` | WAW | both write the same register |
| `a.reads ∩ b.writes ≠ ∅` | WAR | b overwrites a value a still needs |
| both are load or store | MEM | conservative alias-safe ordering |

---

## Scheduling Boundaries

The pass only reorders within **safe local regions**. A region ends whenever the parser sees:

- A **label** (e.g., `loop:`) — other code may jump here
- A **directive** (e.g., `.section`, `.word`)
- A **branch / jump / call / return** — control flow leaves the region
- A **barrier** instruction (`ecall`, `fence`, ...)

Instructions are never moved across these boundaries, preserving correctness of control flow and ABI contracts.

---

## Usage

```bash
# Single file
python riscv_reorder_minimal.py input.s output.s
```

| Argument | Description |
|----------|-------------|
| `input`  | Source RISC-V assembly file |
| `output` | Destination file for the reordered assembly |

The output file contains the **original text lines** re-emitted in the new order — no synthetic instructions are added or removed.

For batch reordering a directory of files use `reorder_all.py`:

```bash
# Default: reads tests/, writes reordered_tests/
python reorder_all.py

# Custom directories
python reorder_all.py --tests-dir "my_folder/test scripts" --reordered-dir "my_folder/reordered_tests"
```

---

## Key Design Choices

- **Window size of 3** keeps the algorithm O(n) and easy to reason about.
- **Conservative memory ordering**: all loads and stores keep their relative order, avoiding any alias-analysis requirement.
- **Original line text is preserved**: comments and formatting survive unchanged.
- **Parser is separate** (`riscv_parser.py`): this script only contains scheduling logic and can be understood independently.

---

## Limitations

- Only looks **one instruction ahead** for a filler (`WINDOW_SIZE - 2 = 1`). A window of 4 or 5 would find more opportunities at the cost of more complexity.
- Does **not insert NOPs**: if no independent instruction is found, the hardware still inserts the stall bubble.
- No **inter-block** (global) scheduling.
- Memory aliases are handled conservatively — two stores to different addresses are not reordered even if provably safe.
