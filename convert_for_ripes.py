#!/usr/bin/env python3
"""Convert a GCC-compiled RISC-V (rv32i) assembly file to a Ripes-compatible file.

What this script does:
  1. Strips GCC-only assembler directives Ripes does not understand
     (.file, .option, .attribute, .ident, .type, .size).
  2. Detects any call to __mulsi3 (GCC's software-multiply helper that is NOT
     linked in when running inside Ripes) and appends a pure rv32i shift-and-add
     software-multiply implementation so the file is self-contained.
  3. Optionally inserts a tiny _start stub so Ripes begins execution at _start
     rather than relying on a bare 'main' label (use --start-stub to enable).

Usage:
    python convert_for_ripes.py <input.s> [output.s] [--start-stub]

If no output path is given the result is written next to the input file with the
suffix '_ripes.s'.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Directives that are GCC-specific and that Ripes rejects
# ---------------------------------------------------------------------------
STRIP_DIRECTIVE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^\s*\.file\b"),
    re.compile(r"^\s*\.option\b"),
    re.compile(r"^\s*\.attribute\b"),
    re.compile(r"^\s*\.ident\b"),
    re.compile(r"^\s*\.type\b"),
    re.compile(r"^\s*\.size\b"),
]

# ---------------------------------------------------------------------------
# __mulsi3 — pure rv32i (shift-and-add) 32-bit signed multiply
#
# Calling convention (same as GCC libgcc):
#   a0 × a1  →  a0
# Clobbers: t0, t1 only.
# Works correctly for all signed 32-bit inputs because the lower 32 bits of
# a signed and an unsigned product are identical.
# ---------------------------------------------------------------------------
MULSI3_IMPL = """\
# -----------------------------------------------------------------------
# __mulsi3: software 32-bit multiply (rv32i, shift-and-add)
# a0 = a0 * a1   clobbers: t0, t1
# -----------------------------------------------------------------------
__mulsi3:
\tmv\tt0, a0\t\t# t0 = multiplicand
\tli\ta0, 0\t\t# a0 = accumulator (result)
__mulsi3_loop:
\tandi\tt1, a1, 1\t# test LSB of multiplier
\tbeq\tt1, zero, __mulsi3_skip
\tadd\ta0, a0, t0\t# accumulate
__mulsi3_skip:
\tslli\tt0, t0, 1\t# multiplicand <<= 1
\tsrli\ta1, a1, 1\t# multiplier >>= 1  (logical shift: handles sign via wrap)
\tbne\ta1, zero, __mulsi3_loop
\tjr\tra
"""

# ---------------------------------------------------------------------------
# _start stub — jumps into main and then loops forever (ecall exit not needed)
# ---------------------------------------------------------------------------
START_STUB = """\
# -----------------------------------------------------------------------
# _start: Ripes entry point — calls main, then exits via ecall
# -----------------------------------------------------------------------
\t.text
\t.globl\t_start
_start:
\tcall\tmain
\tli\ta7, 10\t\t# Ripes exit ecall (terminate simulation)
\tecall
"""


def strip_gcc_directives(lines: list[str]) -> list[str]:
    """Remove lines that contain GCC-only assembler directives."""
    cleaned: list[str] = []
    for line in lines:
        if any(pat.match(line) for pat in STRIP_DIRECTIVE_PATTERNS):
            continue
        cleaned.append(line)
    return cleaned


def needs_mulsi3(lines: list[str]) -> bool:
    """Return True if any line calls __mulsi3."""
    for line in lines:
        # Match both "call __mulsi3" and "jal ra,__mulsi3" etc.
        if re.search(r"\b__mulsi3\b", line):
            return True
    return False


def convert(input_path: Path, output_path: Path, add_start_stub: bool) -> None:
    src = input_path.read_text(encoding="utf-8")
    lines = src.splitlines(keepends=True)

    # 1. Strip unsupported directives
    lines = strip_gcc_directives(lines)

    # 2. Optionally prepend _start stub (before all other .text content)
    extra_header: list[str] = []
    if add_start_stub:
        extra_header = [START_STUB + "\n"]

    # 3. Append __mulsi3 if needed
    extra_footer: list[str] = []
    if needs_mulsi3(lines):
        extra_footer = ["\n\t.text\n", MULSI3_IMPL]

    result = "".join(extra_header + lines + extra_footer)
    output_path.write_text(result, encoding="utf-8")
    print(f"[convert_for_ripes] Input  : {input_path}")
    print(f"[convert_for_ripes] Output : {output_path}")
    if add_start_stub:
        print("[convert_for_ripes] _start stub added  (entry point = _start)")
    else:
        print("[convert_for_ripes] No _start stub     (entry point = main)")
    if extra_footer:
        print("[convert_for_ripes] __mulsi3 appended  (software multiply for rv32i)")
    else:
        print("[convert_for_ripes] __mulsi3 not needed")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert a GCC rv32i .s file to a Ripes-compatible assembly file."
    )
    parser.add_argument("input", help="Path to the GCC-compiled .s file")
    parser.add_argument(
        "output",
        nargs="?",
        default=None,
        help="Output path (default: <input>_ripes.s next to input file)",
    )
    parser.add_argument(
        "--start-stub",
        action="store_true",
        help="Prepend a _start label so Ripes uses _start as the entry point",
    )
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    if not input_path.exists():
        print(f"[error] File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        output_path = Path(args.output).resolve()
    else:
        output_path = input_path.with_name(input_path.stem + "_ripes.s")

    convert(input_path, output_path, add_start_stub=args.start_stub)


if __name__ == "__main__":
    main()
