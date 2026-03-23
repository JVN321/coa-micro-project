#!/usr/bin/env python3
"""run_benchmarks.py – simulate original and reordered programs with Ripes CLI
and produce a side-by-side performance comparison.

Workflow
--------
1. Run every *.s in tests/         → results/<stem>_original.json
2. Run every *.s in reordered_tests/→ results/<stem>_reordered.json
3. Parse JSON metrics from each run.
4. Print a formatted comparison table.
5. Write results/benchmark_summary.csv.

Usage (run from the project root):
    python run_benchmarks.py

Prerequisites
-------------
* Ripes CLI installed at RIPES_EXE (adjust if needed).
* reorder_all.py must have been executed beforehand so that reordered_tests/
  contains the reordered versions.
"""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load .env from the project root (same directory as this script).
load_dotenv(Path(__file__).resolve().parent / ".env")

# ── Configuration ─────────────────────────────────────────────────────────────
# Set RIPES_EXE in your .env file (see .env.example).
RIPES_EXE = os.getenv("RIPES_EXE", "")
if not RIPES_EXE:
    raise EnvironmentError(
        "RIPES_EXE is not set.\n"
        "Copy .env.example to .env and fill in the path to your Ripes executable."
    )

# You can specify the processor model via RIPES_PROC in your .env file.
# By default, "RV32_5S" (with forwarding) is used. Use "RV32_5S_NO_FW" for no forwarding.
RIPES_PROC = os.getenv("RIPES_PROC", "RV32_5S")
# No-forwarding processor identifier (override via .env if desired)
RIPES_PROC_NOFW = os.getenv("RIPES_PROC_NOFW", "RV32_5S_NO_FW")

RIPES_BASE_ARGS = [
    "--mode", "cli",
    "-t", "asm",
    "--json",
    "--all",
]

# ── Paths (all relative to the project root) ─────────────────────────────────
ROOT = Path(__file__).resolve().parent
# Default directories – overridden by CLI args when called from run.py
# ─────────────────────────────────────────────────────────────────────────────


# ── Ripes runner ──────────────────────────────────────────────────────────────

def run_ripes(asm_file: Path, out_json: Path, proc: str) -> bool:
    """Invoke Ripes CLI on *asm_file* and save the raw JSON to *out_json*.

    Returns True on success, False on failure.

    Note: Ripes CLI uses ``--src`` to specify the assembly source file.
    Adjust the flag to ``-f`` or ``--file`` if your build requires it.
    """
    cmd = [RIPES_EXE] + RIPES_BASE_ARGS + ["--proc", proc, "--src", str(asm_file)]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,  # 2-minute safety timeout per simulation
        )
    except FileNotFoundError:
        print(f"  [error] Ripes executable not found: {RIPES_EXE}")
        print("          Update RIPES_EXE in run_benchmarks.py to the correct path.")
        return False
    except subprocess.TimeoutExpired:
        print(f"  [error] Ripes timed out on {asm_file.name}")
        return False

    if result.returncode != 0:
        snippet = (result.stderr or result.stdout).strip()[:300]
        print(f"  [error] Ripes returned exit code {result.returncode}")
        if snippet:
            print(f"          {snippet}")
        return False

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(result.stdout, encoding="utf-8")
    return True


# ── JSON metric extraction ─────────────────────────────────────────────────────

