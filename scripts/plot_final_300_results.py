from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "results" / "final_comm_300_summary.csv"
OUT_DIR = ROOT / "results" / "figures"


def read_rows() -> list[dict]:
    with CSV_PATH.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def plot_metric(rows: list[dict], metric: str, ylabel: str, out_name: str) -> Path:
    import matplotlib.pyplot as plt

    methods = ["MAPPO", "GAT-MAPPO", "EA-RG-MAPPO-S"]
    markers = {"MAPPO": "o", "GAT-MAPPO": "s", "EA-RG-MAPPO-S": "^"}
    colors = {"MAPPO": "#386cb0", "GAT-MAPPO": "#fdb462", "EA-RG-MAPPO-S": "#1b9e77"}
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(7.2, 4.3), dpi=180)
    for method in methods:
        part = [r for r in rows if r["method"] == method]
        part.sort(key=lambda r: float(r["radius"]))
        x = [float(r["radius"]) for r in part]
        y = [float(r[f"{metric}_mean"]) for r in part]
        yerr = [float(r[f"{metric}_std"]) for r in part]
        ax.errorbar(
            x,
            y,
            yerr=yerr,
            marker=markers[method],
            color=colors[method],
            capsize=3,
            linewidth=2.0,
            markersize=6,
            label=method,
        )

    ax.set_xlabel("Communication radius")
    ax.set_ylabel(ylabel)
    ax.set_xticks([4, 6, 8, 10])
    ax.set_ylim(0.0, 1.02)
    ax.grid(True, linestyle="--", linewidth=0.6, alpha=0.45)
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    out_path = OUT_DIR / out_name
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def main() -> None:
    rows = read_rows()
    print(plot_metric(rows, "success", "Success rate", "final_300_success_rate.png"))
    print(plot_metric(rows, "collision", "Collision rate", "final_300_collision_rate.png"))


if __name__ == "__main__":
    main()
