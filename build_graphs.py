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
COLOR_PRIMARY = "#4C72B0"
COLOR_SECOND = "#DD8452"
COLOR_ACCENT = "#55A868"

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
                    ha="center", va="bottom", fontsize=6, clip_on=False)


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
                    ha="center", va="bottom", fontsize=6, clip_on=False)


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
    fig, ax = plt.subplots(figsize=(max(6, len(programs) * 0.9), 5), dpi=150)
    bars1 = ax.bar([i - width/2 for i in x], orig, width, label="Unordered", color=COLOR_PRIMARY)
    bars2 = ax.bar([i + width/2 for i in x], reor, width, label="Reordered", color=COLOR_SECOND)
    ax.set_ylabel("Cycles")
    ax.set_title("Cycles Comparison — Original vs Reordered")
    ax.set_xticks(list(x))
    ax.set_xticklabels(label_names, rotation=0, ha="center", fontsize=8)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=2, frameon=False, fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    # ensure some headroom so labels are not cropped
    _ensure_top_padding(ax, [bars1, bars2], pad=0.12)
    # annotate (stagger bars so labels don't overlap)
    annotate_int_bars(ax, bars1, offset_y=2, dx=-0.02)
    annotate_int_bars(ax, bars2, offset_y=4, dx=0.02)
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
    fig, ax = plt.subplots(figsize=(max(6, len(programs) * 0.9), 5), dpi=150)
    bars1 = ax.bar([i - width/2 for i in x], orig, width, label="Unordered", color=COLOR_PRIMARY)
    bars2 = ax.bar([i + width/2 for i in x], reor, width, label="Reordered", color=COLOR_SECOND)
    ax.set_ylabel("CPI")
    ax.set_title("CPI Comparison — Original vs Reordered")
    ax.set_xticks(list(x))
    ax.set_xticklabels(label_names, rotation=0, ha="center", fontsize=8)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=2, frameon=False, fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    _ensure_top_padding(ax, [bars1, bars2], pad=0.12)
    annotate_float_bars(ax, bars1, offset_y=2, dx=-0.02)
    annotate_float_bars(ax, bars2, offset_y=4, dx=0.02)
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
    fig, ax = plt.subplots(figsize=(max(6, len(programs) * 0.9), 5), dpi=150)
    bars1 = ax.bar([i - width/2 for i in x], orig, width, label="Unordered", color=COLOR_PRIMARY)
    bars2 = ax.bar([i + width/2 for i in x], reor, width, label="Reordered", color=COLOR_SECOND)
    ax.set_ylabel("Stall cycles")
    ax.set_title("Stall Count Comparison — Original vs Reordered")
    ax.set_xticks(list(x))
    ax.set_xticklabels(label_names, rotation=0, ha="center", fontsize=8)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=2, frameon=False, fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    _ensure_top_padding(ax, [bars1, bars2], pad=0.12)
    annotate_int_bars(ax, bars1, offset_y=2, dx=-0.02)
    annotate_int_bars(ax, bars2, offset_y=4, dx=0.02)
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
    fig, ax = plt.subplots(figsize=(max(6, len(programs) * 0.9), 5), dpi=150)
    bars1 = ax.bar([i - width/2 for i in x], raws_orig, width, label="Unordered RAW", color=COLOR_PRIMARY)
    bars2 = ax.bar([i + width/2 for i in x], raws_reor, width, label="Reordered RAW", color=COLOR_SECOND)
    ax.set_ylabel("RAW hazard count (static)")
    ax.set_title("Data Hazard (RAW) — static count from assembly")
    ax.set_xticks(list(x))
    ax.set_xticklabels(label_names, rotation=0, ha="center", fontsize=8)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=2, frameon=False, fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    _ensure_top_padding(ax, [bars1, bars2], pad=0.14)
    # annotate side-by-side with tiny horizontal offsets to avoid overlap
    annotate_int_bars(ax, bars1, offset_y=2, dx=-0.02)
    annotate_int_bars(ax, bars2, offset_y=2, dx=0.02)
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.25)
    fig.savefig(outpath, transparent=True, bbox_inches="tight")
    plt.close(fig)

