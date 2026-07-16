from __future__ import annotations

import csv
import re
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def seed_from_run_dir(run_dir: str) -> int:
    match = re.search(r"seed(\d+)", run_dir)
    if match:
        return int(match.group(1))
    return 0


def load_rows() -> list[dict]:
    rows: list[dict] = []

    for row in read_csv(RESULTS / "mappo_comm_multi_seed_eval.csv"):
        rows.append(
            {
                "method": "MAPPO",
                "seed": seed_from_run_dir(row["run_dir"]),
                "radius": float(row["radius"]),
                "success_rate": float(row["success_rate"]),
                "collision_rate": float(row["collision_rate"]),
                "timeout_rate": float(row["timeout_rate"]),
                "avg_steps": float(row["avg_steps"]),
            }
        )

    for row in read_csv(RESULTS / "gat_comm_multi_seed_eval.csv"):
        rows.append(
            {
                "method": "GAT-MAPPO",
                "seed": seed_from_run_dir(row["run_dir"]),
                "radius": float(row["radius"]),
                "success_rate": float(row["success_rate"]),
                "collision_rate": float(row["collision_rate"]),
                "timeout_rate": float(row["timeout_rate"]),
                "avg_steps": float(row["avg_steps"]),
            }
        )

    for seed in [0, 1, 2]:
        path = RESULTS / f"ri_gmappo_edge_stage2_rand_seed{seed}_20" / "ri_run_eval.csv"
        for row in read_csv(path):
            if row["checkpoint"] != "latest":
                continue
            rows.append(
                {
                    "method": "EA-RG-MAPPO-S",
                    "seed": seed,
                    "radius": float(row["radius"]),
                    "success_rate": float(row["success_rate"]),
                    "collision_rate": float(row["collision_rate"]),
                    "timeout_rate": float(row["timeout_rate"]),
                    "avg_steps": float(row["avg_steps"]),
                }
            )

    return sorted(rows, key=lambda r: (r["method"], r["radius"], r["seed"]))


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: list[dict], path: Path) -> None:
    lines = [
        "# Per-Seed Communication Appendix",
        "",
        "Evaluation setting:",
        "",
        "```text",
        "target_policy = mixed",
        "target_speed = 0.75",
        "episodes = 100",
        "communication_radius = 4, 6, 8, 10",
        "```",
        "",
        "| Method | Seed | Radius | Success | Collision | Timeout | Avg steps |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['method']} | {row['seed']} | {row['radius']:.0f} | "
            f"{row['success_rate']:.2f} | {row['collision_rate']:.2f} | "
            f"{row['timeout_rate']:.2f} | {row['avg_steps']:.2f} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def plot_metric(rows: list[dict], metric: str, ylabel: str, out_png: Path) -> None:
    methods = ["MAPPO", "GAT-MAPPO", "EA-RG-MAPPO-S"]
    colors = {"MAPPO": "tab:blue", "GAT-MAPPO": "tab:orange", "EA-RG-MAPPO-S": "tab:green"}
    offsets = {"MAPPO": -0.18, "GAT-MAPPO": 0.0, "EA-RG-MAPPO-S": 0.18}
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    for method in methods:
        method_rows = [r for r in rows if r["method"] == method]
        xs = [r["radius"] + offsets[method] for r in method_rows]
        ys = [r[metric] for r in method_rows]
        ax.scatter(xs, ys, label=method, color=colors[method], alpha=0.85, s=42)
        radii = sorted({r["radius"] for r in method_rows})
        means = [
            sum(r[metric] for r in method_rows if r["radius"] == radius)
            / len([r for r in method_rows if r["radius"] == radius])
            for radius in radii
        ]
        ax.plot(radii, means, color=colors[method], linewidth=1.8, alpha=0.8)
    ax.set_xticks([4, 6, 8, 10])
    ax.set_xlabel("Communication radius")
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=180)
    plt.close(fig)


def main() -> None:
    rows = load_rows()
    write_csv(rows, RESULTS / "per_seed_comm_appendix.csv")
    write_markdown(rows, RESULTS / "per_seed_comm_appendix.md")
    plot_metric(rows, "success_rate", "Success rate", RESULTS / "figures" / "per_seed_success_scatter.png")
    plot_metric(rows, "collision_rate", "Collision rate", RESULTS / "figures" / "per_seed_collision_scatter.png")
    print(RESULTS / "per_seed_comm_appendix.csv")
    print(RESULTS / "per_seed_comm_appendix.md")
    print(RESULTS / "figures" / "per_seed_success_scatter.png")
    print(RESULTS / "figures" / "per_seed_collision_scatter.png")


if __name__ == "__main__":
    main()
