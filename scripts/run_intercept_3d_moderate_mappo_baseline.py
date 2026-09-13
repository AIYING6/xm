"""Train and evaluate a plain MAPPO baseline on the calibrated 3DOF moderate band.

This is a training-stack acceptance runner, not a paper experiment or a new
method.  It deliberately fixes the calibrated non-saturated condition and
uses ``no_graph`` so that no role-graph, curriculum, DRTP, or auxiliary loss
can enter the policy comparison later.
"""
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

from algorithms.ri_gmappo.simple_ri_gmappo import (  # noqa: E402
    RIGMAPPOAgent,
    RIGMAPPOConfig,
    eval_policy,
    load_matching_state_dict,
    make_env,
    train_ri_gmappo,
)


PROTOCOL = "INTERCEPT-3D-MODERATE-PLAIN-MAPPO-STACK-ACCEPTANCE-V1"
CONDITION = {
    "target_policy": "weaving_mild",
    "communication_dropout_prob": 0.25,
    "radar_dropout_prob": 0.15,
    "message_delay_steps": 4,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=5101)
    parser.add_argument("--updates", type=int, default=64)
    parser.add_argument("--num-envs", type=int, default=4)
    parser.add_argument("--rollout-steps", type=int, default=64)
    parser.add_argument("--eval-episodes", type=int, default=40)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "results" / "development" / "intercept_3d_moderate_plain_mappo" / "seed5101",
    )
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> RIGMAPPOConfig:
    return RIGMAPPOConfig(
        env_name="3d_intercept",
        seed=args.seed,
        num_envs=args.num_envs,
        rollout_steps=args.rollout_steps,
        updates=args.updates,
        hidden_dim=64,
        graph_encoder="no_graph",
        role_gate_mode="none",
        intent_coef=0.0,
        chain_aux_coef=0.0,
        target_policy=CONDITION["target_policy"],
        communication_dropout_prob=CONDITION["communication_dropout_prob"],
        radar_dropout_prob=CONDITION["radar_dropout_prob"],
        message_delay_steps=CONDITION["message_delay_steps"],
        strict_target_sensing=False,
        agent_target_info_bottleneck=False,
        relay_dependent_task=False,
        evaluation_enabled=True,
        eval_interval=max(1, min(16, args.updates)),
        eval_episodes=min(10, args.eval_episodes),
        eval_base_seed=610_000,
        save_interval=max(1, min(16, args.updates)),
        save_snapshots=True,
        out_dir=str(args.out_dir),
        device=args.device,
    )


def load_final_agent(cfg: RIGMAPPOConfig, checkpoint: Path) -> RIGMAPPOAgent:
    env = make_env(cfg, cfg.seed, training=False)
    _, share_obs, graph = env.reset()
    agent = RIGMAPPOAgent(
        obs_dim=env.obs_dim,
        node_feat_dim=graph["node_feat"].shape[-1],
        edge_feat_dim=graph["edge_feat"].shape[-1],
        share_obs_dim=share_obs.shape[-1],
        action_dim=env.action_dim,
        num_agents=env.num_agents,
        num_roles=max(4, int(np.max(graph["role"])) + 1),
        hidden_dim=cfg.hidden_dim,
        role_dim=cfg.role_dim,
        intent_dim=cfg.intent_dim,
        graph_encoder=cfg.graph_encoder,
        role_gate_mode=cfg.role_gate_mode,
        use_intent_context=False,
    ).to(cfg.device)
    load_matching_state_dict(agent, str(checkpoint), torch.device(cfg.device))
    agent.eval()
    return agent


def main() -> None:
    args = parse_args()
    if not args.execute:
        raise SystemExit("This runner changes state; pass --execute.")
    if args.updates <= 0 or args.num_envs <= 0 or args.rollout_steps <= 0:
        raise ValueError("updates, num-envs, and rollout-steps must be positive")
    if args.out_dir.exists() and any(args.out_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite existing run: {args.out_dir}")
    args.out_dir.mkdir(parents=True, exist_ok=False)
    cfg = build_config(args)
    manifest = {
        "protocol": PROTOCOL,
        "artifact_class": "DEVELOPMENT_ONLY_TRAINING_STACK_ACCEPTANCE",
        "purpose": "validate ordinary MAPPO training, checkpointing, and endpoint evaluation",
        "paper_evidence": False,
        "seed": args.seed,
        "environment_steps": args.updates * args.num_envs * args.rollout_steps,
        "condition": CONDITION,
        "fixed_items": ["environment_interface", "PPO", "reward", "observation", "action", "training_budget"],
        "method": {"name": "plain_mappo", "graph_encoder": "no_graph", "sampler": "uniform_fixed_condition"},
        "status": "running",
    }
    (args.out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    train_ri_gmappo(cfg)
    checkpoint = args.out_dir / "actor_critic_latest.pt"
    if not checkpoint.exists():
        raise FileNotFoundError(f"training completed without final checkpoint: {checkpoint}")
    endpoint_cfg = build_config(args)
    endpoint_cfg.eval_episodes = args.eval_episodes
    endpoint = eval_policy(load_final_agent(endpoint_cfg, checkpoint), endpoint_cfg, base_seed=620_000)
    with (args.out_dir / "endpoint_evaluation.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("protocol", "seed", "updates", "environment_steps", *endpoint.keys()))
        writer.writeheader()
        writer.writerow({"protocol": PROTOCOL, "seed": args.seed, "updates": args.updates,
                         "environment_steps": manifest["environment_steps"], **endpoint})
    manifest.update({"status": "completed", "checkpoint": checkpoint.name, "endpoint": endpoint})
    (args.out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
