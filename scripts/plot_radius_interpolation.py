from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt


METHODS = ["MAPPO", "GAT-MAPPO", "EA-RG-MAPPO-S"]
COLORS = {"MAPPO": "#386cb0", "GAT-MAPPO": "#fdb462", "EA-RG-MAPPO-S": "#1b9e77"}
MARKERS = {"MAPPO": "o", "GAT-MAPPO": "s", "EA-RG-MAPPO-S": "^"}


def load_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def plot_metric(rows: list[dict], metric: str, ylabel: str, out_png: Path) -> None:
    fig, ax = plt.subplots(figsize=(6.8, 4.1), dpi=190)
    for method in METHODS:
        part = [row for row in rows if row["method"] == method]
        part.sort(key=lambda row: float(row["radius"]))
        x = [float(row["radius"]) for row in part]
        y = [float(row[f"{metric}_mean"]) for row in part]
        yerr = [float(row[f"{metric}_std"]) for row in part]
        ax.errorbar(
            x,
            y,
            yerr=yerr,
            marker=MARKERS[method],
            color=COLORS[method],
            capsize=3,
            linewidth=2.0,
            markersize=5.8,
            label=method,
        )
    ax.set_xlabel("Unseen communication radius")
    ax.set_ylabel(ylabel)
    ax.set_xticks([5, 7, 9])
    ax.set_ylim(0.0, 1.02)
    ax.grid(True, linestyle="--", linewidth=0.6, alpha=0.45)
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot communication-radius interpolation diagnostic.")
    parser.add_argument("--summary-csv", type=Path, default=Path("results/radius_interpolation_summary.csv"))
    parser.add_argument("--out-dir", type=Path, default=Path("results/figures"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = load_rows(args.summary_csv)
    success_png = args.out_dir / "radius_interpolation_success_rate.png"
    collision_png = args.out_dir / "radius_interpolation_collision_rate.png"
    plot_metric(rows, "success", "Success rate", success_png)
    plot_metric(rows, "collision", "Collision rate", collision_png)
    print(success_png)
    print(collision_png)


if __name__ == "__main__":
    main()
