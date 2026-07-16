from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ABLATION_LABELS = {
    "zero_rel_pos": "pos",
    "zero_distance": "dist",
    "zero_bearing": "bearing",
    "zero_rel_velocity": "rel vel",
    "zero_comm_target_flags": "comm/target",
    "zero_all_edge_features": "all",
}


def load_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def build_delta_rows(rows: list[dict]) -> list[dict]:
    baselines = {float(row["radius"]): row for row in rows if row["ablation"] == "none"}
    delta_rows = []
    for row in rows:
        if row["ablation"] == "none":
            continue
        radius = float(row["radius"])
        base = baselines[radius]
        delta_rows.append(
            {
                "radius": radius,
                "ablation": row["ablation"],
                "delta_success": float(row["success_mean"]) - float(base["success_mean"]),
                "delta_collision": float(row["collision_mean"]) - float(base["collision_mean"]),
            }
        )
    return delta_rows


def plot(delta_rows: list[dict], out_png: Path) -> None:
    radii = sorted({row["radius"] for row in delta_rows})
    ablations = [key for key in ABLATION_LABELS if any(row["ablation"] == key for row in delta_rows)]

    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.2), sharex=True)
    width = 0.36
    x = np.arange(len(ablations))
    colors = ["#2878b5", "#c85200"]

    for ridx, radius in enumerate(radii):
        subset = {row["ablation"]: row for row in delta_rows if row["radius"] == radius}
        offset = (ridx - (len(radii) - 1) / 2.0) * width
        success_values = [subset[a]["delta_success"] for a in ablations]
        collision_values = [subset[a]["delta_collision"] for a in ablations]
        label = f"R={radius:g}"
        axes[0].bar(x + offset, success_values, width=width, label=label, color=colors[ridx % len(colors)], alpha=0.88)
        axes[1].bar(x + offset, collision_values, width=width, label=label, color=colors[ridx % len(colors)], alpha=0.88)

    axes[0].axhline(0.0, color="#333333", linewidth=0.9)
    axes[1].axhline(0.0, color="#333333", linewidth=0.9)
    axes[0].set_title("Success Rate Change")
    axes[1].set_title("Collision Rate Change")
    axes[0].set_ylabel("Delta vs. no masking")
    axes[0].set_xticks(x)
    axes[1].set_xticks(x)
    labels = [ABLATION_LABELS[a] for a in ablations]
    for ax in axes:
        ax.set_xticklabels(labels, rotation=25, ha="right")
        ax.grid(axis="y", linestyle="--", linewidth=0.6, alpha=0.45)
        ax.legend(frameon=False)

    fig.suptitle("Evaluation-Time Edge Feature Masking Diagnostic", y=1.02, fontsize=12)
    fig.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=220, bbox_inches="tight")
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot edge feature evaluation-time ablation deltas.")
    parser.add_argument("--summary-csv", type=Path, default=Path("results/edge_feature_ablation_summary.csv"))
    parser.add_argument("--out-png", type=Path, default=Path("results/figures/edge_feature_ablation_delta.png"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = load_rows(args.summary_csv)
    delta_rows = build_delta_rows(rows)
    plot(delta_rows, args.out_png)
    print(f"saved: {args.out_png}")


if __name__ == "__main__":
    main()
