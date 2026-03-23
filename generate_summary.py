#!/usr/bin/env python3
"""generate_summary.py

Read forwarding and no-forwarding analysis CSVs and produce a
single final_summary.json containing aggregated and per-test metrics.

Usage:
    python generate_summary.py <test_folder>

Writes: <test_folder>/results/final_summary.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


def _read_csv_if_exists(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    try:
        return pd.read_csv(path)
    except Exception:
        return None


def _first_existing_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    # try case-insensitive match
    cols = {col.lower(): col for col in df.columns}
    for c in candidates:
        if c.lower() in cols:
            return cols[c.lower()]
    return None


def safe_sum(series: pd.Series | None) -> float:
    if series is None:
        return 0.0
    try:
        return float(series.fillna(0).astype(float).sum())
    except Exception:
        return 0.0


def safe_mean(seq: list[float]) -> float:
    if not seq:
        return 0.0
    return float(sum(seq) / len(seq))


def round_val(v: Any) -> Any:
    if isinstance(v, (float, int)):
        try:
            return round(float(v), 3)
        except Exception:
            return v
    return v


def _summarize_prefix(df: pd.DataFrame, prefix: str) -> dict:
    """Summarize dataframe using a column prefix (orig or reor).

    Falls back to generic column names if prefixed ones are not present.
    """
    cycles_col = _first_existing_col(df, [f"{prefix}_cycles", "cycles", f"{prefix}_cycle", "orig_cycles"])
    instr_col = _first_existing_col(df, [f"{prefix}_instructions", "instructions", f"{prefix}_instr", "orig_instructions"])
    cpi_col = _first_existing_col(df, [f"{prefix}_cpi", "cpi"])
    stalls_col = _first_existing_col(df, [f"{prefix}_stalls", "stalls", f"{prefix}_stall_cycles"])

    total_cycles = safe_sum(df[cycles_col]) if cycles_col else 0.0
    total_instructions = safe_sum(df[instr_col]) if instr_col else 0.0

    if cpi_col:
        try:
            per_cpi = df[cpi_col].astype(float).fillna(0)
            if instr_col and total_instructions > 0:
                weighted = (per_cpi * df[instr_col].astype(float).fillna(0)).sum()
                cpi = weighted / total_instructions if total_instructions else 0.0
            else:
                cpi = float(per_cpi.mean()) if not per_cpi.empty else 0.0
        except Exception:
            cpi = (total_cycles / total_instructions) if total_instructions else 0.0
    else:
        cpi = (total_cycles / total_instructions) if total_instructions else 0.0

    total_stall_cycles = safe_sum(df[stalls_col]) if stalls_col else 0.0
    total_stalls = 0
    if stalls_col:
        try:
            total_stalls = int((df[stalls_col].astype(float).fillna(0) > 0).sum())
        except Exception:
            total_stalls = 0

    useful_cycles = total_cycles - total_stall_cycles
    pipeline_efficiency = (useful_cycles / total_cycles) if total_cycles else 0.0

    return {
        "total_cycles": round_val(total_cycles),
        "total_instructions": round_val(total_instructions),
        "cpi": round_val(cpi),
        "total_stall_cycles": round_val(total_stall_cycles),
        "total_stalls": round_val(total_stalls),
        "useful_cycles": round_val(useful_cycles),
        "pipeline_efficiency": round_val(pipeline_efficiency),
    }


def build_per_test(df_fw: pd.DataFrame | None, df_nofw: pd.DataFrame | None) -> list[dict]:
    prog_set = set()
    if df_fw is not None:
        prog_set.update(df_fw["program"].astype(str).tolist())
    if df_nofw is not None:
        prog_set.update(df_nofw["program"].astype(str).tolist())

    prog_list = sorted(prog_set)
    per_test = []
    for p in prog_list:
        row_fw = None
        row_nofw = None
        if df_fw is not None:
            sub = df_fw[df_fw["program"].astype(str) == p]
            if not sub.empty:
                row_fw = sub.iloc[0].to_dict()
        if df_nofw is not None:
            sub = df_nofw[df_nofw["program"].astype(str) == p]
            if not sub.empty:
                row_nofw = sub.iloc[0].to_dict()

        def pick(row, keys):
            if row is None:
                return None
            for k in keys:
                if k in row:
                    try:
                        return float(row[k])
                    except Exception:
                        try:
                            return float(str(row[k]).strip())
                        except Exception:
                            return None
            return None

        cycles_fw = pick(row_fw, ["reor_cycles", "orig_cycles", "cycles"]) or 0.0
        cycles_nofw = pick(row_nofw, ["reor_cycles", "orig_cycles", "cycles"]) or 0.0
        instr_fw = pick(row_fw, ["reor_instructions", "orig_instructions", "instructions"]) or 0.0
        instr_nofw = pick(row_nofw, ["reor_instructions", "orig_instructions", "instructions"]) or 0.0

        cpi_fw = pick(row_fw, ["reor_cpi", "orig_cpi", "cpi"]) or (cycles_fw / instr_fw if instr_fw else 0.0)
        cpi_nofw = pick(row_nofw, ["reor_cpi", "orig_cpi", "cpi"]) or (cycles_nofw / instr_nofw if instr_nofw else 0.0)

        stalls_fw = pick(row_fw, ["reor_stalls", "orig_stalls", "stalls"]) or 0.0
        stalls_nofw = pick(row_nofw, ["reor_stalls", "orig_stalls", "stalls"]) or 0.0

        raw_h = int(pick(row_fw, ["raw_hazards"]) or pick(row_nofw, ["raw_hazards"]) or 0)

        # speedup per test: ratio of CPI_no_fw / CPI_fw (guard zeros)
        if cpi_fw and cpi_nofw:
            speedup = cpi_nofw / cpi_fw if cpi_fw else 0.0
        else:
            # fallback to cycles ratio if CPI not available
            speedup = (cycles_nofw / cycles_fw) if (cycles_fw and cycles_nofw) else 0.0

        per_test.append({
            "name": p,
            "cycles_forwarding": round_val(cycles_fw),
            "cycles_no_forwarding": round_val(cycles_nofw),
            "cpi_forwarding": round_val(cpi_fw),
            "cpi_no_forwarding": round_val(cpi_nofw),
            "stalls_forwarding": round_val(stalls_fw),
            "stalls_no_forwarding": round_val(stalls_nofw),
            "raw_hazards": round_val(raw_h),
            "speedup": round_val(speedup),
        })

    return per_test


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", nargs="?", default=".", help="test folder containing results/")
    args = parser.parse_args()

    folder = Path(args.folder).resolve()
    results = folder / "results"
    if not results.exists():
        print(f"Results directory not found: {results}")
        return 2

    csv_fw = results / "analysis.csv"
    csv_no_fw = results / "analysis_no_fw.csv"

    df_fw = _read_csv_if_exists(csv_fw)
    df_nofw = _read_csv_if_exists(csv_no_fw)

    if df_fw is None and df_nofw is None:
        print("No analysis CSVs found; expected analysis.csv or analysis_no_fw.csv")
        return 3

    # (previous summarize_df removed) datasets will be processed below

    # New prioritization: instruction reordering (original vs reordered)
    # Collect available datasets (forwarding / no_forwarding labeled by filename)
    datasets: dict[str, pd.DataFrame] = {}
    if df_fw is not None:
        datasets["forwarding"] = df_fw
    if df_nofw is not None:
        datasets["no_forwarding"] = df_nofw

    # For each dataset compute 'orig' and 'reor' summaries (if columns exist)
    original_group = {}
    reordered_group = {}

    # Aggregates across datasets
    agg_orig_cycles = 0.0
    agg_orig_instr = 0.0
    agg_orig_stalls = 0.0

    agg_reor_cycles = 0.0
    agg_reor_instr = 0.0
    agg_reor_stalls = 0.0

    for hw_key, df in datasets.items():
        # if df contains prefixed columns like orig_ / reor_, use them
        orig_summary = _summarize_prefix(df, "orig")
        reor_summary = _summarize_prefix(df, "reor")

        original_group[hw_key] = orig_summary
        reordered_group[hw_key] = reor_summary

        agg_orig_cycles += float(orig_summary.get("total_cycles", 0) or 0)
        agg_orig_instr += float(orig_summary.get("total_instructions", 0) or 0)
        agg_orig_stalls += float(orig_summary.get("total_stall_cycles", 0) or 0)

        agg_reor_cycles += float(reor_summary.get("total_cycles", 0) or 0)
        agg_reor_instr += float(reor_summary.get("total_instructions", 0) or 0)
        agg_reor_stalls += float(reor_summary.get("total_stall_cycles", 0) or 0)

    # If no datasets (shouldn't happen), fall back to single-file summaries
    if not datasets and df_fw is not None:
        original_group["default"] = _summarize_prefix(df_fw, "orig")
        reordered_group["default"] = _summarize_prefix(df_fw, "reor")

    # Compute aggregated top-level original/reordered summaries
    def _agg_summary(cycles, instr, stalls):
        useful = cycles - stalls
        eff = (useful / cycles) if cycles else 0.0
        cpi = (cycles / instr) if instr else 0.0
        return {"cpi": round_val(cpi), "total_stall_cycles": round_val(stalls), "pipeline_efficiency": round_val(eff),
                "total_cycles": round_val(cycles), "total_instructions": round_val(instr)}

    orig_agg = _agg_summary(agg_orig_cycles, agg_orig_instr, agg_orig_stalls)
    reor_agg = _agg_summary(agg_reor_cycles, agg_reor_instr, agg_reor_stalls)

    # Reordering impact (main): compare aggregated original vs reordered
    cycles_saved = round_val((agg_orig_cycles - agg_reor_cycles) if (agg_orig_cycles and agg_reor_cycles) else (agg_orig_cycles - agg_reor_cycles))
    cpi_reduction_percent = ((orig_agg["cpi"] - reor_agg["cpi"]) / orig_agg["cpi"] * 100.0) if orig_agg["cpi"] else 0.0
    stall_reduction_percent = ((orig_agg["total_stall_cycles"] - reor_agg["total_stall_cycles"]) / orig_agg["total_stall_cycles"] * 100.0) if orig_agg["total_stall_cycles"] else 0.0
    efficiency_improvement = round_val(reor_agg.get("pipeline_efficiency", 0.0) - orig_agg.get("pipeline_efficiency", 0.0))

    # Per-test reordering analysis: prefer forwarding dataset if present, else any
    preferred_df = datasets.get("forwarding") if "forwarding" in datasets else (next(iter(datasets.values()), None) if datasets else None)
    per_test = []
    if preferred_df is not None:
        programs = preferred_df["program"].astype(str).tolist()
        for i, row in preferred_df.iterrows():
            name = str(row.get("program", ""))
            # pick per-row values
            def pick_row(r, keys):
                for k in keys:
                    if k in r and pd.notna(r[k]):
                        try:
                            return float(r[k])
                        except Exception:
                            try:
                                return float(str(r[k]).strip())
                            except Exception:
                                return 0.0
                return 0.0

            cpi_orig = pick_row(row, ["orig_cpi", "cpi"]) or (pick_row(row, ["orig_cycles"]) / pick_row(row, ["orig_instructions"]) if pick_row(row, ["orig_instructions"]) else 0.0)
            cpi_reor = pick_row(row, ["reor_cpi"]) or (pick_row(row, ["reor_cycles"]) / pick_row(row, ["reor_instructions"]) if pick_row(row, ["reor_instructions"]) else 0.0)
            stalls_orig = pick_row(row, ["orig_stalls"]) or 0.0
            stalls_reor = pick_row(row, ["reor_stalls"]) or 0.0

            speedup = (cpi_orig / cpi_reor) if (cpi_reor and cpi_orig) else ( (pick_row(row,["orig_cycles"]) / pick_row(row,["reor_cycles"])) if (pick_row(row,["orig_cycles"]) and pick_row(row,["reor_cycles"])) else 0.0)
            stall_reduction = ((stalls_orig - stalls_reor) / stalls_orig * 100.0) if stalls_orig else 0.0

            per_test.append({
                "name": name,
                "cpi_original": round_val(cpi_orig),
                "cpi_reordered": round_val(cpi_reor),
                "stalls_original": round_val(stalls_orig),
                "stalls_reordered": round_val(stalls_reor),
                "speedup_due_to_reordering": round_val(speedup),
                "stall_reduction_percent": round_val(stall_reduction),
            })

    # Summary statistics
    speedups = [pt.get("speedup_due_to_reordering", 0.0) for pt in per_test if isinstance(pt.get("speedup_due_to_reordering"), (int, float))]
    avg_cpi_original = round_val(safe_mean([pt.get("cpi_original",0.0) for pt in per_test]))
    avg_cpi_reordered = round_val(safe_mean([pt.get("cpi_reordered",0.0) for pt in per_test]))
    avg_speedup = round_val(safe_mean(speedups))
    max_speed = round_val(max(speedups) if speedups else 0.0)
    min_speed = round_val(min(speedups) if speedups else 0.0)

    # Optional forwarding effect (secondary)
    forwarding_effect = {"included": False, "speedup": 0.0, "cpi_reduction_percent": 0.0}
    if "forwarding" in datasets and "no_forwarding" in datasets:
        # compare aggregated reordered CPI between forwarding and no_forwarding if available
        f_reor = _summarize_prefix(datasets["forwarding"], "reor")
        nf_reor = _summarize_prefix(datasets["no_forwarding"], "reor")
        cpi_f = f_reor.get("cpi", 0.0)
        cpi_nf = nf_reor.get("cpi", 0.0)
        if cpi_f and cpi_nf:
            forwarding_effect = {
                "included": True,
                "speedup": round_val((cpi_nf / cpi_f) if cpi_f else 0.0),
                "cpi_reduction_percent": round_val(((cpi_nf - cpi_f) / cpi_nf * 100.0) if cpi_nf else 0.0),
            }

    out = {
        "original": {"by_hw": original_group},
        "reordered": {"by_hw": reordered_group},
        "reordering_impact": {
            "cpi_reduction_percent": round_val(cpi_reduction_percent),
            "stall_reduction_percent": round_val(stall_reduction_percent),
            "efficiency_improvement": efficiency_improvement,
            "cycles_saved": cycles_saved,
        },
        "per_test": per_test,
        "summary_stats": {
            "avg_cpi_original": avg_cpi_original,
            "avg_cpi_reordered": avg_cpi_reordered,
            "avg_speedup": avg_speedup,
            "max_speedup": max_speed,
            "min_speedup": min_speed,
        },
        "forwarding_effect": forwarding_effect,
    }

    summary_dir = results / "summary"
    summary_dir.mkdir(parents=True, exist_ok=True)
    outpath = summary_dir / "final_summary.json"
    with outpath.open("w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)

    # Print a brief formatted summary
    print("Wrote summary to:", outpath)
    top_summary = {
        "cycles_saved": out["reordering_impact"].get("cycles_saved"),
        "reordering_impact": out["reordering_impact"],
        "summary_stats": out["summary_stats"],
    }
    print("Summary (top-level):")
    print(json.dumps(top_summary, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
