from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.evaluate_gat_model import evaluate as evaluate_gat
from scripts.evaluate_model import evaluate as evaluate_mappo
from scripts.evaluate_ri_gmappo import evaluate as evaluate_ri


FINAL_RUNS = [
    {
        "method": "MAPPO",
        "seed": 0,
        "kind": "mappo",
        "model": Path("results/mappo_curriculum_slow_150/actor_critic_latest.pt"),
    },
    {
        "method": "MAPPO",
        "seed": 1,
        "kind": "mappo",
        "model": Path("results/mappo_curriculum_slow_seed1_150/actor_critic_latest.pt"),
    },
    {
        "method": "MAPPO",
        "seed": 2,
        "kind": "mappo",
        "model": Path("results/mappo_curriculum_slow_seed2_150/actor_critic_latest.pt"),
    },
    {
        "method": "GAT-MAPPO",
        "seed": 0,
        "kind": "gat",
        "model": Path("results/gat_mappo_hybrid_slow_60_plus90/actor_critic_latest.pt"),
    },
    {
        "method": "GAT-MAPPO",
        "seed": 1,
        "kind": "gat",
        "model": Path("results/gat_mappo_hybrid_slow_seed1_60_plus90/actor_critic_latest.pt"),
    },
    {
        "method": "GAT-MAPPO",
        "seed": 2,
        "kind": "gat",
        "model": Path("results/gat_mappo_hybrid_slow_seed2_60_plus90/actor_critic_latest.pt"),
    },
    {
        "method": "EA-RG-MAPPO-S",
        "seed": 0,
        "kind": "ri",
        "model": Path("results/ri_gmappo_edge_stage2_rand_seed0_20/actor_critic_latest.pt"),
    },
    {
        "method": "EA-RG-MAPPO-S",
        "seed": 1,
        "kind": "ri",
        "model": Path("results/ri_gmappo_edge_stage2_rand_seed1_20/actor_critic_latest.pt"),
    },
    {
        "method": "EA-RG-MAPPO-S",
        "seed": 2,
        "kind": "ri",
        "model": Path("results/ri_gmappo_edge_stage2_rand_seed2_20/actor_critic_latest.pt"),
    },
]


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def std(values: list[float]) -> float:
    m = mean(values)
    return math.sqrt(sum((v - m) ** 2 for v in values) / len(values))


def evaluate_run(run: dict, episodes: int, radius: float, target_policy: str, target_speed: float) -> dict:
    model = ROOT / run["model"]
    if run["kind"] == "mappo":
        result = evaluate_mappo(model, episodes, target_policy, target_speed, radius, True)
    elif run["kind"] == "gat":
        result = evaluate_gat(model, episodes, target_policy, target_speed, radius, True)
    elif run["kind"] == "ri":
        result = evaluate_ri(model, episodes, target_policy, target_speed, radius, True, True, False)
    else:
        raise ValueError(f"unknown run kind: {run['kind']}")
    return {
        "method": run["method"],
        "seed": run["seed"],
        "kind": run["kind"],
        "model": str(run["model"]),
        "episodes": episodes,
        "target_policy": target_policy,
        "target_speed": target_speed,
        "radius": radius,
        "success_rate": result["success_rate"],
        "collision_rate": result["collision_rate"],
        "timeout_rate": result["timeout_rate"],
        "avg_steps": result["avg_steps"],
        "avg_mean_distance": result["avg_mean_distance"],
        "intent_accuracy": result.get("intent_accuracy", ""),
    }


def write_rows(rows: list[dict], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows: list[dict]) -> list[dict]:
    summary = []
    methods = list(dict.fromkeys(row["method"] for row in rows))
    radii = sorted({float(row["radius"]) for row in rows})
    for method in methods:
        for radius in radii:
            group = [row for row in rows if row["method"] == method and float(row["radius"]) == radius]
            summary.append(
                {
                    "method": method,
                    "episodes": group[0]["episodes"],
                    "radius": radius,
                    "success_mean": mean([float(row["success_rate"]) for row in group]),
                    "success_std": std([float(row["success_rate"]) for row in group]),
                    "collision_mean": mean([float(row["collision_rate"]) for row in group]),
                    "collision_std": std([float(row["collision_rate"]) for row in group]),
                    "timeout_mean": mean([float(row["timeout_rate"]) for row in group]),
                    "timeout_std": std([float(row["timeout_rate"]) for row in group]),
                    "avg_steps_mean": mean([float(row["avg_steps"]) for row in group]),
                    "avg_steps_std": std([float(row["avg_steps"]) for row in group]),
                    "n": len(group),
                }
            )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=int, default=300)
    parser.add_argument("--target-policy", type=str, default="mixed")
    parser.add_argument("--target-speed", type=float, default=0.75)
    parser.add_argument("--radii", type=float, nargs="+", default=[4.0, 6.0, 8.0, 10.0])
    parser.add_argument("--out-csv", type=Path, default=Path("results/final_comm_300_eval.csv"))
    parser.add_argument("--summary-csv", type=Path, default=Path("results/final_comm_300_summary.csv"))
    args = parser.parse_args()

    rows = []
    for run in FINAL_RUNS:
        for radius in args.radii:
            row = evaluate_run(run, args.episodes, radius, args.target_policy, args.target_speed)
            rows.append(row)
            print(row, flush=True)
            write_rows(rows, args.out_csv)

    summary = summarize(rows)
    write_rows(summary, args.summary_csv)
    print(f"saved: {args.out_csv}")
    print(f"saved: {args.summary_csv}")


if __name__ == "__main__":
    main()
