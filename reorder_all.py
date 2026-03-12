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

# ─────────────────────────────────────────────────────────────────────────────


def main(tests_dir: Path = None, reordered_dir: Path = None) -> None:
    tests_dir     = tests_dir     or (ROOT / "tests")
    reordered_dir = reordered_dir or (ROOT / "reordered_tests")

    reordered_dir.mkdir(parents=True, exist_ok=True)

    asm_files = sorted(tests_dir.glob("*.s"))
    if not asm_files:
        print(f"[warn] No .s files found in {tests_dir}")
        return

    passed = 0
    failed = 0

    print(f"Found {len(asm_files)} assembly file(s) in {tests_dir}\n")

    for src in asm_files:
        out = reordered_dir / f"{src.stem}_reordered.s"
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
    print(f"Reordered files saved to: {reordered_dir}/")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--tests-dir",     type=Path, default=None)
    parser.add_argument("--reordered-dir", type=Path, default=None)
    parser.add_argument("--results-dir",   type=Path, default=None)  # accepted but unused
    args = parser.parse_args()
    main(args.tests_dir, args.reordered_dir)
