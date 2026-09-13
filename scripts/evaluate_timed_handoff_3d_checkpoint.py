"""Read-only, context-stratified endpoint evaluation for timed-handoff MAPPO."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from envs.timed_handoff_intercept_3d_env import HANDOFF_CONTEXTS
from scripts.run_timed_handoff_3d_plain_mappo import build_config, load_agent
from algorithms.ri_gmappo.simple_ri_gmappo import make_env, stack_graphs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--episodes-per-context", type=int, default=40)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--env-name", choices=("timed_handoff_3d", "commitment_handoff_3d"), default="timed_handoff_3d")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--out-file", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.checkpoint.is_file():
        raise FileNotFoundError(args.checkpoint)
    if args.out_file.exists():
        raise FileExistsError(f"refusing to overwrite {args.out_file}")
    if args.episodes_per_context <= 0:
        raise ValueError("episodes-per-context must be positive")
    # The runner's config builder needs only these fields; no training occurs.
    args.updates = 1
    args.num_envs = 1
    args.rollout_steps = 1
    args.selection_eval_episodes = 1
    args.endpoint_eval_episodes = args.episodes_per_context
    args.out_dir = args.out_file.parent
    cfg = build_config(args, env_name=args.env_name)
    cfg.timed_handoff_context_mode = "balanced"
    agent = load_agent(cfg, args.checkpoint)
    device = torch.device(cfg.device)
    rows: list[dict[str, object]] = []
    agent.eval()
    with torch.no_grad():
        for context_index, context in enumerate(HANDOFF_CONTEXTS):
            for episode in range(args.episodes_per_context):
                env_seed = 750_000 + context_index * 10_000 + episode
                env_cfg = build_config(args, env_name=args.env_name)
                env_cfg.timed_handoff_context_mode = context
                env = make_env(env_cfg, env_seed, training=False)
                obs, share_obs, graph = env.reset()
                while True:
                    packed = stack_graphs([graph])
                    actions, *_ = agent.get_action_and_value(
                        torch.as_tensor(obs[None, ...], dtype=torch.float32, device=device),
                        torch.as_tensor(packed["node_feat"], dtype=torch.float32, device=device),
                        torch.as_tensor(packed["edge_feat"], dtype=torch.float32, device=device),
                        torch.as_tensor(packed["role"], dtype=torch.long, device=device),
                        torch.as_tensor(packed["adj"], dtype=torch.float32, device=device),
                        torch.as_tensor(share_obs[None, ...], dtype=torch.float32, device=device),
                        relation_adj=torch.as_tensor(packed["relation_adj"], dtype=torch.float32, device=device),
                        deterministic=True,
                    )
                    obs, share_obs, graph, _, dones, info = env.step(actions.squeeze(0).cpu().numpy())
                    if np.all(dones):
                        rows.append({"context": context, "episode": episode, **info})
                        break
    fields = ("context", "episode", "success", "timeout", "collision", "handoff_success", "authorization_handoff_observed", "postbranch_refresh_observed", "handoff_service_progress", "step")
    args.out_file.parent.mkdir(parents=True, exist_ok=True)
    with args.out_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    summary = {}
    for context in HANDOFF_CONTEXTS:
        cell = [row for row in rows if row["context"] == context]
        summary[context] = {
            "n": len(cell),
            "success_rate": float(np.mean([row["success"] for row in cell])),
            "timeout_rate": float(np.mean([row["timeout"] for row in cell])),
            "collision_rate": float(np.mean([row["collision"] for row in cell])),
            "mean_terminal_service_progress": float(np.mean([row["handoff_service_progress"] for row in cell])),
        }
    report = {"protocol": "TIMED-HANDOFF-3D-CONTEXT-STRATIFIED-READONLY-EVALUATION-V1", "env_name": args.env_name, "checkpoint": str(args.checkpoint), "seed": args.seed, "summary": summary}
    args.out_file.with_suffix(".json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
