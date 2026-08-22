"""Publication-style, offline figures for the DRTP-DIV-A0 forensic audit.

Figure contract
---------------
Core conclusion: archived PPO diagnostics and matched-state policy distances
do not identify a common precursor unique to weak DRTP seeds; coordination
precedence is not estimable because step trajectories were not archived.
Archetype: quantitative grid.  Evidence is descriptive by training seed.
No episode, state, or seed is excluded.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

mpl.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans", "sans-serif"],
                     "font.size": 7, "svg.fonttype": "none", "pdf.fonttype": 42,
                     "axes.spines.right": False, "axes.spines.top": False, "axes.linewidth": 0.8})

COLORS = {"strong": "#4C78A8", "weak": "#D65F5F", "utr_sg": "#7F7F7F", "drtp_sg": "#1B9E77"}
WINDOW_ORDER = ["0_0.25M", "0.25_0.5M", "0.5_1M", "1_2M", "2_3M", "3_10M"]


def read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as h:
        return list(csv.DictReader(h))


def export(fig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(path.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(path.with_suffix(".tiff"), dpi=600, bbox_inches="tight")
    plt.close(fig)


def panel_label(ax, label: str) -> None:
    ax.text(-0.16, 1.05, label, transform=ax.transAxes, fontsize=8, fontweight="bold", va="top")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--artifact-root", type=Path, required=True)
    args = p.parse_args()
    root = args.artifact_root
    opt, policy = read(root / "optimization_timeline.csv"), read(root / "policy_distance_timeline.csv")
    out = root / "figures"

    # A: primary optimization evidence.  Each point is a seed-window mean.
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 4.2), constrained_layout=True)
    for ax, metric, title in zip(axes.flat, ["approx_kl", "clip_fraction", "entropy", "grad_norm"],
                                 ["Approx. KL", "Clip fraction", "Actor entropy", "Gradient norm"]):
        for seed in (1901, 1902, 2001, 2002, 2003):
            rows = [r for r in opt if r["arm"] == "drtp_sg" and r["metric"] == metric and int(r["seed"]) == seed]
            rows.sort(key=lambda r: WINDOW_ORDER.index(r["window"]))
            xs = list(range(len(rows))); ys = [float(r["mean"]) for r in rows]
            ax.plot(xs, ys, marker="o", ms=3, lw=1, color=COLORS[rows[0]["seed_class"]], alpha=.82)
        ax.set_title(title); ax.set_xticks(range(6), [".25", ".5", "1", "2", "3", "10"])
        ax.set_xlabel("training horizon (M steps)"); ax.set_ylabel("window mean")
        panel_label(ax, chr(97 + list(axes.flat).index(ax)))
    axes[0, 0].plot([], [], color=COLORS["strong"], label="strong historical seed")
    axes[0, 0].plot([], [], color=COLORS["weak"], label="weak historical seed")
    axes[0, 0].legend(loc="best", fontsize=6)
    export(fig, out / "figure_A_optimization_timeline")

    # B: matched-state policy mapping.
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9), constrained_layout=True)
    for ax, metric, title in zip(axes, ["mean_total_variation", "mean_js_divergence"],
                                 ["DRTP–UTR action total variation", "DRTP–UTR Jensen–Shannon divergence"]):
        for seed in (1901, 1902, 2001, 2002, 2003):
            rows = [r for r in policy if int(r["seed"]) == seed]
            rows.sort(key=lambda r: float(r["environment_steps"]))
            ax.plot([float(r["environment_steps"])/1e6 for r in rows], [float(r[metric]) for r in rows],
                    marker="o", ms=2.5, lw=1, color=COLORS[rows[0]["seed_class"]], alpha=.82)
        ax.set_xlabel("policy milestone (M steps)"); ax.set_ylabel("mean across archived bank")
        ax.set_title(title); panel_label(ax, "a" if ax is axes[0] else "b")
    axes[0].plot([], [], color=COLORS["strong"], label="strong historical seed")
    axes[0].plot([], [], color=COLORS["weak"], label="weak historical seed")
    axes[0].legend(loc="best", fontsize=6)
    export(fig, out / "figure_B_matched_policy_divergence")

    # C: evidence-availability figure, deliberately not a fabricated coordination curve.
    fig, ax = plt.subplots(figsize=(7.2, 2.2), constrained_layout=True)
    labels = ["PPO update diagnostics", "Runtime actor-legal state bank", "Step-level coordination trajectories", "Milestone behavior evaluation"]
    values = [1, 1, 0, 0]
    colors = ["#4C78A8", "#4C78A8", "#BDBDBD", "#BDBDBD"]
    ax.barh(range(len(labels)), values, color=colors)
    ax.set_yticks(range(len(labels)), labels); ax.set_xlim(0, 1.15); ax.set_xticks([0, 1], ["absent", "archived"])
    for y, value in enumerate(values): ax.text(value + .03, y, "available" if value else "not archived", va="center")
    ax.set_title("Evidence availability constrains the temporal claim")
    panel_label(ax, "c")
    export(fig, out / "figure_C_coordination_evidence_availability")

    # D: causal-timeline bounds.
    fig, ax = plt.subplots(figsize=(7.2, 2.5), constrained_layout=True)
    ax.hlines(3, .0, 10, color="#4C78A8", lw=5, label="optimization diagnostics available")
    ax.hlines(2, .5, 10, color="#1B9E77", lw=5, label="matched-state policy mapping available")
    ax.hlines(1, .0, 10, color="#BDBDBD", lw=5, label="coordination trajectory not archived")
    ax.hlines(0, 10, 10, color="#D65F5F", lw=5, label="final external performance available")
    ax.set_xlim(0, 10.4); ax.set_ylim(-.6, 3.6); ax.set_xticks(range(0, 11)); ax.set_xlabel("training budget (M steps)")
    ax.set_yticks([0,1,2,3], ["external performance", "coordination", "policy mapping", "optimization"])
    ax.set_title("Temporal-precedence boundary: no archival basis for coordination-first attribution")
    panel_label(ax, "d")
    export(fig, out / "figure_D_temporal_precedence_boundary")


if __name__ == "__main__":
    main()
