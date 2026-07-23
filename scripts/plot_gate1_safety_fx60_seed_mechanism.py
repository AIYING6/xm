from __future__ import annotations

import argparse
import ast
import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TABLE_DIR = ROOT / "results" / "gate1_safety_fx60_paper_tables"
DEFAULT_OUT_DIR = ROOT / "results" / "gate1_safety_fx60_seed_mechanism"
DEFAULT_DOC = ROOT / "docs" / "gate1_safety_fx60_seed_mechanism_summary.md"

METHOD_ORDER = ("no_graph", "single", "multi_relation")
ABLATION_ORDER = ("multi_relation", "no_task_support", "no_role_pair_gate")
METHOD_LABELS = {
    "no_graph": "MAPPO\n(no graph)",
    "single": "Single\nGraph",
    "multi_relation": "Full\nMulti-Rel.",
    "no_task_support": "w/o Task\nSupport",
    "no_role_pair_gate": "w/o Role-Pair\nGate",
}
COMPARISON_LABELS = {
    "multi_relation_vs_single": "Full vs Single graph",
    "multi_relation_vs_no_graph": "Full vs No graph",
    "multi_relation_vs_no_task_support": "Full vs w/o task-support",
    "multi_relation_vs_no_role_pair_gate": "Full vs w/o role-pair gate",
}
METRIC_LABELS = {
    "post_failure_chain_recovered": "Recovery",
    "tracking_during_failure_rate": "Tracking",
    "chain_closed_during_failure_rate": "Chain closed",
    "timeout": "Timeout",
}
COLORS = {
    "no_graph": "#5B6770",
    "single": "#3B73B9",
    "multi_relation": "#2F9C67",
    "no_task_support": "#D9822B",
    "no_role_pair_gate": "#8E5EA2",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate seed-level and mechanism evidence figures for the Gate-1 safety fixed-update-60 package."
    )
    parser.add_argument("--table-dir", type=Path, default=DEFAULT_TABLE_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_DOC)
    return parser.parse_args()


def native_path(path: Path) -> str:
    resolved = path.resolve()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def open_path(path: Path, mode: str, **kwargs):
    return open(native_path(path), mode, **kwargs)


