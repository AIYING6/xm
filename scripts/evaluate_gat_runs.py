from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.evaluate_gat_model import evaluate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dirs", type=Path, nargs="+", required=True)
    parser.add_argument("--episodes", type=int, default=100)
    parser.add_argument("--target-policy", type=str, default="mixed")
    parser.add_argument("--target-speed", type=float, default=0.75)
    parser.add_argument("--radii", type=float, nargs="+", default=[4.0, 6.0, 8.0, 10.0])
    parser.add_argument("--checkpoint", choices=["best", "latest"], default="latest")
    parser.add_argument("--stochastic", action="store_true")
    parser.add_argument("--out-csv", type=Path, default=Path("results/gat_comm_multi_seed_eval.csv"))
    args = parser.parse_args()

    rows = []
    ckpt_name = f"actor_critic_{args.checkpoint}.pt"
    for run_dir in args.run_dirs:
        ckpt_path = run_dir / ckpt_name
        if not ckpt_path.exists():
            raise FileNotFoundError(f"Missing checkpoint: {ckpt_path}")

        for radius in args.radii:
            result = evaluate(
                ckpt_path,
                args.episodes,
                args.target_policy,
                args.target_speed,
                radius,
                not args.stochastic,
            )
            row = {
                "run_dir": str(run_dir),
                "checkpoint": args.checkpoint,
                "radius": radius,
                "success_rate": result["success_rate"],
                "collision_rate": result["collision_rate"],
                "timeout_rate": result["timeout_rate"],
                "avg_steps": result["avg_steps"],
                "avg_mean_distance": result["avg_mean_distance"],
            }
            rows.append(row)
            print(row, flush=True)

    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.out_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"saved: {args.out_csv}")


if __name__ == "__main__":
    main()
