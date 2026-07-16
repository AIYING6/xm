from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt


METHODS = ["MAPPO", "GAT-MAPPO", "EA-RG-MAPPO-S"]
COLORS = {"MAPPO": "#386cb0", "GAT-MAPPO": "#fdb462", "EA-RG-MAPPO-S": "#1b9e77"}
MARKERS = {"MAPPO": "o", "GAT-MAPPO": "s", "EA-RG-MAPPO-S": "^"}
LINESTYLES = {4.0: "-", 8.0: "--"}


def load_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def plot_metric(rows: list[dict], metric: str, ylabel: str, out_png: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.4, 4.35), dpi=190)
    radii = sorted({float(row["radius"]) for row in rows})
    for radius in radii:
        for method in METHODS:
            part = [
                row
                for row in rows
                if row["method"] == method and abs(float(row["radius"]) - radius) < 1e-6
            ]
            part.sort(key=lambda row: float(row["comm_dropout_prob"]))
            x = [float(row["comm_dropout_prob"]) for row in part]
            y = [float(row[f"{metric}_mean"]) for row in part]
            yerr = [float(row[f"{metric}_std"]) for row in part]
            ax.errorbar(
                x,
                y,
                yerr=yerr,
                marker=MARKERS[method],
                linestyle=LINESTYLES.get(radius, "-"),
                color=COLORS[method],
                alpha=0.92,
                capsize=3,
                linewidth=2.0,
                markersize=5.8,
                label=f"{method}, R={radius:g}",
            )
    ax.set_xlabel("Communication dropout probability")
    ax.set_ylabel(ylabel)
    ax.set_xticks([0.0, 0.25, 0.5])
    ax.set_ylim(0.0, 1.02)
    ax.grid(True, linestyle="--", linewidth=0.6, alpha=0.45)
    ax.legend(frameon=False, fontsize=8, ncol=2)
    fig.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot communication-dropout robustness results.")
    parser.add_argument("--summary-csv", type=Path, default=Path("results/comm_dropout_robustness_summary.csv"))
    parser.add_argument("--out-dir", type=Path, default=Path("results/figures"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = load_rows(args.summary_csv)
    success_png = args.out_dir / "comm_dropout_success_rate.png"
    collision_png = args.out_dir / "comm_dropout_collision_rate.png"
    plot_metric(rows, "success", "Success rate", success_png)
    plot_metric(rows, "collision", "Collision rate", collision_png)
    print(success_png)
    print(collision_png)


if __name__ == "__main__":
    main()
