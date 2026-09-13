"""Isolate one legal handoff context to diagnose G2 learnability.

This development-only control has the same plant, macro actions, PPO,
reward, architecture and budget as the balanced G2 pilot.  It changes only
the reset-time context schedule, allowing us to distinguish a difficult
single-context credit path from interference between two opposing decisions.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import eval_policy, train_ri_gmappo
from envs.timed_handoff_intercept_3d_env import HANDOFF_CONTEXTS
from scripts.run_timed_handoff_3d_plain_mappo import build_config, load_agent


PROTOCOL = "COMMITMENT-HANDOFF-3D-G2-CONTEXT-ISOLATION-DIAGNOSTIC-V1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--context", choices=HANDOFF_CONTEXTS, required=True)
    parser.add_argument("--updates", type=int, default=96)
    parser.add_argument("--num-envs", type=int, default=4)
    parser.add_argument("--rollout-steps", type=int, default=64)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--selection-eval-episodes", type=int, default=16)
    parser.add_argument("--endpoint-eval-episodes", type=int, default=40)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.execute:
        raise SystemExit("pass --execute because this command creates a development diagnostic")
    if min(args.updates, args.num_envs, args.rollout_steps, args.selection_eval_episodes, args.endpoint_eval_episodes) <= 0:
        raise ValueError("all training and evaluation counts must be positive")
    if args.out_dir.exists():
        raise FileExistsError(f"refusing to overwrite {args.out_dir}")
    args.out_dir.mkdir(parents=True)
    cfg = build_config(args, env_name="commitment_handoff_3d")
    cfg.timed_handoff_context_mode = args.context
    manifest = {
        "protocol": PROTOCOL,
        "artifact_class": "DEVELOPMENT_ONLY_G2_CONTEXT_ISOLATION_DIAGNOSTIC",
        "paper_evidence": False,
        "purpose": "identify whether the current-authorization branch is learnable in isolation",
        "seed": args.seed,
        "context": args.context,
        "environment_steps": args.updates * args.num_envs * args.rollout_steps,
        "fixed_controls": ["3DOF plant", "binary relay commitments", "plain MLP MAPPO", "PPO", "reward", "budget"],
        "only_changed_factor": "reset-time handoff context schedule",
        "status": "running",
    }
    (args.out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    train_ri_gmappo(cfg)
    checkpoint = args.out_dir / "actor_critic_latest.pt"
    if not checkpoint.is_file():
        raise FileNotFoundError(f"missing final checkpoint: {checkpoint}")
    endpoint_cfg = build_config(args, env_name="commitment_handoff_3d")
    endpoint_cfg.timed_handoff_context_mode = args.context
    endpoint_cfg.eval_episodes = args.endpoint_eval_episodes
    endpoint = eval_policy(load_agent(endpoint_cfg, checkpoint), endpoint_cfg, base_seed=770_000)
    row = {"protocol": PROTOCOL, "seed": args.seed, "context": args.context, "updates": args.updates, **endpoint}
    with (args.out_dir / "endpoint_evaluation.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
    manifest.update({"status": "completed", "checkpoint": checkpoint.name, "endpoint": endpoint})
    (args.out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
