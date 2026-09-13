"""Evaluate one fixed 3DOF-moderate checkpoint on the held-out endpoint band.

This utility never trains or changes a checkpoint.  It records a reproducible
development evaluation for a checkpoint selected on a separate training-time
selection band.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import eval_policy  # noqa: E402
from run_intercept_3d_moderate_mappo_baseline import build_config, load_final_agent  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--episodes", type=int, default=60)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--out-file", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.checkpoint.is_file():
        raise FileNotFoundError(args.checkpoint)
    if args.episodes <= 0:
        raise ValueError("episodes must be positive")
    if args.out_file.exists():
        raise FileExistsError(f"refusing to overwrite {args.out_file}")

    # build_config only relies on these runner arguments.  The selection band
    # is intentionally distinct from the held-out endpoint base seed below.
    args.updates = 128
    args.num_envs = 4
    args.rollout_steps = 64
    args.selection_eval_episodes = 20
    args.eval_episodes = args.episodes
    args.actor_learning_rate = 3e-5
    args.critic_learning_rate = 3e-4
    args.target_kl = None
    args.policy_update_guard_mode = "none"
    args.behavior_cloning_coef = 0.1
    args.init_checkpoint = None
    args.endpoint_checkpoint = "best"
    args.out_dir = args.out_file.parent
    cfg = build_config(args)
    endpoint = eval_policy(load_final_agent(cfg, args.checkpoint), cfg, base_seed=620_000)
    row = {
        "protocol": "INTERCEPT-3D-MODERATE-HELDOUT-CHECKPOINT-EVALUATION-V1",
        "artifact_class": "DEVELOPMENT_ONLY_READONLY_EVALUATION",
        "paper_evidence": False,
        "seed": args.seed,
        "checkpoint": str(args.checkpoint),
        "episodes": args.episodes,
        "selection_base_seed": 610_000,
        "endpoint_base_seed": 620_000,
        **endpoint,
    }
    args.out_file.parent.mkdir(parents=True, exist_ok=True)
    with args.out_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
    print(json.dumps(row, indent=2))


if __name__ == "__main__":
    main()