def _compute_pct_and_speedup(orig: pd.Series, reor: pd.Series) -> pd.DataFrame:
    df = pd.DataFrame({"orig": orig.astype(float), "reor": reor.astype(float)})
    # avoid divide-by-zero
    df["speedup"] = df.apply(lambda r: r["orig"] / r["reor"] if r["reor"] and r["reor"] > 0 else 1.0, axis=1)
    df["pct_improvement"] = df.apply(lambda r: ((r["orig"] - r["reor"]) / r["orig"] * 100.0)
                                      if r["orig"] and r["orig"] > 0 else 0.0, axis=1)
    return df


def plot_pct_cycles_and_speedup(df_src: pd.DataFrame, outpath: Path) -> None:
    programs = df_src["program"].astype(str)
    label_names = [p.replace("_", "\n") for p in programs]
    comp = _compute_pct_and_speedup(df_src["orig_cycles"], df_src["reor_cycles"])

    x = range(len(programs))
    width = 0.6
    fig, ax = plt.subplots(figsize=(max(6, len(programs) * 0.9), 4.5), dpi=150)
    bars = ax.bar(x, comp["pct_improvement"], width, color=COLOR_ACCENT)
    ax.set_ylabel("% Cycle Improvement")
    ax.set_title("Percent Cycle Improvement (annotated speedup)")
    ax.set_xticks(list(x))
    ax.set_xticklabels(label_names, rotation=0, ha="center", fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    _ensure_top_padding(ax, bars, pad=0.14)
    # annotate percent and speedup
    for i, b in enumerate(bars):
        pv = comp.iloc[i]["pct_improvement"]
        sv = comp.iloc[i]["speedup"]
        txt = f"{pv:.1f}%\n({sv:.2f}x)"
        ax.annotate(txt, xy=(b.get_x() + b.get_width() / 2, b.get_height()),
                    xytext=(0, 4), textcoords="offset points", ha="center", va="bottom",
                    fontsize=6)
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.30)
    fig.savefig(outpath, transparent=True, bbox_inches="tight")
    plt.close(fig)


def plot_stall_rate(df_src: pd.DataFrame, outpath: Path) -> None:
    # expects columns orig_stall_rate and reor_stall_rate
    programs = df_src["program"].astype(str)
    label_names = [p.replace("_", "\n") for p in programs]
    orig = df_src["orig_stall_rate"].astype(float)
    reor = df_src["reor_stall_rate"].astype(float)

    x = range(len(programs))
    width = 0.35
    fig, ax = plt.subplots(figsize=(max(6, len(programs) * 0.9), 4.5), dpi=150)
    bars1 = ax.bar([i - width/2 for i in x], orig, width, label="Unordered", color=COLOR_PRIMARY)
    bars2 = ax.bar([i + width/2 for i in x], reor, width, label="Reordered", color=COLOR_SECOND)
    ax.set_ylabel("Stall rate")
    ax.set_title("Stall Rate Comparison — Original vs Reordered")
    ax.set_xticks(list(x))
    ax.set_xticklabels(label_names, rotation=0, ha="center", fontsize=8)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=2, frameon=False, fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    _ensure_top_padding(ax, [bars1, bars2], pad=0.12)
    annotate_float_bars(ax, bars1, offset_y=2, dx=-0.02, precision=3)
    annotate_float_bars(ax, bars2, offset_y=2, dx=0.02, precision=3)
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.30)
    fig.savefig(outpath, transparent=True, bbox_inches="tight")
    plt.close(fig)


