#!/usr/bin/env python3
"""Compile every C file in <folder>/programs/, convert each to a Ripes-compatible
assembly file, and place the result in <folder>/test scripts/.

Usage:
    python compile_c_for_ripes.py <test_folder> [--start-stub] [--gcc GCC_PATH]

Steps performed for each .c file found in <folder>/programs/:
    1. Compile with riscv32-unknown-elf-gcc (or riscv64-unknown-elf-gcc if the
       32-bit variant is not found) to a raw .s assembly file.
    2. Run convert_for_ripes.py on the .s file.
    3. Copy the converted *_ripes.s into <folder>/test scripts/.

The intermediate .s files are written alongside the .c files in programs/ and
kept so you can inspect the raw GCC output.

Requirements:
    - A RISC-V GCC cross-compiler on PATH (riscv32-unknown-elf-gcc or
      riscv64-unknown-elf-gcc).  Override with --gcc if necessary.
    - convert_for_ripes.py must be in the same directory as this script.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

# Default compiler candidates (tried in order)
GCC_CANDIDATES = [
    "riscv32-unknown-elf-gcc",
    "riscv64-unknown-elf-gcc",
]

GCC_FLAGS = [
    "-march=rv32i",
    "-mabi=ilp32",
    "-O0",        # no optimisation so the assembly is readable
    "-S",         # stop after compiling to assembly
    "-nostdlib",  # no libc — we provide everything ourselves
]


def find_gcc(override: str | None) -> str:
    """Return the GCC executable to use, or exit with a clear error."""
    if override:
        if shutil.which(override):
            return override
        print(f"[error] Specified GCC not found on PATH: {override}", file=sys.stderr)
        sys.exit(1)

    for candidate in GCC_CANDIDATES:
        if shutil.which(candidate):
            return candidate

    print(
        "[error] No RISC-V GCC found on PATH.\n"
        "        Install riscv32-unknown-elf-gcc (or riscv64-unknown-elf-gcc) and\n"
        "        make sure it is on your PATH, or pass --gcc <path> explicitly.\n"
        "        Windows users: https://github.com/stnolting/riscv-gcc-prebuilt",
        file=sys.stderr,
    )
    sys.exit(1)


def compile_c(gcc: str, c_file: Path, s_file: Path) -> bool:
    """Compile *c_file* to *s_file*.  Returns True on success."""
    cmd = [gcc] + GCC_FLAGS + [str(c_file), "-o", str(s_file)]
    print(f"  [gcc] {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"  [error] Compilation failed for {c_file.name}", file=sys.stderr)
        return False
    return True


def convert(convert_script: Path, s_file: Path, out_file: Path, start_stub: bool) -> bool:
    """Run convert_for_ripes.py.  Returns True on success."""
    cmd = [sys.executable, str(convert_script), str(s_file), str(out_file)]
    if not start_stub:
        cmd.append("--no-start-stub")
    print(f"  [convert] {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"  [error] Conversion failed for {s_file.name}", file=sys.stderr)
        return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compile C files in <folder>/programs/ and convert to Ripes assembly."
    )
    parser.add_argument("folder", help="Test folder (e.g. test2). Must contain a programs/ sub-folder.")
    parser.add_argument(
        "--no-start-stub",
        action="store_true",
        help="Do NOT add a _start entry-point stub (the stub is added by default).",
    )
    parser.add_argument(
        "--gcc",
        default=None,
        metavar="GCC_PATH",
        help="Path or name of the RISC-V GCC executable to use.",
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------ paths
    folder = Path(args.folder).resolve()
    programs_dir  = folder / "programs"
    tests_dir     = folder / "test scripts"
    convert_script = Path(__file__).parent / "convert_for_ripes.py"

    if not folder.exists():
        print(f"[error] Folder not found: {folder}", file=sys.stderr)
        sys.exit(1)
    if not programs_dir.exists():
        print(f"[error] 'programs' sub-folder not found inside: {folder}", file=sys.stderr)
        sys.exit(1)
    if not convert_script.exists():
        print(f"[error] convert_for_ripes.py not found at: {convert_script}", file=sys.stderr)
        sys.exit(1)

    tests_dir.mkdir(exist_ok=True)

    # --------------------------------------------------------- find compiler
    gcc = find_gcc(args.gcc)
    print(f"[compile_c_for_ripes] Compiler  : {gcc}")
    print(f"[compile_c_for_ripes] Programs  : {programs_dir}")
    print(f"[compile_c_for_ripes] Output    : {tests_dir}")
    print()

    # --------------------------------------------------- process each .c file
    c_files = sorted(programs_dir.glob("*.c"))
    if not c_files:
        print(f"[warning] No .c files found in {programs_dir}")
        sys.exit(0)

    success_count = 0
    fail_count = 0

    for c_file in c_files:
        print(f"--- {c_file.name} ---")

        # Step 1: compile → raw assembly (kept in programs/)
        s_file = programs_dir / (c_file.stem + ".s")
        if not compile_c(gcc, c_file, s_file):
            fail_count += 1
            print()
            continue

        # Step 2: convert → Ripes-compatible assembly (written to programs/ then moved)
        ripes_s_file = programs_dir / (c_file.stem + "_ripes.s")
        if not convert(convert_script, s_file, ripes_s_file, start_stub=not args.no_start_stub):
            fail_count += 1
            print()
            continue

        # Step 3: move the converted file into test scripts/
        dest = tests_dir / ripes_s_file.name
        shutil.move(str(ripes_s_file), str(dest))
        print(f"  [done]  → {dest.relative_to(folder)}")
        success_count += 1
        print()

    # --------------------------------------------------------------- summary
    total = success_count + fail_count
    print(f"[compile_c_for_ripes] Done: {success_count}/{total} file(s) converted successfully.")
    if fail_count:
        sys.exit(1)


if __name__ == "__main__":
    main()
