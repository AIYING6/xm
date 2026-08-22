"""Create the four pre-specified G0 topology-generalization figures.

The script is read-only with respect to experiment evidence: it consumes the
frozen aggregate CSV/manifest and writes publication-oriented visualizations.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np


mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
        "font.size": 7,
        "axes.spines.right": False,
        "axes.spines.top": False,
        "axes.linewidth": 0.8,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
    }
)

COLORS = {"UTR-SG-MAPPO": "#3B6FB6", "DRTP-SG-MAPPO": "#C27A2C"}
ORDER = [
    "reference_nominal",
    "seen_f0_44_80",
    "parameter_timing_20_80",
    "parameter_duration_44_140",
    "U1_scout_node_failure",
    "U2_static_symmetric_direct_prune",
    "U3_static_directed_scout_to_attacker_prune",
    "U4_scout_failure_symmetric_direct_prune",
    "U5_relay_failure_directed_direct_prune",
    "U6_relay_failure_symmetric_direct_prune",
]
SHORT = {
    "reference_nominal": "N",
    "seen_f0_44_80": "F0",
    "parameter_timing_20_80": "T",
    "parameter_duration_44_140": "D",
    "U1_scout_node_failure": "U1",
    "U2_static_symmetric_direct_prune": "U2",
    "U3_static_directed_scout_to_attacker_prune": "U3",
    "U4_scout_failure_symmetric_direct_prune": "U4",
    "U5_relay_failure_directed_direct_prune": "U5",
    "U6_relay_failure_symmetric_direct_prune": "U6",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def save(fig: mpl.figure.Figure, out: Path, stem: str) -> None:
    fig.savefig(out / f"{stem}.png", dpi=600, bbox_inches="tight")
    fig.savefig(out / f"{stem}.svg", bbox_inches="tight")
    fig.savefig(out / f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(out / f"{stem}.tiff", dpi=600, bbox_inches="tight")
    plt.close(fig)


def plot_suite(manifest: dict, out: Path) -> None:
    training = manifest["training_exposure"]
    labels = ["nominal", "F0", "timing", "duration", "compound"]
    counts = [1, 1, 2, 2, 2]
    fig, ax = plt.subplots(figsize=(5.8, 3.0))
    ax.bar(labels, counts, color="#8796A8", width=0.62)
    ax.axhline(0, color="black", linewidth=0.6)
    ax.set_ylabel("Distinct scheduled condition groups")
    ax.set_title("G0 topology suite: training exposure versus unseen structure", loc="left", weight="bold")
    ax.text(0.01, 0.02, "Training exposure contains failure timing/duration only; no edge deletion or non-Relay node failure.", transform=ax.transAxes, fontsize=6)
    ax.set_ylim(0, 2.7)
    for idx, value in enumerate(counts):
        ax.text(idx, value + 0.08, str(value), ha="center", va="bottom")
    fig.tight_layout()
    save(fig, out, "g0_training_vs_unseen_topology_suite")


def plot_per_topology(rows: list[dict[str, str]], out: Path) -> None:
    grouped: dict[tuple[str, str], float] = {}
    for row in rows:
        grouped[(row["method"], row["condition"])] = float(row["J"])
    methods = ["UTR-SG-MAPPO", "DRTP-SG-MAPPO"]
    x = np.arange(len(ORDER))
    width = 0.36
    fig, ax = plt.subplots(figsize=(9.0, 3.8))
    for idx, method in enumerate(methods):
        values = [grouped.get((method, condition), np.nan) for condition in ORDER]
        ax.bar(x + (idx - 0.5) * width, values, width=width, color=COLORS[method], alpha=0.88, label=method)
    ax.set_xticks(x, [SHORT[item] for item in ORDER])
    ax.set_ylabel("Mean episode return J")
    ax.set_title("Frozen-policy zero-shot performance across topology conditions", loc="left", weight="bold")
    ax.axvline(3.5, color="#555555", linewidth=0.7, linestyle="--")
    ax.text(0.18, 0.96, "parameter OOD", transform=ax.transAxes, fontsize=6, ha="center")
    ax.text(0.69, 0.96, "structural OOD", transform=ax.transAxes, fontsize=6, ha="center")
    ax.legend(ncol=2, loc="best")
    fig.tight_layout()
    save(fig, out, "g0_zero_shot_per_topology")


def plot_structural_parameter(rows: list[dict[str, str]], out: Path) -> None:
    families = {"parameter": ["parameter_timing_20_80", "parameter_duration_44_140"], "structural": ["U1_scout_node_failure", "U2_static_symmetric_direct_prune", "U3_static_directed_scout_to_attacker_prune", "U4_scout_failure_symmetric_direct_prune", "U5_relay_failure_directed_direct_prune"]}
    method_values = defaultdict(dict)
    for row in rows:
        method_values[row["method"]][row["condition"]] = float(row["J"])
    fig, ax = plt.subplots(figsize=(5.4, 3.3))
    x = np.arange(2)
    width = 0.36
    for idx, method in enumerate(("UTR-SG-MAPPO", "DRTP-SG-MAPPO")):
        seen = method_values[method]["seen_f0_44_80"]
        gaps = [seen - np.mean([method_values[method][c] for c in conditions]) for conditions in families.values()]
        ax.bar(x + (idx - 0.5) * width, gaps, width=width, label=method, color=COLORS[method])
    ax.set_xticks(x, ["Timing/duration\nparameter OOD", "Topology\nstructural OOD"])
    ax.set_ylabel("Degradation from seen F0 (J_seen − J_OOD)")
    ax.set_title("Structural versus parameter OOD gap", loc="left", weight="bold")
    ax.axhline(0, color="black", linewidth=0.6)
    ax.legend()
    fig.tight_layout()
    save(fig, out, "g0_structural_vs_parameter_ood")


def plot_heatmap(seed_rows: list[dict[str, str]], out: Path) -> None:
    conditions = ["U1_scout_node_failure", "U2_static_symmetric_direct_prune", "U3_static_directed_scout_to_attacker_prune", "U4_scout_failure_symmetric_direct_prune", "U5_relay_failure_directed_direct_prune"]
    rows = [row for row in seed_rows if row["method"] == "UTR-SG-MAPPO"]
    seeds = sorted({int(row["training_seed"]) for row in rows})
    lookup = {(int(row["training_seed"]), row["condition"]): float(row["J"]) for row in rows}
    data = np.array([[lookup[(seed, condition)] for condition in conditions] for seed in seeds])
    fig, ax = plt.subplots(figsize=(5.4, 3.2))
    image = ax.imshow(data, cmap="Blues", aspect="auto")
    ax.set_xticks(range(len(conditions)), [SHORT[c] for c in conditions])
    ax.set_yticks(range(len(seeds)), [f"seed{s}" for s in seeds])
    ax.set_title("UTR seed × unseen-topology performance", loc="left", weight="bold")
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            ax.text(j, i, f"{data[i, j]:.1f}", ha="center", va="center", fontsize=6, color="black")
    fig.colorbar(image, ax=ax, label="Mean return J", shrink=0.86)
    fig.tight_layout()
    save(fig, out, "g0_seed_topology_heatmap")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts", type=Path, default=Path("artifacts/g0"))
    args = parser.parse_args()
    args.artifacts = args.artifacts.resolve()
    out = args.artifacts / "figures"
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((args.artifacts / "topology_manifest.json").read_text(encoding="utf-8"))
    plot_suite(manifest, out)
    plot_per_topology(read_csv(args.artifacts / "topology_results.csv"), out)
    plot_structural_parameter(read_csv(args.artifacts / "topology_results.csv"), out)
    plot_heatmap(read_csv(args.artifacts / "seed_topology_results.csv"), out)
    print(f"wrote four G0 figures to {out}")


if __name__ == "__main__":
    main()