def plot_pct_cpi_and_speedup(df_src: pd.DataFrame, outpath: Path) -> None:
    programs = df_src["program"].astype(str)
    label_names = [p.replace("_", "\n") for p in programs]
    comp = _compute_pct_and_speedup(df_src["orig_cpi"], df_src["reor_cpi"])

    x = range(len(programs))
    width = 0.6
    fig, ax = plt.subplots(figsize=(max(6, len(programs) * 0.9), 4.5), dpi=150)
    bars = ax.bar(x, comp["pct_improvement"], width, color=COLOR_ACCENT)
    ax.set_ylabel("% CPI Improvement")
    ax.set_title("Percent CPI Improvement (annotated ratio)")
    ax.set_xticks(list(x))
    ax.set_xticklabels(label_names, rotation=0, ha="center", fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    _ensure_top_padding(ax, bars, pad=0.14)
    for i, b in enumerate(bars):
        pv = comp.iloc[i]["pct_improvement"]
        sv = comp.iloc[i]["speedup"]
        txt = f"{pv:.1f}%\n({sv:.2f}x)"
        ax.annotate(txt, xy=(b.get_x() + b.get_width() / 2, b.get_height()),
                    xytext=(0, 4), textcoords="offset points", ha="center", va="bottom",
                    fontsize=6)
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.30)
    fig.savefig(outpath, transparent=True, bbox_inches="tight")
    plt.close(fig)


def plot_pct_stalls_and_speedup(df_src: pd.DataFrame, outpath: Path) -> None:
    programs = df_src["program"].astype(str)
    label_names = [p.replace("_", "\n") for p in programs]
    comp = _compute_pct_and_speedup(df_src["orig_stalls"], df_src["reor_stalls"])

    x = range(len(programs))
    width = 0.6
    fig, ax = plt.subplots(figsize=(max(6, len(programs) * 0.9), 4.5), dpi=150)
    bars = ax.bar(x, comp["pct_improvement"], width, color=COLOR_ACCENT)
    ax.set_ylabel("% Stall Improvement")
    ax.set_title("Percent Stall Improvement (annotated ratio)")
    ax.set_xticks(list(x))
    ax.set_xticklabels(label_names, rotation=0, ha="center", fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    _ensure_top_padding(ax, bars, pad=0.14)
    for i, b in enumerate(bars):
        pv = comp.iloc[i]["pct_improvement"]
        sv = comp.iloc[i]["speedup"]
        txt = f"{pv:.1f}%\n({sv:.2f}x)"
        ax.annotate(txt, xy=(b.get_x() + b.get_width() / 2, b.get_height()),
                    xytext=(0, 4), textcoords="offset points", ha="center", va="bottom",
                    fontsize=6)
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.30)
    fig.savefig(outpath, transparent=True, bbox_inches="tight")
    plt.close(fig)

def main(folder: Path) -> int:
    results_dir = folder / "results"
    csv_path = results_dir / "analysis.csv"
    if not csv_path.exists():
        print(f"analysis.csv not found at: {csv_path}")
        return 2

    df = read_analysis_csv(csv_path)
    graphs = ensure_graphs_dir(results_dir)

    # Primary graphs
    plot_cycles(df, graphs / "cycles_comparison.png")
    plot_cpi(df, graphs / "cpi_comparison.png")
    plot_stalls(df, graphs / "stalls_comparison.png")
    print(f"Saved cycles/cpi/stalls graphs to: {graphs}")

    # Percent cycle improvement + annotated speedup
    plot_pct_cycles_and_speedup(df, graphs / "pct_cycles_improvement.png")
    print(f"Saved percent cycle improvement graph to: {graphs / 'pct_cycles_improvement.png'}")

    # Optional: stall rate comparison if available
    if "orig_stall_rate" in df.columns and "reor_stall_rate" in df.columns:
        plot_stall_rate(df, graphs / "stall_rate_comparison.png")
        print(f"Saved stall rate comparison to: {graphs / 'stall_rate_comparison.png'}")
    # Percent CPI improvement
    plot_pct_cpi_and_speedup(df, graphs / "pct_cpi_improvement.png")
    print(f"Saved percent CPI improvement graph to: {graphs / 'pct_cpi_improvement.png'}")

    # Percent Stall improvement
    plot_pct_stalls_and_speedup(df, graphs / "pct_stalls_improvement.png")
    print(f"Saved percent Stall improvement graph to: {graphs / 'pct_stalls_improvement.png'}")

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=textwrap.dedent("""Build comparison graphs from results/analysis.csv.
        Primary graph: cycles before vs after (most important).
        """))
    parser.add_argument("folder", nargs="?", default=".", help="Test folder (default: current dir)")
    args = parser.parse_args()
    folder = Path(args.folder).resolve()
    sys.exit(main(folder))
