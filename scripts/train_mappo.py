from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.mappo import MAPPOAgent, train_mappo
from algorithms.mappo.simple_mappo import MAPPOConfig


def parse_args() -> MAPPOConfig:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--num-envs", type=int, default=8)
    parser.add_argument("--rollout-steps", type=int, default=128)
    parser.add_argument("--updates", type=int, default=200)
    parser.add_argument("--hidden-dim", type=int, default=128)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--eval-interval", type=int, default=10)
    parser.add_argument("--eval-episodes", type=int, default=20)
    parser.add_argument("--target-policy", type=str, default="mixed")
    parser.add_argument("--target-speed", type=float, default=0.75)
    parser.add_argument("--communication-radius", type=float, default=8.0)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--out-dir", type=str, default=str(ROOT / "results" / "mappo"))
    parser.add_argument("--save-interval", type=int, default=10)
    parser.add_argument("--resume", type=str, default=None)
    args = parser.parse_args()
    return MAPPOConfig(
        seed=args.seed,
        num_envs=args.num_envs,
        rollout_steps=args.rollout_steps,
        updates=args.updates,
        hidden_dim=args.hidden_dim,
        lr=args.lr,
        eval_interval=args.eval_interval,
        eval_episodes=args.eval_episodes,
        target_policy=args.target_policy,
        target_speed=args.target_speed,
        communication_radius=args.communication_radius,
        device=args.device,
        out_dir=args.out_dir,
        save_interval=args.save_interval,
        resume=args.resume,
    )


def main() -> None:
    cfg = parse_args()
    log_path = train_mappo(cfg)
    print(f"training log: {log_path}")


if __name__ == "__main__":
    main()
