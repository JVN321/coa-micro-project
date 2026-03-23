#!/usr/bin/env python3
"""build_graphs.py

Generate comparison graphs from a test folder's `results/analysis.csv`.

Usage:
    python build_graphs.py <test_folder>

If no folder is given the current directory is used. The script expects
`<test_folder>/results/analysis.csv` to exist. Output images are written to
`<test_folder>/results/graphs/` (created if needed).

Produces:
    - cycles_comparison.png   : original vs reordered cycles (primary)
    - cpi_comparison.png      : original vs reordered CPI
    - stalls_comparison.png   : original vs reordered stall counts
    - pct_cycles_improvement.png : percent cycle improvement (annotated with speedup)
    - stall_rate_comparison.png (optional) : original vs reordered stall rates if present
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import textwrap

try:
    import pandas as pd
    import matplotlib.pyplot as plt
except Exception as exc:  # pragma: no cover - runtime dependency handling
    print("Missing dependency: ensure pandas and matplotlib are installed.")
    print("pip install pandas matplotlib")
    raise

# Styling defaults: colorblind-friendly palette and grid
try:
    plt.style.use("seaborn-v0_8-colorblind")
except Exception:
    plt.style.use("seaborn-darkgrid")

# Default colors (blue/orange pair, high contrast)
COLOR_FW_ORIG = "#A1C9F4"    # Pastel Blue
COLOR_FW_REOR = "#8DE5A1"    # Pastel Green
COLOR_NOFW_ORIG = "#FFB482"  # Pastel Orange
COLOR_NOFW_REOR = "#FF9F9B"  # Pastel Red
COLOR_PRIMARY = COLOR_FW_ORIG
COLOR_SECOND = COLOR_FW_REOR
COLOR_ACCENT = "#D0BBFF"     # Pastel Purple

from riscv_parser import parse_assembly_lines, ParsedLine


def _format_int(value: int) -> str:
    try:
        return f"{value:,}"
    except Exception:
        return str(value)


def annotate_int_bars(ax, bars, offset_y=3, dx=0.0):
    for b in bars:  # type: ignore
        h = b.get_height()
        if h is None:
            continue
        try:
            hv = float(h)
        except Exception:
            continue
        if hv <= 0:
            continue
        x = b.get_x() + b.get_width() / 2 + dx
        txt = _format_int(int(hv))
        ax.annotate(txt, xy=(x, hv), xytext=(0, offset_y), textcoords="offset points",
                    ha="center", va="bottom", fontsize=10, clip_on=False)


def annotate_float_bars(ax, bars, offset_y=3, dx=0.0, precision=3):
    for b in bars:  # type: ignore
        h = b.get_height()
        if h is None:
            continue
        try:
            hv = float(h)
        except Exception:
            continue
        if hv <= 0:
            continue
        x = b.get_x() + b.get_width() / 2 + dx
        txt = f"{hv:.{precision}f}"
        ax.annotate(txt, xy=(x, hv), xytext=(0, offset_y), textcoords="offset points",
                    ha="center", va="bottom", fontsize=10, clip_on=False)


def _ensure_top_padding(ax, bars, pad=0.12):
    """Ensure the y-axis has some headroom so bar labels don't get cropped.

    bars may be a sequence (list) of BarContainer objects or a single BarContainer.
    """
    # flatten bars into a list of patches
    patches = []
    if bars is None:
        return
    try:
        for b in bars:
            # if bars is a list of BarContainer, extend
            try:
                patches.extend(list(b))
            except Exception:
                patches.append(b)
    except Exception:
        # bars may be a BarContainer
        try:
            patches = list(bars)
        except Exception:
            patches = []

    if not patches:
        return

    max_h = max((p.get_height() for p in patches), default=0)
    if max_h <= 0:
        return
    cur_bottom, cur_top = ax.get_ylim()
    desired_top = max(cur_top, max_h * (1.0 + pad))
    ax.set_ylim(cur_bottom := 0 if cur_bottom is None else 0, desired_top)


def read_analysis_csv(csv_path: Path) -> pd.DataFrame:
    return pd.read_csv(csv_path)


def ensure_graphs_dir(results_dir: Path) -> Path:
    graphs = results_dir / "graphs"
    graphs.mkdir(parents=True, exist_ok=True)
    return graphs


def plot_cycles(df: pd.DataFrame, outpath: Path) -> None:
    programs = df["program"].astype(str)
    label_names = [p.replace("_", "\n") for p in programs]
    orig = df["orig_cycles"].astype(float)
    reor = df["reor_cycles"].astype(float)

    x = range(len(programs))
    width = 0.35
    fig, ax = plt.subplots(figsize=(max(16, len(programs) * 3.0), 8), dpi=150)
    bars1 = ax.bar([i - width/2 for i in x], orig, width, label="Unordered", color=COLOR_FW_ORIG)
    bars2 = ax.bar([i + width/2 for i in x], reor, width, label="Reordered", color=COLOR_FW_REOR)
    ax.set_ylabel("Cycles")
    ax.set_title("Cycles Comparison — Original vs Reordered")
    ax.set_xticks(list(x))
    ax.set_xticklabels(label_names, rotation=0, ha="center", fontsize=10)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=2, frameon=False, fontsize=10)
    ax.grid(axis="y", alpha=0.25)
    # ensure some headroom so labels are not cropped
    _ensure_top_padding(ax, [bars1, bars2], pad=0.12)
    # annotate 
    annotate_int_bars(ax, bars1, offset_y=2)
    annotate_int_bars(ax, bars2, offset_y=2)
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.40)
    fig.savefig(outpath, transparent=True, bbox_inches="tight")
    plt.close(fig)


def plot_cpi(df: pd.DataFrame, outpath: Path) -> None:
    programs = df["program"].astype(str)
    label_names = [p.replace("_", "\n") for p in programs]
    orig = df["orig_cpi"].astype(float)
    reor = df["reor_cpi"].astype(float)

    x = range(len(programs))
    width = 0.35
    fig, ax = plt.subplots(figsize=(max(16, len(programs) * 3.0), 8), dpi=150)
    bars1 = ax.bar([i - width/2 for i in x], orig, width, label="Unordered", color=COLOR_FW_ORIG)
    bars2 = ax.bar([i + width/2 for i in x], reor, width, label="Reordered", color=COLOR_FW_REOR)
    ax.set_ylabel("CPI")
    ax.set_title("CPI Comparison — Original vs Reordered")
    ax.set_xticks(list(x))
    ax.set_xticklabels(label_names, rotation=0, ha="center", fontsize=10)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=2, frameon=False, fontsize=10)
    ax.grid(axis="y", alpha=0.25)
    _ensure_top_padding(ax, [bars1, bars2], pad=0.12)
    annotate_float_bars(ax, bars1, offset_y=2)
    annotate_float_bars(ax, bars2, offset_y=2)
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.35)
    fig.savefig(outpath, transparent=True, bbox_inches="tight")
    plt.close(fig)


def plot_stalls(df: pd.DataFrame, outpath: Path) -> None:
    programs = df["program"].astype(str)
    label_names = [p.replace("_", "\n") for p in programs]
    orig = df["orig_stalls"].astype(float)
    reor = df["reor_stalls"].astype(float)

    x = range(len(programs))
    width = 0.35
    fig, ax = plt.subplots(figsize=(max(16, len(programs) * 3.0), 8), dpi=150)
    bars1 = ax.bar([i - width/2 for i in x], orig, width, label="Unordered", color=COLOR_FW_ORIG)
    bars2 = ax.bar([i + width/2 for i in x], reor, width, label="Reordered", color=COLOR_FW_REOR)
    ax.set_ylabel("Stall cycles")
    ax.set_title("Stall Count Comparison — Original vs Reordered")
    ax.set_xticks(list(x))
    ax.set_xticklabels(label_names, rotation=0, ha="center", fontsize=10)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=2, frameon=False, fontsize=10)
    ax.grid(axis="y", alpha=0.25)
    _ensure_top_padding(ax, [bars1, bars2], pad=0.12)
    annotate_int_bars(ax, bars1, offset_y=2)
    annotate_int_bars(ax, bars2, offset_y=2)
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.35)
    fig.savefig(outpath, transparent=True, bbox_inches="tight")
    plt.close(fig)


def split_regions(parsed_lines: list[ParsedLine]) -> list[list[ParsedLine]]:
    regions = []
    cur = []
    for pl in parsed_lines:
        if pl.kind in ("label", "directive"):
            if cur:
                regions.append(cur)
                cur = []
            continue
        if pl.kind == "instruction" and pl.inst is not None:
            cur.append(pl)
            # barrier / control instruction ends region
            from riscv_parser import is_control_or_barrier
            if is_control_or_barrier(pl.inst):
                if cur:
                    regions.append(cur)
                cur = []
        else:
            # blank/comment/other - keep
            continue
    if cur:
        regions.append(cur)
    return regions


def count_hazards_in_lines(lines: list[str]) -> dict:
    parsed = parse_assembly_lines(lines)
    regions = split_regions(parsed)
    raw = 0
    war = 0
    waw = 0

    for region in regions:
        n = len(region)
        for i in range(n):
            inst_i = region[i].inst
            if inst_i is None:
                continue
            for j in range(i + 1, n):
                inst_j = region[j].inst
                if inst_j is None:
                    continue
                # For each register we ensure there is no intermediate writer
                # between i and j that overwrites the reg.
                # RAW: i writes, j reads
                for r in inst_i.writes & inst_j.reads:
                    intervening = any(r in region[k].inst.writes for k in range(i + 1, j)
                                      if region[k].inst)
                    if not intervening:
                        raw += 1
                # WAW: both write same reg
                for r in inst_i.writes & inst_j.writes:
                    intervening = any(r in region[k].inst.writes for k in range(i + 1, j)
                                      if region[k].inst)
                    if not intervening:
                        waw += 1
                # WAR: i reads, j writes
                for r in inst_i.reads & inst_j.writes:
                    intervening = any(r in region[k].inst.writes for k in range(i + 1, j)
                                      if region[k].inst)
                    if not intervening:
                        war += 1

    return {"RAW": raw, "WAR": war, "WAW": waw}


def find_asm_file(test_dir: Path, program: str, candidates: list[str]) -> Path | None:
    for c in candidates:
        p = test_dir / c.format(program=program)
        if p.exists():
            return p
    return None


def plot_hazards(programs: list[str], orig_counts: list[dict], reor_counts: list[dict], outpath: Path) -> None:
    # plot RAW primarily, stack optional WAR/WAW side table
    raws_orig = [c.get("RAW", 0) for c in orig_counts]
    raws_reor = [c.get("RAW", 0) for c in reor_counts]

    label_names = [p.replace("_", "\n") for p in programs]

    x = range(len(programs))
    width = 0.35
    fig, ax = plt.subplots(figsize=(max(16, len(programs) * 3.0), 8), dpi=150)
    bars1 = ax.bar([i - width/2 for i in x], raws_orig, width, label="Unordered RAW", color=COLOR_FW_ORIG)
    bars2 = ax.bar([i + width/2 for i in x], raws_reor, width, label="Reordered RAW", color=COLOR_FW_REOR)
    ax.set_ylabel("RAW hazard count (static)")
    ax.set_title("Data Hazard (RAW) — static count from assembly")
    ax.set_xticks(list(x))
    ax.set_xticklabels(label_names, rotation=0, ha="center", fontsize=10)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=2, frameon=False, fontsize=10)
    ax.grid(axis="y", alpha=0.25)
    _ensure_top_padding(ax, [bars1, bars2], pad=0.14)
    # annotate side-by-side
    annotate_int_bars(ax, bars1, offset_y=2)
    annotate_int_bars(ax, bars2, offset_y=2)
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.25)
    fig.savefig(outpath, transparent=True, bbox_inches="tight")
    plt.close(fig)


def _plot_combined_bars(programs, fw_orig, fw_reor, nofw_orig, nofw_reor,
                        outpath: Path, ylabel: str, title: str,
                        annotate_int: bool = True, precision: int = 3):
    label_names = [p.replace("_", "\n") for p in programs]
    x = range(len(programs))
    # four bars per group: fw_orig, fw_reor, nofw_orig, nofw_reor
    width = 0.22
    fig, ax = plt.subplots(figsize=(max(16, len(programs) * 3.0), 8), dpi=150)
    offs = [-1.5*width, -0.5*width, 0.5*width, 1.5*width]
    bars_fw_orig = ax.bar([i + offs[0] for i in x], fw_orig, width, label="Orig (fw)", color=COLOR_FW_ORIG)
    bars_fw_reor = ax.bar([i + offs[1] for i in x], fw_reor, width, label="Reor (fw)", color=COLOR_FW_REOR)
    bars_nofw_orig = ax.bar([i + offs[2] for i in x], nofw_orig, width, label="Orig (no-fw)", color=COLOR_NOFW_ORIG)
    bars_nofw_reor = ax.bar([i + offs[3] for i in x], nofw_reor, width, label="Reor (no-fw)", color=COLOR_NOFW_REOR)

    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.set_xticks(list(x))
    ax.set_xticklabels(label_names, rotation=0, ha="center", fontsize=10)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=4, frameon=False, fontsize=10)
    ax.grid(axis="y", alpha=0.25)
    _ensure_top_padding(ax, [bars_fw_orig, bars_fw_reor, bars_nofw_orig, bars_nofw_reor], pad=0.12)

    if annotate_int:
        annotate_int_bars(ax, bars_fw_orig, offset_y=2)
        annotate_int_bars(ax, bars_fw_reor, offset_y=2)
        annotate_int_bars(ax, bars_nofw_orig, offset_y=2)
        annotate_int_bars(ax, bars_nofw_reor, offset_y=2)
    else:
        annotate_float_bars(ax, bars_fw_orig, offset_y=2, precision=precision)
        annotate_float_bars(ax, bars_fw_reor, offset_y=2, precision=precision)
        annotate_float_bars(ax, bars_nofw_orig, offset_y=2, precision=precision)
        annotate_float_bars(ax, bars_nofw_reor, offset_y=2, precision=precision)

    fig.tight_layout()
    fig.subplots_adjust(bottom=0.45)
    fig.savefig(outpath, transparent=True, bbox_inches="tight")
    plt.close(fig)


def plot_combined_cycles(df_fw: pd.DataFrame, df_nofw: pd.DataFrame, outpath: Path) -> None:
    # align programs
    prog = sorted(set(df_fw['program'].astype(str)).union(df_nofw['program'].astype(str)))
    fw_map = {r['program']: r for _, r in df_fw.iterrows()}
    nofw_map = {r['program']: r for _, r in df_nofw.iterrows()}
    fw_orig = [float(fw_map.get(p, {}).get('orig_cycles', 0) or 0) for p in prog]
    fw_reor = [float(fw_map.get(p, {}).get('reor_cycles', 0) or 0) for p in prog]
    nofw_orig = [float(nofw_map.get(p, {}).get('orig_cycles', 0) or 0) for p in prog]
    nofw_reor = [float(nofw_map.get(p, {}).get('reor_cycles', 0) or 0) for p in prog]
    _plot_combined_bars(prog, fw_orig, fw_reor, nofw_orig, nofw_reor, outpath,
                        ylabel="Cycles", title="Cycles Comparison")


def plot_combined_cpi(df_fw: pd.DataFrame, df_nofw: pd.DataFrame, outpath: Path) -> None:
    prog = sorted(set(df_fw['program'].astype(str)).union(df_nofw['program'].astype(str)))
    fw_map = {r['program']: r for _, r in df_fw.iterrows()}
    nofw_map = {r['program']: r for _, r in df_nofw.iterrows()}
    fw_orig = [float(fw_map.get(p, {}).get('orig_cpi', 0) or 0) for p in prog]
    fw_reor = [float(fw_map.get(p, {}).get('reor_cpi', 0) or 0) for p in prog]
    nofw_orig = [float(nofw_map.get(p, {}).get('orig_cpi', 0) or 0) for p in prog]
    nofw_reor = [float(nofw_map.get(p, {}).get('reor_cpi', 0) or 0) for p in prog]
    _plot_combined_bars(prog, fw_orig, fw_reor, nofw_orig, nofw_reor, outpath,
                        ylabel="CPI", title="CPI comparison",
                        annotate_int=False, precision=4)


def plot_combined_stalls(df_fw: pd.DataFrame, df_nofw: pd.DataFrame, outpath: Path) -> None:
    prog = sorted(set(df_fw['program'].astype(str)).union(df_nofw['program'].astype(str)))
    fw_map = {r['program']: r for _, r in df_fw.iterrows()}
    nofw_map = {r['program']: r for _, r in df_nofw.iterrows()}
    fw_orig = [float(fw_map.get(p, {}).get('orig_stalls', 0) or 0) for p in prog]
    fw_reor = [float(fw_map.get(p, {}).get('reor_stalls', 0) or 0) for p in prog]
    nofw_orig = [float(nofw_map.get(p, {}).get('orig_stalls', 0) or 0) for p in prog]
    nofw_reor = [float(nofw_map.get(p, {}).get('reor_stalls', 0) or 0) for p in prog]
    _plot_combined_bars(prog, fw_orig, fw_reor, nofw_orig, nofw_reor, outpath,
                        ylabel="Stall cycles", title="Stall count comparison")


def plot_combined_stall_rate(df_fw: pd.DataFrame, df_nofw: pd.DataFrame, outpath: Path) -> None:
    prog = sorted(set(df_fw['program'].astype(str)).union(df_nofw['program'].astype(str)))
    fw_map = {r['program']: r for _, r in df_fw.iterrows()}
    nofw_map = {r['program']: r for _, r in df_nofw.iterrows()}
    fw_orig = [float(fw_map.get(p, {}).get('orig_stall_rate', 0) or 0) for p in prog]
    fw_reor = [float(fw_map.get(p, {}).get('reor_stall_rate', 0) or 0) for p in prog]
    nofw_orig = [float(nofw_map.get(p, {}).get('orig_stall_rate', 0) or 0) for p in prog]
    nofw_reor = [float(nofw_map.get(p, {}).get('reor_stall_rate', 0) or 0) for p in prog]
    _plot_combined_bars(prog, fw_orig, fw_reor, nofw_orig, nofw_reor, outpath,
                        ylabel="Stall rate", title="Stall rate comparison",
                        annotate_int=False, precision=3)


def plot_combined_pct_metric(df_fw: pd.DataFrame, df_nofw: pd.DataFrame, orig_col: str, reor_col: str, pct_col: str, title: str, ylabel: str, outpath: Path) -> None:
    prog = sorted(set(df_fw['program'].astype(str)).union(df_nofw['program'].astype(str)))
    fw_map = {r['program']: r for _, r in df_fw.iterrows()}
    nofw_map = {r['program']: r for _, r in df_nofw.iterrows()}
    
    pct_fw = [float(fw_map.get(p, {}).get(pct_col, 0) or 0) for p in prog]
    pct_nofw = [float(nofw_map.get(p, {}).get(pct_col, 0) or 0) for p in prog]

    def get_ratio(m):
        try:
            orig = float(m.get(orig_col, 0) or 0)
            reor = float(m.get(reor_col, 0) or 0)
            return orig / reor if reor and reor > 0 else 1.0
        except Exception:
            return 1.0

    ratio_fw = [get_ratio(fw_map.get(p, {})) for p in prog]
    ratio_nofw = [get_ratio(nofw_map.get(p, {})) for p in prog]

    x = range(len(prog))
    width = 0.4
    fig, ax = plt.subplots(figsize=(max(16, len(prog) * 3.0), 8), dpi=150)
    b1 = ax.bar([i - width/2 for i in x], pct_fw, width, label="Pct Improvement (fw)", color=COLOR_FW_ORIG)
    b2 = ax.bar([i + width/2 for i in x], pct_nofw, width, label="Pct Improvement (no-fw)", color=COLOR_NOFW_ORIG)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.set_xticks(list(x))
    ax.set_xticklabels([p.replace("_", "\n") for p in prog], rotation=0, ha="center", fontsize=10)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=2, frameon=False, fontsize=10)
    ax.grid(axis="y", alpha=0.25)

    _ensure_top_padding(ax, [b1, b2], pad=0.14)

    for i, b in enumerate(b1):
        txt = f"{pct_fw[i]:.1f}%\n({ratio_fw[i]:.2f}x)"
        ax.annotate(txt, xy=(b.get_x() + b.get_width() / 2, b.get_height()),
                    xytext=(0, 4), textcoords="offset points", ha="center", va="bottom",
                    fontsize=10)
    for i, b in enumerate(b2):
        txt = f"{pct_nofw[i]:.1f}%\n({ratio_nofw[i]:.2f}x)"
        ax.annotate(txt, xy=(b.get_x() + b.get_width() / 2, b.get_height()),
                    xytext=(0, 4), textcoords="offset points", ha="center", va="bottom",
                    fontsize=10)

    fig.tight_layout()
    fig.subplots_adjust(bottom=0.45)
    fig.savefig(outpath, transparent=True, bbox_inches="tight")
    plt.close(fig)

def main(folder: Path) -> int:
    # folder may be a Path or None; default to current working dir when None
    folder = folder or Path.cwd()
    results_dir = Path(folder) / "results"

    if not results_dir.exists():
        print(f"Results directory not found: {results_dir}")
        return 1

    graphs_dir = ensure_graphs_dir(results_dir)

    csv_fw = results_dir / "analysis.csv"
    csv_no_fw = results_dir / "analysis_no_fw.csv"

    # Helper to generate the common suite of graphs for a dataframe and suffix
    def _gen_all(df: pd.DataFrame, suffix: str = ""):
        suf = f"{suffix}" if suffix else ""
        try:
            plot_stalls(df, graphs_dir / f"stall_count_comparison{suf}.png")
            plot_stall_rate(df, graphs_dir / f"stall_rate_comparison{suf}.png")
            plot_pct_stalls_and_speedup(df, graphs_dir / f"percent_stall_improvement{suf}.png")
            
            plot_cycles(df, graphs_dir / f"cycles_comparison{suf}.png")
            plot_pct_cycles_and_speedup(df, graphs_dir / f"percent_cycle_improvement{suf}.png")
            
            plot_cpi(df, graphs_dir / f"cpi_comparison{suf}.png")
            plot_pct_cpi_and_speedup(df, graphs_dir / f"percent_cpi_improvement{suf}.png")
        except Exception as e:
            print(f"Error generating individual graph: {e}")

    # If both forwarding and no-forwarding analyses exist, produce combined
    # per-program graphs that show forwarding and no-forwarding side-by-side.
    if csv_fw.exists() and csv_no_fw.exists():
        print(f"Reading {csv_fw} and {csv_no_fw}")
        df_fw = read_analysis_csv(csv_fw)
        df_nofw = read_analysis_csv(csv_no_fw)

        plot_combined_stalls(df_fw, df_nofw, graphs_dir / "stall_count_comparison.png")
        plot_combined_stall_rate(df_fw, df_nofw, graphs_dir / "stall_rate_comparison.png")
        plot_combined_pct_metric(df_fw, df_nofw, "orig_stalls", "reor_stalls", "pct_stall_improvement",
                                 "Percent Stall Improvement (annotated ratio)", "% Stall Improvement",
                                 graphs_dir / "percent_stall_improvement.png")
        
        plot_combined_cycles(df_fw, df_nofw, graphs_dir / "cycles_comparison.png")
        plot_combined_pct_metric(df_fw, df_nofw, "orig_cycles", "reor_cycles", "pct_cycle_improvement",
                                 "Percent cycle Improvement (annotated speedup)", "% Cycle Improvement",
                                 graphs_dir / "percent_cycle_improvement.png")
        
        plot_combined_cpi(df_fw, df_nofw, graphs_dir / "cpi_comparison.png")
        plot_combined_pct_metric(df_fw, df_nofw, "orig_cpi", "reor_cpi", "pct_cpi_improvement",
                                 "Percent CPI Improvement (annotated ratio)", "% CPI Improvement",
                                 graphs_dir / "percent_cpi_improvement.png")

        print(f"Wrote combined graphs to: {graphs_dir}")
        return 0

    # Fallback: if only one dataset exists, generate the existing suite.
    if csv_fw.exists():
        print(f"Reading {csv_fw}")
        df_fw = read_analysis_csv(csv_fw)
        _gen_all(df_fw, suffix="")
        print(f"Wrote graphs to: {graphs_dir}")
        return 0

    if csv_no_fw.exists():
        print(f"Reading {csv_no_fw}")
        df_nofw = read_analysis_csv(csv_no_fw)
        _gen_all(df_nofw, suffix="_no_fw")
        print(f"Wrote no-forwarding graphs to: {graphs_dir}")
        return 0

    print(f"No analysis CSVs found in {results_dir}; expected analysis.csv or analysis_no_fw.csv")
    return 2


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=textwrap.dedent("""Build comparison graphs from results/analysis.csv.
        Primary graph: cycles before vs after (most important).
        """))
    parser.add_argument("folder", nargs="?", default=".", help="Test folder (default: current dir)")
    args = parser.parse_args()
    folder = Path(args.folder).resolve()
    sys.exit(main(folder))
