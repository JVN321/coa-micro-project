#!/usr/bin/env python3
"""Minimal RISC-V instruction reordering using a sliding window of size 3.

Algorithm:
    window_size = 3
    for each instruction i:
        if instruction i depends on instruction i-1:
            search the next (window_size - 2) instructions for one independent of both i-1 and i
            if found, move it between i-1 and i

Usage:
    python riscv_reorder_minimal.py input.s output.s
"""

from __future__ import annotations

import argparse
from typing import List

from riscv_parser import (
    Instruction,
    ParsedLine,
    is_control_or_barrier,
    parse_assembly_lines,
)

WINDOW_SIZE = 3


def depends_on(a: Instruction, b: Instruction) -> bool:
    """Return True if b has any register or memory dependency on a."""
    if a.writes & b.reads:   # RAW
        return True
    if a.writes & b.writes:  # WAW
        return True
    if a.reads & b.writes:   # WAR
        return True
    if a.is_store or b.is_store:
        return True
    return False


def window_schedule(block: List[Instruction]) -> List[Instruction]:
    """Apply the window-3 reordering pass to a flat list of instructions."""
    result = list(block)  # work on a copy
    i = 1
    while i < len(result):
        prev = result[i - 1]
        curr = result[i]

        if depends_on(prev, curr):
            # Search up to WINDOW_SIZE-2 instructions ahead for one that can
            # be safely inserted between prev and curr.
            search_limit = min(i + WINDOW_SIZE - 2, len(result) - 1)
            found_at = None
            for j in range(i + 1, search_limit + 1):
                candidate = result[j]
                if not depends_on(prev, candidate) and not depends_on(candidate, curr):
                    found_at = j
                    break

            if found_at is not None:
                # Move candidate so it sits between prev (i-1) and curr (i).
                candidate = result.pop(found_at)
                result.insert(i, candidate)
                # curr is now at i+1; advance past the newly inserted instruction
                # so we re-evaluate the (now shifted) curr next iteration.
                i += 1
                continue

        i += 1

    return result


def reorder_lines(parsed: List[ParsedLine]) -> List[str]:
    output: List[str] = []
    block: List[Instruction] = []
    # non-instruction lines that belong before the current block
    pending_non_inst: List[str] = []

    def flush_block() -> None:
        for line in pending_non_inst:
            output.append(line)
        pending_non_inst.clear()
        if block:
            for inst in window_schedule(block):
                clean = inst.original_line.split("#", 1)[0].rstrip()
                output.append(clean + "\n")
            block.clear()

    for entry in parsed:
        if entry.kind == "instruction" and entry.inst is not None:
            if is_control_or_barrier(entry.inst):
                flush_block()
                clean = entry.text.split("#", 1)[0].rstrip()
                output.append(clean + "\n")
            else:
                # Flush any accumulated non-instruction lines first so labels/
                # directives remain attached to the correct position.
                for line in pending_non_inst:
                    output.append(line)
                pending_non_inst.clear()
                block.append(entry.inst)
        else:
            # Blanks and comments carry no semantics — discard them.
            if entry.kind not in ("label", "directive"):
                continue
            flush_block()
            pending_non_inst.append(entry.text)

    # Emit anything left.
    flush_block()
    for line in pending_non_inst:
        output.append(line)

    return output


def optimize_assembly_text(text: str) -> str:
    lines = text.splitlines(keepends=True)
    parsed = parse_assembly_lines(lines)
    reordered = reorder_lines(parsed)
    return "".join(reordered)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Window-3 RISC-V instruction reordering for a 5-stage pipeline"
    )
    parser.add_argument("input", help="Input RISC-V assembly file")
    parser.add_argument("output", help="Output optimized assembly file")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        src = f.read()

    optimized = optimize_assembly_text(src)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(optimized)

    print(f"Optimized assembly written to {args.output}")


if __name__ == "__main__":
    main()
