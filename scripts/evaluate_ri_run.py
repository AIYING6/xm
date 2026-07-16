from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.evaluate_ri_gmappo import evaluate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--episodes", type=int, default=100)
    parser.add_argument("--target-policy", type=str, default="mixed")
    parser.add_argument("--target-speed", type=float, default=0.75)
    parser.add_argument("--radii", type=float, nargs="+", default=[4.0, 6.0, 8.0, 10.0])
    parser.add_argument("--detach-intent", action="store_true")
    parser.add_argument("--oracle-intent", action="store_true")
    parser.add_argument("--stochastic", action="store_true")
    parser.add_argument("--out-csv", type=Path, default=None)
    args = parser.parse_args()

    checkpoints = []
    for name in ["actor_critic_best.pt", "actor_critic_latest.pt"]:
        path = args.run_dir / name
        if path.exists():
            checkpoints.append((name.replace("actor_critic_", "").replace(".pt", ""), path))
    if not checkpoints:
        raise FileNotFoundError(f"No actor_critic_best.pt or actor_critic_latest.pt under {args.run_dir}")

    rows = []
    for ckpt_name, ckpt_path in checkpoints:
        for radius in args.radii:
            result = evaluate(
                ckpt_path,
                args.episodes,
                args.target_policy,
                args.target_speed,
                radius,
                not args.stochastic,
                args.detach_intent,
                args.oracle_intent,
            )
            rows.append(
                {
                    "run_dir": str(args.run_dir),
                    "checkpoint": ckpt_name,
                    "radius": radius,
                    "success_rate": result["success_rate"],
                    "collision_rate": result["collision_rate"],
                    "timeout_rate": result["timeout_rate"],
                    "avg_steps": result["avg_steps"],
                    "avg_mean_distance": result["avg_mean_distance"],
                    "intent_accuracy": result["intent_accuracy"],
                }
            )
            print(rows[-1], flush=True)

    out_csv = args.out_csv or (args.run_dir / "ri_run_eval.csv")
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"saved: {out_csv}")


if __name__ == "__main__":
    main()