def _search(obj: object, *keys: str) -> Optional[float]:
    """Recursively search *obj* for the first key that matches any of *keys*.

    Ripes has changed its JSON schema between releases; this helper tolerates
    different nesting levels and key name variations.
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.lower() in keys:
                try:
                    return float(v)
                except (TypeError, ValueError):
                    pass
            found = _search(v, *keys)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = _search(item, *keys)
            if found is not None:
                return found
    return None


def extract_metrics(json_path: Path) -> dict:
    """Return a dict with keys: cycles, instructions, ipc, cpi."""
    try:
        raw = json_path.read_text(encoding="utf-8")
        # Ripes CLI prepends "Program exited with code: N\r\n" before the JSON.
        json_start = raw.find("{")
        if json_start == -1:
            raise json.JSONDecodeError("No JSON object found", raw, 0)
        data = json.loads(raw[json_start:])
    except (json.JSONDecodeError, OSError) as exc:
        print(f"  [warn] Cannot parse {json_path.name}: {exc}")
        return {"cycles": None, "instructions": None, "ipc": None, "cpi": None}

    cycles = _search(data, "cycles")
    instructions = _search(
        data,
        "instructionsretired", "instructions_retired",
        "instructions", "instruction_count",
    )
    ipc = _search(data, "ipc")
    cpi = _search(data, "cpi")

    # Derive missing metrics where possible.
    if ipc is None and cycles and instructions and instructions > 0:
        ipc = instructions / cycles
    if cpi is None and cycles and instructions and instructions > 0:
        cpi = cycles / instructions

    return {"cycles": cycles, "instructions": instructions, "ipc": ipc, "cpi": cpi}


# ── Comparison helpers ────────────────────────────────────────────────────────

def pct_improvement(original: float, reordered: float) -> float:
    """Percentage cycle reduction: positive means fewer cycles after reordering."""
    if original == 0:
        return 0.0
    return (original - reordered) / original * 100.0


# ── Table formatting ──────────────────────────────────────────────────────────

_COL_WIDTHS = [22, 13, 17, 15, 11, 14]
_HEADERS    = ["Program", "Orig Cycles", "Reordered Cycles",
               "% Improvement", "IPC Orig", "IPC Reordered"]


def _sep() -> str:
    return "+" + "+".join("-" * w for w in _COL_WIDTHS) + "+"


def _row(cells: list) -> str:
    parts = []
    for cell, width in zip(cells, _COL_WIDTHS):
        text = str(cell)
        parts.append(f" {text:<{width - 2}} ")
    return "|" + "|".join(parts) + "|"

# ── Main ──────────────────────────────────────────────────────────────────────

def main(tests_dir: Path = None, reordered_dir: Path = None,
         results_dir: Path = None) -> None:

    tests_dir     = tests_dir     or (ROOT / "tests")
    reordered_dir = reordered_dir or (ROOT / "reordered_tests")
    results_dir   = results_dir   or (ROOT / "results")

    results_dir.mkdir(parents=True, exist_ok=True)

    asm_files = sorted(tests_dir.glob("*.s"))
    if not asm_files:
        print(f"[warn] No .s files found in {tests_dir}/")
        return

    rows: list[dict] = []

    # ── Step 1 & 2: simulate original and reordered files ────────────────────
    for src in asm_files:
        stem = src.stem
        print(f"\n{'─' * 60}")
        print(f"  Program : {stem}")

        # --- original ---
        # forward-enabled (default) output keeps the original filenames for
        # backwards compatibility (e.g. <stem>_original.json).
        orig_json = results_dir / f"{stem}_original.json"
        print(f"  [1/4] Running original (with forwarding)  …", end=" ", flush=True)
        ok_orig_fw = run_ripes(src, orig_json, RIPES_PROC)
        print("done" if ok_orig_fw else "FAILED")

        # no-forwarding output gets a distinct suffix so it can be analysed
        # separately (e.g. <stem>_original_no_fw.json).
        orig_json_nofw = results_dir / f"{stem}_original_no_fw.json"
        print(f"  [2/4] Running original (no forwarding)   …", end=" ", flush=True)
        ok_orig_nofw = run_ripes(src, orig_json_nofw, RIPES_PROC_NOFW)
        print("done" if ok_orig_nofw else "FAILED")

        # --- reordered ---
        reordered_src  = reordered_dir / f"{stem}_reordered.s"
        reordered_json = results_dir   / f"{stem}_reordered.json"

        if not reordered_src.exists():
            print(f"  [warn] Reordered file not found ({reordered_src.name}).")
            print("         Run  python reorder_all.py  first.")
            continue

        print(f"  [3/4] Running reordered (with forwarding)  …", end=" ", flush=True)
        ok_reordered_fw = run_ripes(reordered_src, reordered_json, RIPES_PROC)
        print("done" if ok_reordered_fw else "FAILED")

        reordered_json_nofw = results_dir / f"{stem}_reordered_no_fw.json"
        print(f"  [4/4] Running reordered (no forwarding)   …", end=" ", flush=True)
        ok_reordered_nofw = run_ripes(reordered_src, reordered_json_nofw, RIPES_PROC_NOFW)
        print("done" if ok_reordered_nofw else "FAILED")

        # For the remainder of the script keep the original behaviour and
        # proceed if the forward-enabled runs succeeded. The no-forwarding
        # results are still written above and will be analysed separately.
        if not (ok_orig_fw and ok_reordered_fw):
            print(f"  [skip] Skipping {stem} — simulation error(s) above.")
            continue

        # ── Step 3: extract metrics ───────────────────────────────────────────
        orig_m  = extract_metrics(orig_json)
        reord_m = extract_metrics(reordered_json)

        orig_cycles  = orig_m["cycles"]
        reord_cycles = reord_m["cycles"]

        if orig_cycles is None or reord_cycles is None:
            print(f"  [warn] Could not extract cycle count for {stem}; skipping.")
            continue

        # ── Step 4: compute improvement ───────────────────────────────────────
        pct = pct_improvement(orig_cycles, reord_cycles)

        rows.append({
            "program":               stem,
            "orig_cycles":           orig_cycles,
            "reordered_cycles":      reord_cycles,
            "pct_improvement":       pct,
            "ipc_orig":              orig_m["ipc"],
            "ipc_reordered":         reord_m["ipc"],
            "cpi_orig":              orig_m["cpi"],
            "cpi_reordered":         reord_m["cpi"],
            "instructions_orig":     orig_m["instructions"],
            "instructions_reordered": reord_m["instructions"],
        })

    if not rows:
        print("\n[info] No comparable results — nothing to report.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--tests-dir",     type=Path, default=None)
    parser.add_argument("--reordered-dir", type=Path, default=None)
    parser.add_argument("--results-dir",   type=Path, default=None)
    args = parser.parse_args()
    main(args.tests_dir, args.reordered_dir, args.results_dir)
