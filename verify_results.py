#!/usr/bin/env python3
"""verify_results.py – compare registers in Ripes JSON outputs.

Reads every *_original.json / *_reordered.json pair from the results directory,
and verifies that the final register states match exactly.
This ensures the reordered programs maintain semantic correctness.

Usage (run from the project root):
    python verify_results.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent

# ── JSON loading ─────────────────────────────────────────────────────────────

def load_json(path: Path) -> dict:
    try:
        raw = path.read_text(encoding="utf-8")
        json_start = raw.find("{")
        if json_start == -1:
            return {}
        return json.loads(raw[json_start:])
    except (OSError, json.JSONDecodeError) as exc:
        print(f"  [warn] Cannot read {path.name}: {exc}")
        return {}

def extract_registers(data: dict) -> dict:
    """Extracts the final register states from a Ripes JSON result."""
    return data.get("registers", {})


def verify_pairs(results_dir: Path, suffix: str = "") -> list:
    originals = {p.stem.removesuffix(f"_original{suffix}"): p
                 for p in results_dir.glob(f"*_original{suffix}.json")}
    reordered = {p.stem.removesuffix(f"_reordered{suffix}"): p
                 for p in results_dir.glob(f"*_reordered{suffix}.json")}

    programs = sorted(originals.keys() & reordered.keys())

    if not programs:
        return []

    results = []
    
    for name in programs:
        orig_data = load_json(originals[name])
        reor_data = load_json(reordered[name])
        
        if not orig_data or not reor_data:
            continue

        orig_regs = extract_registers(orig_data)
        reor_regs = extract_registers(reor_data)
        
        matches = orig_regs == reor_regs
        diff = {}
        if not matches:
            all_keys = set(orig_regs.keys()) | set(reor_regs.keys())
            for k in all_keys:
                o_val = orig_regs.get(k)
                r_val = reor_regs.get(k)
                if o_val != r_val:
                    diff[k] = {"original": o_val, "reordered": r_val}

        results.append({
            "program": name,
            "matches": matches,
            "diff": diff
        })

    return results

def print_verification(results: list, label: str):
    print(f"\n=======================================================")
    print(f" VERIFICATION REPORT - {label}")
    print(f"=======================================================")
    
    all_match = True
    
    for res in results:
        status = "MATCH" if res['matches'] else "MISMATCH"
        print(f"  Program : {res['program']:<30} [{status}]")
        
        if not res['matches']:
            all_match = False
            print(f"    Differences:")
            for reg, vals in res['diff'].items():
                print(f"      {reg}: Original={vals['original']}, Reordered={vals['reordered']}")
                
    print(f"  -----------------------------------------------------")
    if all_match:
        print("  ✅ All programs matched successfully!")
    else:
        print("  ❌ Some programs had mismatched register states.")
    print(f"=======================================================\n")


def main(results_dirs: list[Path] = None) -> None:
    if results_dirs is None:
        # Check both test1 and test2 if they exist, or just use general results
        results_dirs = [ROOT / "results", ROOT / "test1" / "results", ROOT / "test2" / "results"]
        results_dirs = [d for d in results_dirs if d.exists()]

    if not results_dirs:
        print("[error] Cannot find any results/ directory.")
        print("        Run  python run_benchmarks.py  first to generate JSON outputs.")
        return

    for results_dir in results_dirs:
        print(f"\nChecking directory: {results_dir}")
        json_count = len(list(results_dir.glob("*.json")))
        if json_count == 0:
            print("  No JSON files found.")
            continue
            
        # Verify forwarding results
        pairs_fw = verify_pairs(results_dir, suffix="")
        if pairs_fw:
            print_verification(pairs_fw, "Forwarding Enabled")
            
        # Verify no-forwarding results
        pairs_nofw = verify_pairs(results_dir, suffix="_no_fw")
        if pairs_nofw:
            print_verification(pairs_nofw, "No Forwarding")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", nargs="?", type=Path, default=None,
                        help="Base folder containing a 'results' directory (e.g., test2)")
    parser.add_argument("--tests-dir", type=Path, default=None, help="Ignored")
    parser.add_argument("--reordered-dir", type=Path, default=None, help="Ignored")
    parser.add_argument("--results-dir", type=Path, default=None, 
                        help="Path to the results directory to verify")
    args, unknown = parser.parse_known_args()
    
    if args.folder:
        main([args.folder / "results"])
    elif args.results_dir:
        main([args.results_dir])
    else:
        main()
