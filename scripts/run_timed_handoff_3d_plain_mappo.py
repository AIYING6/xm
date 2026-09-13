"""Train a development-only, strict-local plain MAPPO baseline for G2.

The runner is intentionally method-free: no graph encoder, curriculum,
sampler, auxiliary task, behavior cloning, or handoff-value head is active.
Its sole purpose is to determine whether the G0-passing staged-handoff task is
learnable without being trivially saturated before a candidate method exists.
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

from algorithms.ri_gmappo.simple_ri_gmappo import (
    RIGMAPPOAgent,
    RIGMAPPOConfig,
    eval_policy,
    load_matching_state_dict,
    make_env,
    train_ri_gmappo,
)


PROTOCOL = "TIMED-HANDOFF-3D-PLAIN-MAPPO-G2-DEVELOPMENT-V1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--updates", type=int, default=48)
    parser.add_argument("--num-envs", type=int, default=4)
    parser.add_argument("--rollout-steps", type=int, default=64)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--selection-eval-episodes", type=int, default=16)
    parser.add_argument("--endpoint-eval-episodes", type=int, default=40)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args()


def build_config(args: argparse.Namespace, *, env_name: str = "timed_handoff_3d") -> RIGMAPPOConfig:
    return RIGMAPPOConfig(
        env_name=env_name,
        seed=args.seed,
        num_envs=args.num_envs,
        rollout_steps=args.rollout_steps,
        updates=args.updates,
        hidden_dim=args.hidden_dim,
        graph_encoder="no_graph",
        role_gate_mode="none",
        # In this staged macro task only the relay commitment is wired into
        # the physical controller.  The two other UAVs remain in the critic
        # state, but their ignored macro placeholders must not enter PPO's
        # actor likelihood or entropy objective.
        actor_action_mask_mode=("relay_only" if env_name == "commitment_handoff_3d" else "all_agents"),
        intent_coef=0.0,
        chain_aux_coef=0.0,
        behavior_cloning_coef=0.0,
        behavior_cloning_teacher="none",
        target_policy="weaving_mild",
        communication_dropout_prob=0.0,
        radar_dropout_prob=0.0,
        message_delay_steps=0,
        max_target_message_age_steps=10,
        timed_handoff_context_mode="balanced",
        handoff_authorization_start_step=12,
        handoff_authorization_deadline=28,
        handoff_branch_step=40,
        handoff_authorization_hold_steps=8,
        handoff_refresh_hold_steps=16,
        handoff_corridor_radius=900.0,
        handoff_future_corridor_lateral_offset=1_500.0,
        handoff_commitment_action_repeat=8,
        handoff_legacy_intercept_reward_weight=0.0,
        handoff_prebranch_target_policy="weaving_mild",
        handoff_postbranch_target_policy="weaving_mild",
        # Match the G0-verified physical contract.  The staged service
        # decision is only useful if both public routes are reachable under
        # the same target-initialisation geometry used by the scripted
        # decision-switch controllers.
        target_init_range_scale=0.65,
        evaluation_enabled=True,
        eval_interval=max(1, min(12, args.updates)),
        eval_episodes=args.selection_eval_episodes,
        eval_base_seed=730_000,
        save_interval=max(1, min(12, args.updates)),
        save_snapshots=True,
        out_dir=str(args.out_dir),
        device=args.device,
    )


def load_agent(cfg: RIGMAPPOConfig, checkpoint: Path) -> RIGMAPPOAgent:
    env = make_env(cfg, cfg.seed, training=False)
    obs, share_obs, graph = env.reset()
    agent = RIGMAPPOAgent(
        obs_dim=obs.shape[-1],
        node_feat_dim=graph["node_feat"].shape[-1],
        edge_feat_dim=graph["edge_feat"].shape[-1],
        share_obs_dim=share_obs.shape[-1],
        action_dim=env.action_dim,
        num_agents=env.num_agents,
        num_roles=max(4, int(np.max(graph["role"])) + 1),
        hidden_dim=cfg.hidden_dim,
        role_dim=cfg.role_dim,
        intent_dim=cfg.intent_dim,
        graph_encoder="no_graph",
        role_gate_mode="none",
        use_intent_context=False,
    ).to(cfg.device)
    load_matching_state_dict(agent, str(checkpoint), torch.device(cfg.device))
    return agent.eval()


def main() -> None:
    args = parse_args()
    if not args.execute:
        raise SystemExit("pass --execute because this command creates a development run")
    if min(args.updates, args.num_envs, args.rollout_steps, args.selection_eval_episodes, args.endpoint_eval_episodes) <= 0:
        raise ValueError("all training and evaluation counts must be positive")
    if args.out_dir.exists():
        raise FileExistsError(f"refusing to overwrite {args.out_dir}")
    args.out_dir.mkdir(parents=True)
    cfg = build_config(args)
    manifest = {
        "protocol": PROTOCOL,
        "artifact_class": "DEVELOPMENT_ONLY_G2_LEARNABILITY_PILOT",
        "paper_evidence": False,
        "purpose": "test whether capacity-controlled plain MAPPO is learnable but non-saturated on the G0-passing task",
        "seed": args.seed,
        "environment_steps": args.updates * args.num_envs * args.rollout_steps,
        "task_context_schedule": "balanced deterministic parity across environment seeds",
        "fixed_task": {
            "authorization_window": [12, 28],
            "branch_step": 40,
            "current_and_future_service_radius": 900.0,
            "future_lateral_offset": 1_500.0,
            "legacy_intercept_reward_weight": 0.0,
            "service_progress_reward_weight": 1.0,
        },
        "method": "plain capacity-controlled MLP MAPPO; no graph, no sampler, no auxiliary loss",
        "status": "running",
    }
    (args.out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    train_ri_gmappo(cfg)
    checkpoint = args.out_dir / "actor_critic_latest.pt"
    if not checkpoint.is_file():
        raise FileNotFoundError(f"missing final checkpoint: {checkpoint}")
    endpoint_cfg = build_config(args)
    endpoint_cfg.eval_episodes = args.endpoint_eval_episodes
    endpoint = eval_policy(load_agent(endpoint_cfg, checkpoint), endpoint_cfg, base_seed=740_000)
    row = {
        "protocol": PROTOCOL,
        "seed": args.seed,
        "updates": args.updates,
        "environment_steps": manifest["environment_steps"],
        **endpoint,
    }
    with (args.out_dir / "endpoint_evaluation.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
    manifest.update({"status": "completed", "checkpoint": checkpoint.name, "endpoint": endpoint})
    (args.out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
