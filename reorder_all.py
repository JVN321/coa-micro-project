#!/usr/bin/env python3
"""reorder_all.py – batch-reorder every assembly program in tests/.

For each *.s file in the tests/ directory the script calls
riscv_reorder_minimal.optimize_assembly_text directly and writes the
reordered output to reordered_tests/<stem>_reordered.s.

Usage (run from the project root):
    python reorder_all.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root is on the path so the shared modules are importable
# when this script is invoked from any working directory.
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from riscv_reorder_minimal import optimize_assembly_text  # noqa: E402

# ── Paths (all relative to the project root) ─────────────────────────────────
TESTS_DIR     = ROOT / "tests"
REORDERED_DIR = ROOT / "reordered_tests"
# ─────────────────────────────────────────────────────────────────────────────


def main() -> None:
    REORDERED_DIR.mkdir(parents=True, exist_ok=True)

    asm_files = sorted(TESTS_DIR.glob("*.s"))
    if not asm_files:
        print(f"[warn] No .s files found in {TESTS_DIR}")
        return

    passed = 0
    failed = 0

    print(f"Found {len(asm_files)} assembly file(s) in {TESTS_DIR.relative_to(ROOT)}/\n")

    for src in asm_files:
        out = REORDERED_DIR / f"{src.stem}_reordered.s"
        print(f"  {src.name:<30}  ->  {out.name}", end="  ", flush=True)

        try:
            src_text = src.read_text(encoding="utf-8")
            reordered = optimize_assembly_text(src_text)
            out.write_text(reordered, encoding="utf-8")
            print("OK")
            passed += 1
        except Exception as exc:
            print("FAILED")
            print(f"    {exc}")
            failed += 1

    print(f"\nDone — {passed} succeeded, {failed} failed.")
    print(f"Reordered files saved to: {REORDERED_DIR.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