def read_rows(path: Path) -> list[dict[str, str]]:
    with open_path(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_rows(path: Path, rows: Iterable[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open_path(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def parse_seed_values(text: str) -> list[float]:
    value = ast.literal_eval(text)
    if not isinstance(value, list):
        raise ValueError(f"seed_recovery must be a list: {text!r}")
    return [float(v) for v in value]


def seed_rows(rows: list[dict[str, str]], source: str) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for row in rows:
        method = row["method"]
        for seed, value in enumerate(parse_seed_values(row["seed_recovery"])):
            out.append(
                {
                    "source": source,
                    "method": method,
                    "label": row["label"],
                    "seed": seed,
                    "recovery": value,
                    "tracking_mean": float(row["tracking_mean"]),
                    "chain_mean": float(row["chain_mean"]),
                    "timeout_mean": float(row["timeout_mean"]),
                    "collision_mean": float(row["collision_mean"]),
                }
            )
    return out


def mean(values: list[float]) -> float:
    return float(np.mean(values)) if values else float("nan")


def sd(values: list[float]) -> float:
    return float(np.std(values, ddof=1)) if len(values) > 1 else 0.0


def style_axes(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#D8DDE3", linewidth=0.8, alpha=0.85)


def save_fig(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=260, bbox_inches="tight")
    plt.close(fig)


def plot_main_seed_scatter(rows: list[dict[str, object]], out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.3, 4.2))
    jitter = np.linspace(-0.16, 0.16, 5)
    for x, method in enumerate(METHOD_ORDER):
        values = [float(r["recovery"]) for r in rows if r["method"] == method]
        for seed, value in enumerate(values):
            ax.scatter(
                x + jitter[seed],
                value * 100.0,
                s=52,
                color=COLORS[method],
                edgecolor="white",
                linewidth=0.9,
                zorder=3,
            )
            ax.text(x + jitter[seed], value * 100.0 + 3.2, f"s{seed}", ha="center", fontsize=7, color="#30363D")
        ax.hlines(mean(values) * 100.0, x - 0.28, x + 0.28, color="#111827", linewidth=2.0, zorder=4)
        ax.errorbar(
            x,
            mean(values) * 100.0,
            yerr=sd(values) * 100.0,
            color="#111827",
            capsize=5,
            linewidth=1.2,
            zorder=2,
        )
    ax.set_xticks(range(len(METHOD_ORDER)), [METHOD_LABELS[m] for m in METHOD_ORDER])
    ax.set_ylabel("Post-failure recovery (%)")
    ax.set_ylim(-4, 108)
    ax.set_title("Seed-level recovery under strict sensing and relay failure", fontsize=11)
    style_axes(ax)
    save_fig(fig, out_path)


def plot_ablation_pair_deltas(rows: list[dict[str, object]], out_path: Path) -> None:
    by_method = {
        method: [float(r["recovery"]) for r in rows if r["method"] == method]
        for method in ABLATION_ORDER
    }
    fig, axes = plt.subplots(1, 2, figsize=(8.8, 3.8), sharey=True)
    pairs = [
        ("no_task_support", "Task-support relation"),
        ("no_role_pair_gate", "Role-pair gate"),
    ]
    for ax, (ablation, title) in zip(axes, pairs):
        base = by_method[ablation]
        full = by_method["multi_relation"]
        for seed, (b, f) in enumerate(zip(base, full)):
            ax.plot([0, 1], [b * 100.0, f * 100.0], color="#A7B0BA", linewidth=1.2, zorder=1)
            ax.scatter(0, b * 100.0, s=46, color=COLORS[ablation], edgecolor="white", linewidth=0.8, zorder=3)
            ax.scatter(1, f * 100.0, s=46, color=COLORS["multi_relation"], edgecolor="white", linewidth=0.8, zorder=3)
            ax.text(1.04, f * 100.0, f"s{seed}", va="center", fontsize=7, color="#30363D")
        deltas = [(f - b) * 100.0 for b, f in zip(base, full)]
        ax.text(
            0.5,
            104,
            f"mean delta {mean(deltas):+.1f} pp",
            ha="center",
            va="top",
            fontsize=8,
            color="#111827",
        )
        ax.set_xticks([0, 1], [METHOD_LABELS[ablation], METHOD_LABELS["multi_relation"]])
        ax.set_title(title, fontsize=10)
        ax.set_ylim(-4, 108)
        style_axes(ax)
    axes[0].set_ylabel("Post-failure recovery (%)")
    fig.suptitle("Paired seed-level mechanism ablations", fontsize=11, y=1.04)
    save_fig(fig, out_path)


def plot_bootstrap_forest(rows: list[dict[str, str]], out_path: Path) -> None:
    metrics = (
        "post_failure_chain_recovered",
        "tracking_during_failure_rate",
        "chain_closed_during_failure_rate",
        "timeout",
    )
    selected = [r for r in rows if r["metric"] in metrics]
    fig, axes = plt.subplots(1, 4, figsize=(13.0, 4.5), sharey=True)
    comparisons = list(COMPARISON_LABELS)
    y_positions = np.arange(len(comparisons))[::-1]
    for ax, metric in zip(axes, metrics):
        metric_rows = {r["comparison"]: r for r in selected if r["metric"] == metric}
        for y, comparison in zip(y_positions, comparisons):
            row = metric_rows[comparison]
            delta = float(row["delta_proposed_minus_baseline"]) * 100.0
            lo = float(row["delta_ci_low"]) * 100.0
            hi = float(row["delta_ci_high"]) * 100.0
            color = COLORS["multi_relation"] if lo > 0 or hi < 0 else "#697386"
            ax.plot([lo, hi], [y, y], color=color, linewidth=2.0)
            ax.scatter(delta, y, color=color, s=38, edgecolor="white", linewidth=0.7, zorder=3)
        ax.axvline(0, color="#333333", linewidth=0.9, linestyle="--")
        ax.set_title(METRIC_LABELS[metric], fontsize=10)
        ax.set_xlabel("Full minus baseline (pp)")
        ax.grid(axis="x", color="#D8DDE3", linewidth=0.8, alpha=0.85)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    axes[0].set_yticks(y_positions, [COMPARISON_LABELS[c] for c in comparisons])
    for ax in axes[1:]:
        ax.tick_params(axis="y", left=False, labelleft=False)
    fig.suptitle("Seed-aware hierarchical bootstrap deltas", fontsize=11, y=1.03)
    save_fig(fig, out_path)


def write_report(path: Path, out_dir: Path, main_rows: list[dict[str, object]], ablation_rows: list[dict[str, object]]) -> None:
    main_summary = []
    for method in METHOD_ORDER:
        vals = [float(r["recovery"]) for r in main_rows if r["method"] == method]
        main_summary.append((method, mean(vals), sd(vals), vals))
    ablation_summary = []
    for method in ABLATION_ORDER:
        vals = [float(r["recovery"]) for r in ablation_rows if r["method"] == method]
        ablation_summary.append((method, mean(vals), sd(vals), vals))

    lines = [
        "# Gate 1 Safety Fixed-Update-60 Seed-Level Mechanism Figures",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Purpose",
        "",
        "This package turns the frozen fixed-update-60 evidence into seed-level mechanism figures. It does not introduce new training, new checkpoint selection, or new test episodes.",
        "",
        "## Main Seed-Level Recovery",
        "",
        "| Method | Recovery | Seed recovery |",
        "|---|---:|---:|",
    ]
    for method, m, s, vals in main_summary:
        lines.append(
            f"| {METHOD_LABELS[method].replace(chr(10), ' ')} | {m * 100.0:.1f}% +/- {s * 100.0:.1f} | "
            f"[{', '.join(f'{v * 100.0:.1f}' for v in vals)}] |"
        )
    lines.extend(
        [
            "",
            "## Mechanism Ablation Seed Recovery",
            "",
            "| Variant | Recovery | Seed recovery |",
            "|---|---:|---:|",
        ]
    )
    for method, m, s, vals in ablation_summary:
        lines.append(
            f"| {METHOD_LABELS[method].replace(chr(10), ' ')} | {m * 100.0:.1f}% +/- {s * 100.0:.1f} | "
            f"[{', '.join(f'{v * 100.0:.1f}' for v in vals)}] |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The main comparison figure makes the seed-level stability gap visible: full multi-relation has high recovery on all five seeds, while `no_graph` and `single` have large seed-to-seed failures.",
            "- The paired ablation figure shows that role-pair gating is the cleaner mechanism result; task-support removal reduces mean recovery but has weaker seed separation.",
            "- The bootstrap forest plot should be used to avoid overclaiming: only intervals that stay away from zero should be described as statistically separated.",
            "",
            "## Artifacts",
            "",
            f"- Main seed scatter: `{(out_dir / 'main_seed_recovery_scatter.png').relative_to(ROOT).as_posix()}`",
            f"- Ablation paired deltas: `{(out_dir / 'mechanism_ablation_seed_pairs.png').relative_to(ROOT).as_posix()}`",
            f"- Bootstrap forest: `{(out_dir / 'seed_aware_delta_forest.png').relative_to(ROOT).as_posix()}`",
            f"- Long-form seed CSV: `{(out_dir / 'seed_level_recovery_long.csv').relative_to(ROOT).as_posix()}`",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with open_path(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def main() -> None:
    args = parse_args()
    main_csv = args.table_dir / "main_results.csv"
    ablation_csv = args.table_dir / "ablation_results.csv"
    delta_csv = args.table_dir / "seed_aware_deltas.csv"

    main_rows_raw = read_rows(main_csv)
    ablation_rows_raw = read_rows(ablation_csv)
    delta_rows = read_rows(delta_csv)

    main_seed_rows = seed_rows(main_rows_raw, "main")
    ablation_seed_rows = seed_rows(ablation_rows_raw, "ablation")
    long_rows = main_seed_rows + ablation_seed_rows

    write_rows(
        args.out_dir / "seed_level_recovery_long.csv",
        long_rows,
        [
            "source",
            "method",
            "label",
            "seed",
            "recovery",
            "tracking_mean",
            "chain_mean",
            "timeout_mean",
            "collision_mean",
        ],
    )
    plot_main_seed_scatter(main_seed_rows, args.out_dir / "main_seed_recovery_scatter.png")
    plot_ablation_pair_deltas(ablation_seed_rows, args.out_dir / "mechanism_ablation_seed_pairs.png")
    plot_bootstrap_forest(delta_rows, args.out_dir / "seed_aware_delta_forest.png")
    write_report(args.report, args.out_dir, main_seed_rows, ablation_seed_rows)
    print(args.report)


if __name__ == "__main__":
    main()
