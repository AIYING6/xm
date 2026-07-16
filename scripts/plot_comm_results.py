from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "results" / "paper_comm_results.csv"
OUT_DIR = ROOT / "results" / "figures"


def read_rows():
    with CSV_PATH.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def plot_metric(rows, metric: str, ylabel: str, out_name: str) -> Path:
    import matplotlib.pyplot as plt

    methods = [
        "MAPPO",
        "GAT-MAPPO",
        "RI no-edge",
        "RI edge fixed-r8",
        "RI edge staged",
    ]
    markers = ["o", "s", "^", "D", "x"]
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=160)
    for method, marker in zip(methods, markers):
        part = [r for r in rows if r["method"] == method]
        part.sort(key=lambda r: float(r["radius"]))
        x = [float(r["radius"]) for r in part]
        y = [float(r[f"{metric}_mean"]) for r in part]
        yerr = [float(r[f"{metric}_std"]) if r[f"{metric}_std"] else 0.0 for r in part]
        ax.errorbar(x, y, yerr=yerr, marker=marker, capsize=3, linewidth=1.8, label=method)

    ax.set_xlabel("Communication radius")
    ax.set_ylabel(ylabel)
    ax.set_xticks([4, 6, 8, 10])
    ax.set_ylim(0.0, 1.02)
    ax.grid(True, linestyle="--", linewidth=0.6, alpha=0.5)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    out_path = OUT_DIR / out_name
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def main() -> None:
    rows = read_rows()
    success_path = plot_metric(rows, "success", "Success rate", "comm_success_rate.png")
    collision_path = plot_metric(rows, "collision", "Collision rate", "comm_collision_rate.png")
    print(success_path)
    print(collision_path)


if __name__ == "__main__":
    main()
