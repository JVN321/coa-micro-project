#!/usr/bin/env python3
"""analyze_results.py – parse Ripes JSON outputs and write a detailed CSV report.

Reads every *_original.json / *_reordered.json pair from results/, computes
performance metrics (including pipeline stall counts), prints a formatted
analysis table, and appends/overwrites results/analysis.csv.

Usage (run from the project root):
    python analyze_results.py

No Ripes installation required – operates entirely on the JSON files already
produced by run_benchmarks.py.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Optional

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT        = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"
CSV_PATH    = RESULTS_DIR / "analysis.csv"

# A 5-stage in-order pipeline needs (stages - 1) = 4 fill/drain cycles
# with zero stalls.  Everything above that is a stall or flush cycle.
PIPELINE_STAGES = 5
# ─────────────────────────────────────────────────────────────────────────────


# ── JSON loading & metric extraction ─────────────────────────────────────────

def load_json(path: Path) -> Optional[dict]:
    try:
        raw = path.read_text(encoding="utf-8")
        # Ripes CLI writes a "Program exited with code: N" preamble to stdout
        # before the JSON object.  Strip everything up to the first '{'.
        json_start = raw.find("{")
        if json_start == -1:
            raise json.JSONDecodeError("No JSON object found", raw, 0)
        return json.loads(raw[json_start:])
    except (OSError, json.JSONDecodeError) as exc:
        print(f"  [warn] Cannot read {path.name}: {exc}")
        return None


def extract_metrics(data: dict) -> dict:
    """Pull every useful field out of a Ripes JSON result."""
    cycles       = data.get("cycles")
    instructions = data.get("# instructions retired")
    ipc          = data.get("IPC")
    cpi          = data.get("CPI")
    processor    = data.get("runinfo", {}).get("processor", "")
    source_file  = data.get("runinfo", {}).get("source file", "")

    # Derive any missing scalar metrics.
    if ipc is None and cycles and instructions:
        ipc = instructions / cycles
    if cpi is None and cycles and instructions:
        cpi = cycles / instructions

    # Stall cycles: for a perfectly filled pipeline the minimum cycle count
    # is  (instructions + PIPELINE_STAGES - 1).  Every cycle above that is a
    # stall (bubble) inserted to resolve a hazard.
    stalls: Optional[int] = None
    if cycles is not None and instructions is not None:
        ideal  = int(instructions) + PIPELINE_STAGES - 1
        stalls = max(0, int(cycles) - ideal)

    # Pipeline efficiency: useful instruction-issue cycles / total cycles.
    efficiency: Optional[float] = None
    if cycles and instructions:
        efficiency = instructions / cycles  # same as IPC for a scalar CPU

    # Stall rate: stall cycles per instruction retired.
    stall_rate: Optional[float] = None
    if stalls is not None and instructions:
        stall_rate = stalls / instructions

    return {
        "cycles":      cycles,
        "instructions": instructions,
        "ipc":         ipc,
        "cpi":         cpi,
        "stalls":      stalls,
        "efficiency":  efficiency,
        "stall_rate":  stall_rate,
        "processor":   processor,
        "source_file": source_file,
    }


# ── Pairing helper ────────────────────────────────────────────────────────────

def collect_pairs() -> list[dict]:
    """Return one record per program containing both original and reordered metrics."""
    originals = {p.stem.removesuffix("_original"): p
                 for p in RESULTS_DIR.glob("*_original.json")}
    reordered = {p.stem.removesuffix("_reordered"): p
                 for p in RESULTS_DIR.glob("*_reordered.json")}

    programs = sorted(originals.keys() & reordered.keys())

    if not programs:
        return []

    # Also warn about unpaired files.
    orig_only = sorted(originals.keys() - reordered.keys())
    reor_only = sorted(reordered.keys() - originals.keys())
    for name in orig_only:
        print(f"  [warn] No reordered JSON found for '{name}' – skipped.")
    for name in reor_only:
        print(f"  [warn] No original JSON found for  '{name}' – skipped.")

    pairs = []
    for name in programs:
        orig_data = load_json(originals[name])
        reor_data = load_json(reordered[name])
        if orig_data is None or reor_data is None:
            continue

        om = extract_metrics(orig_data)
        rm = extract_metrics(reor_data)

        def pct_delta(orig_val, reor_val, lower_is_better=True):
            """Positive = improvement (toward the desired direction)."""
            if orig_val is None or reor_val is None or orig_val == 0:
                return None
            delta = (orig_val - reor_val) / orig_val * 100.0
            return delta if lower_is_better else -delta

        cycles_saved  = None if (om["cycles"] is None or rm["cycles"] is None) \
                        else int(om["cycles"]) - int(rm["cycles"])
        stalls_saved  = None if (om["stalls"] is None or rm["stalls"] is None) \
                        else int(om["stalls"]) - int(rm["stalls"])

        pairs.append({
            "program":           name,
            # ── original ──
            "orig_cycles":       om["cycles"],
            "orig_instructions": om["instructions"],
            "orig_cpi":          om["cpi"],
            "orig_ipc":          om["ipc"],
            "orig_stalls":       om["stalls"],
            "orig_stall_rate":   om["stall_rate"],
            "orig_efficiency":   om["efficiency"],
            # ── reordered ──
            "reor_cycles":       rm["cycles"],
            "reor_instructions": rm["instructions"],
            "reor_cpi":          rm["cpi"],
            "reor_ipc":          rm["ipc"],
            "reor_stalls":       rm["stalls"],
            "reor_stall_rate":   rm["stall_rate"],
            "reor_efficiency":   rm["efficiency"],
            # ── deltas ──
            "cycles_saved":          cycles_saved,
            "stalls_saved":          stalls_saved,
            "pct_cycle_improvement": pct_delta(om["cycles"],    rm["cycles"]),
            "pct_cpi_improvement":   pct_delta(om["cpi"],       rm["cpi"]),
            "pct_stall_improvement": pct_delta(om["stalls"],    rm["stalls"]),
            "pct_ipc_improvement":   pct_delta(om["ipc"],       rm["ipc"],
                                               lower_is_better=False),
            # ── meta ──
            "processor":   om["processor"] or rm["processor"],
        })

    return pairs


# ── Console output ────────────────────────────────────────────────────────────

def _fmt(val, fmt_spec="", fallback="n/a"):
    if val is None:
        return fallback
    return format(val, fmt_spec)


def print_analysis(pairs: list[dict]) -> None:
    divider = "=" * 92

    print("\n" + divider)
    print(" ANALYSIS REPORT  —  original vs reordered  (RV32 5-stage pipeline)")
    print(divider)

    for p in pairs:
        print(f"\n  Program : {p['program']}   (processor: {p['processor']})")
        print(f"  {'Metric':<30}  {'Original':>12}  {'Reordered':>12}  {'Delta':>12}")
        print(f"  {'-'*30}  {'-'*12}  {'-'*12}  {'-'*12}")

        rows = [
            ("Cycles",           p["orig_cycles"],        p["reor_cycles"],
             f"{_fmt(p['pct_cycle_improvement'], '+.2f')}%"),
            ("Instructions ret.",p["orig_instructions"],  p["reor_instructions"],
             "—"),
            ("CPI",              _fmt(p["orig_cpi"],      ".4f"),
                                 _fmt(p["reor_cpi"],      ".4f"),
             f"{_fmt(p['pct_cpi_improvement'], '+.2f')}%"),
            ("IPC",              _fmt(p["orig_ipc"],      ".4f"),
                                 _fmt(p["reor_ipc"],      ".4f"),
             f"{_fmt(p['pct_ipc_improvement'], '+.2f')}%"),
            ("Stall cycles",     p["orig_stalls"],        p["reor_stalls"],
             _fmt(p["stalls_saved"], "+d") if p["stalls_saved"] is not None else "n/a"),
            ("Stalls / instr.",  _fmt(p["orig_stall_rate"],".4f"),
                                 _fmt(p["reor_stall_rate"],".4f"),
             f"{_fmt(p['pct_stall_improvement'], '+.2f')}%"),
        ]
        for label, orig, reor, delta in rows:
            print(f"  {label:<30}  {str(orig):>12}  {str(reor):>12}  {str(delta):>12}")

    # ── Summary ───────────────────────────────────────────────────────────────
    valid_pct = [p["pct_cycle_improvement"] for p in pairs
                 if p["pct_cycle_improvement"] is not None]
    if valid_pct:
        avg   = sum(valid_pct) / len(valid_pct)
        best  = max(valid_pct)
        worst = min(valid_pct)
        best_prog  = pairs[valid_pct.index(best)]["program"]
        worst_prog = pairs[valid_pct.index(worst)]["program"]

        print(f"\n{divider}")
        print(" SUMMARY")
        print(f"{divider}")
        print(f"  Programs analysed         : {len(pairs)}")
        print(f"  Avg cycle improvement     : {avg:+.2f}%")
        print(f"  Best  cycle improvement   : {best:+.2f}%  ({best_prog})")
        print(f"  Worst cycle improvement   : {worst:+.2f}%  ({worst_prog})")

        total_stalls_saved = sum(
            p["stalls_saved"] for p in pairs if p["stalls_saved"] is not None
        )
        print(f"  Total stall cycles saved  : {total_stalls_saved}")
    print(divider + "\n")


# ── CSV export ────────────────────────────────────────────────────────────────

_CSV_FIELDS = [
    "program", "processor",
    # original
    "orig_cycles", "orig_instructions", "orig_cpi", "orig_ipc",
    "orig_stalls", "orig_stall_rate", "orig_efficiency",
    # reordered
    "reor_cycles", "reor_instructions", "reor_cpi", "reor_ipc",
    "reor_stalls", "reor_stall_rate", "reor_efficiency",
    # deltas
    "cycles_saved", "stalls_saved",
    "pct_cycle_improvement", "pct_cpi_improvement",
    "pct_stall_improvement", "pct_ipc_improvement",
]


def _round(val, ndigits=6):
    if isinstance(val, float):
        return round(val, ndigits)
    return val


def write_csv(pairs: list[dict]) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    with open(CSV_PATH, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=_CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for p in pairs:
            writer.writerow({k: _round(p.get(k)) for k in _CSV_FIELDS})

    print(f"  Analysis CSV written to: {CSV_PATH.relative_to(ROOT)}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    if not RESULTS_DIR.exists():
        print("[error] results/ directory not found.")
        print("        Run  python run_benchmarks.py  first to generate JSON outputs.")
        return

    json_count = len(list(RESULTS_DIR.glob("*.json")))
    print(f"Found {json_count} JSON file(s) in {RESULTS_DIR.relative_to(ROOT)}/")

    pairs = collect_pairs()
    if not pairs:
        print("[error] No matching original/reordered JSON pairs found.")
        return

    print_analysis(pairs)
    write_csv(pairs)


if __name__ == "__main__":
    main()
