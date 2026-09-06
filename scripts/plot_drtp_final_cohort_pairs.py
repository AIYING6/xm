"""Render the final DRTP cohort-paired figure from a complete seed-level CSV.

This is a paper-asset renderer only.  It neither trains nor evaluates a policy,
and it refuses partial cohorts or pooled-only input.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import shutil

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np


REQUIRED = {"cohort", "seed", "method", "perturbed_return", "timeout", "collision"}
METHODS = ("UTR", "Original DRTP")
COHORTS = ("A", "B")
COLORS = {"UTR": "#7A8793", "Original DRTP": "#257F8A"}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or not REQUIRED.issubset(reader.fieldnames):
            missing = sorted(REQUIRED - set(reader.fieldnames or ()))
            raise ValueError(f"input is missing required columns: {missing}")
        rows = list(reader)
    seen = set()
    for row in rows:
        key = (row["cohort"], int(row["seed"]), row["method"])
        if row["cohort"] not in COHORTS or row["method"] not in METHODS:
            raise ValueError(f"unsupported cohort or method: {key}")
        if key in seen:
            raise ValueError(f"duplicate cohort/seed/method row: {key}")
        seen.add(key)
        for field in ("perturbed_return", "timeout", "collision"):
            float(row[field])
    for cohort in COHORTS:
        seeds = {int(row["seed"]) for row in rows if row["cohort"] == cohort}
        if len(seeds) != 5:
            raise ValueError(f"cohort {cohort} must contain exactly five retained seeds")
        for seed in seeds:
            if {row["method"] for row in rows if row["cohort"] == cohort and int(row["seed"]) == seed} != set(METHODS):
                raise ValueError(f"cohort {cohort}, seed {seed} lacks a matched UTR/DRTP pair")
    return rows


def by_key(rows: list[dict[str, str]]) -> dict[tuple[str, int, str], dict[str, str]]:
    return {(row["cohort"], int(row["seed"]), row["method"]): row for row in rows}


def style() -> None:
    mpl.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "svg.fonttype": "none", "pdf.fonttype": 42, "font.size": 8,
        "axes.spines.right": False, "axes.spines.top": False, "axes.linewidth": 0.8,
    })


def render(rows: list[dict[str, str]], output: Path) -> None:
    output.mkdir(parents=True, exist_ok=False)
    style(); keyed = by_key(rows)
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.2), constrained_layout=True)
    deltas = {"return": {}, "timeout": {}, "collision": {}}
    for col, cohort in enumerate(COHORTS):
        ax = axes[0, col]
        seeds = sorted({int(row["seed"]) for row in rows if row["cohort"] == cohort})
        for seed in seeds:
            utr = float(keyed[(cohort, seed, "UTR")]["perturbed_return"])
            drtp = float(keyed[(cohort, seed, "Original DRTP")]["perturbed_return"])
            ax.plot((0, 1), (utr, drtp), color="#B8C0C8", linewidth=0.9, zorder=1)
            ax.scatter(0, utr, color=COLORS["UTR"], s=24, zorder=2)
            ax.scatter(1, drtp, color=COLORS["Original DRTP"], s=24, zorder=2)
            deltas["return"][(cohort, seed)] = drtp - utr
            deltas["timeout"][(cohort, seed)] = float(keyed[(cohort, seed, "Original DRTP")]["timeout"]) - float(keyed[(cohort, seed, "UTR")]["timeout"])
            deltas["collision"][(cohort, seed)] = float(keyed[(cohort, seed, "Original DRTP")]["collision"]) - float(keyed[(cohort, seed, "UTR")]["collision"])
        ax.set_title(f"Cohort {cohort}")
        ax.set_xticks((0, 1), METHODS)
        ax.set_ylabel("Perturbed return")
    for metric, ax, ylabel in (("return", axes[1, 0], "DRTP − UTR perturbed return"), ("timeout", axes[1, 1], "DRTP − UTR timeout")):
        for col, cohort in enumerate(COHORTS):
            values = [deltas[metric][(cohort, seed)] for seed in sorted({seed for c, seed in deltas[metric] if c == cohort})]
            ax.scatter(np.full(len(values), col), values, color="#257F8A", s=24)
        ax.axhline(0, color="#444444", linewidth=0.8)
        ax.set_xticks((0, 1), ("A", "B"))
        ax.set_ylabel(ylabel)
    fig.savefig(output / "figure_01_cohort_pairs.svg", bbox_inches="tight")
    fig.savefig(output / "figure_01_cohort_pairs.pdf", bbox_inches="tight")
    fig.savefig(output / "figure_01_cohort_pairs.tiff", dpi=600, bbox_inches="tight")
    plt.close(fig)
    with (output / "figure_01_source_data.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    with (output / "figure_01_metadata.txt").open("w", encoding="utf-8") as handle:
        handle.write("Figure is seed-level and cohort-separated. No pooled n=10 inference is shown.\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    rows = read_rows(args.input)
    if args.validate_only:
        print(f"VALID: {len(rows)} rows; complete A/B UTR/Original DRTP matched cohorts")
        return
    if args.output_dir.exists():
        raise FileExistsError(f"refusing to overwrite figure output: {args.output_dir}")
    render(rows, args.output_dir)
    print(f"WROTE: {args.output_dir}")


if __name__ == "__main__":
    main()
