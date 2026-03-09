#!/usr/bin/env python3
"""Simple RISC-V assembly instruction reordering for a 5-stage pipeline.

This script performs conservative, local scheduling inside basic-block-like regions
to reduce obvious hazards (especially load-use) while preserving correctness.

Usage:
    python riscv_reorder.py input.s output.s
"""

from __future__ import annotations

import argparse
from typing import Dict, List, Set, Tuple

from riscv_parser import Instruction, ParsedLine, is_control_or_barrier, parse_assembly_lines


def build_dependency_graph(block: List[Instruction]) -> Tuple[Dict[int, Set[int]], Dict[int, Dict[int, int]]]:
    """Build hard deps and soft latency hints.

    hard_preds[j] includes all i that must appear before j for correctness.
    soft_latency[i][j] is preferred minimum issue distance (cycles) for performance.
    """
    hard_preds: Dict[int, Set[int]] = {i: set() for i in range(len(block))}
    soft_latency: Dict[int, Dict[int, int]] = {i: {} for i in range(len(block))}

    for i in range(len(block)):
        for j in range(i + 1, len(block)):
            a = block[i]
            b = block[j]

            # Register correctness dependencies.
            raw = bool(a.writes & b.reads)
            waw = bool(a.writes & b.writes)
            war = bool(a.reads & b.writes)
            if raw or waw or war:
                hard_preds[j].add(i)

            # Keep memory operations in original order (conservative alias handling).
            if (a.is_load or a.is_store) and (b.is_load or b.is_store):
                hard_preds[j].add(i)

            # Load-use latency hint: in a classic 5-stage pipeline, prefer one
            # independent instruction between a load and its consumer.
            if a.is_load and (a.writes & b.reads):
                soft_latency[i][j] = max(soft_latency[i].get(j, 1), 2)

    return hard_preds, soft_latency


def schedule_block(block: List[Instruction]) -> List[Instruction]:
    if len(block) <= 1:
        return block[:]

    hard_preds, soft_latency = build_dependency_graph(block)

    unscheduled = set(range(len(block)))
    scheduled: List[int] = []
    issue_cycle: Dict[int, int] = {}

    while unscheduled:
        ready = [idx for idx in unscheduled if hard_preds[idx].issubset(set(scheduled))]
        if not ready:
            # Should not happen with forward-only dependencies; fallback to original order.
            scheduled.extend(sorted(unscheduled))
            break

        cycle = len(scheduled)

        def preferred_earliest(idx: int) -> int:
            earliest = 0
            for pred in scheduled:
                latency = soft_latency.get(pred, {}).get(idx, 1)
                earliest = max(earliest, issue_cycle[pred] + latency)
            return earliest

        on_time = [idx for idx in ready if preferred_earliest(idx) <= cycle]

        if on_time:
            # Keep output stable by preferring original order among equally good choices.
            chosen = min(on_time)
        else:
            # No candidate can fully hide latency; pick the one that becomes ready soonest.
            chosen = min(ready, key=lambda idx: (preferred_earliest(idx), idx))

        scheduled.append(chosen)
        issue_cycle[chosen] = cycle
        unscheduled.remove(chosen)

    return [block[i] for i in scheduled]


def reorder_lines(parsed: List[ParsedLine]) -> List[str]:
    output: List[str] = []
    block: List[Instruction] = []

    def flush_block() -> None:
        nonlocal block
        if block:
            for inst in schedule_block(block):
                output.append(inst.original_line)
            block = []

    for entry in parsed:
        if entry.kind == "instruction" and entry.inst is not None:
            if is_control_or_barrier(entry.inst):
                flush_block()
                output.append(entry.text)
            else:
                block.append(entry.inst)
        else:
            flush_block()
            output.append(entry.text)

    flush_block()
    return output


def optimize_assembly_text(text: str) -> str:
    lines = text.splitlines(keepends=True)
    parsed = parse_assembly_lines(lines)
    reordered = reorder_lines(parsed)
    return "".join(reordered)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Conservative RISC-V instruction reordering for a 5-stage pipeline"
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
