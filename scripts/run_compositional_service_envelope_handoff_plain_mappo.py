"""Frozen G2 plain-MAPPO control for the V5 service-envelope task.

This development-only runner deliberately contains no candidate relation-value
module.  It establishes whether a capacity-matched MLP policy can learn the
four public service-envelope profiles without a trivial ceiling before any
method comparison is permitted.
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
    load_matching_state_dict,
    make_env,
    stack_graphs,
    train_ri_gmappo,
)
from envs.timed_handoff_intercept_3d_env import SERVICE_ENVELOPE_PROFILES  # noqa: E402


PROTOCOL = "COMMITMENT-HANDOFF-3D-V5-PLAIN-MAPPO-G2-DEVELOPMENT-V1"
ENDPOINT_PROTOCOL = "COMMITMENT-HANDOFF-3D-V5-PROFILE-STRATIFIED-ENDPOINT-V1"


def training_protocol(service_envelope_mode: str) -> str:
    return (
        "COMMITMENT-HANDOFF-3D-V6-PLAIN-MAPPO-G2-DEVELOPMENT-V1"
        if service_envelope_mode == "compositional_v6_staged"
        else PROTOCOL
    )


def endpoint_protocol(service_envelope_mode: str) -> str:
    return (
        "COMMITMENT-HANDOFF-3D-V6-PROFILE-STRATIFIED-ENDPOINT-V1"
        if service_envelope_mode == "compositional_v6_staged"
        else ENDPOINT_PROTOCOL
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, required=True)
    # These values are frozen before this first G2 result is inspected.
    parser.add_argument("--updates", type=int, default=64)
    parser.add_argument("--num-envs", type=int, default=4)
    parser.add_argument("--rollout-steps", type=int, default=64)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--selection-eval-episodes", type=int, default=16)
    parser.add_argument("--endpoint-episodes-per-profile", type=int, default=60)
    parser.add_argument("--service-envelope-mode", choices=("compositional_v5", "compositional_v6_staged"), default="compositional_v5")
    parser.add_argument("--future-corridor-lateral-offset", type=float, default=1_500.0)
    parser.add_argument("--branch-step", type=int, default=40)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args()


def build_config(args: argparse.Namespace, *, profile: str = "balanced_v5") -> RIGMAPPOConfig:
    return RIGMAPPOConfig(
        env_name="commitment_handoff_3d",
        seed=args.seed,
        num_envs=args.num_envs,
        rollout_steps=args.rollout_steps,
        updates=args.updates,
        hidden_dim=args.hidden_dim,
        graph_encoder="no_graph",
        role_gate_mode="none",
        actor_action_mask_mode="relay_only",
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
        handoff_branch_step=args.branch_step,
        handoff_authorization_hold_steps=8,
        handoff_refresh_hold_steps=16,
        handoff_corridor_radius=900.0,
        handoff_future_corridor_lateral_offset=args.future_corridor_lateral_offset,
        handoff_commitment_action_repeat=8,
        handoff_legacy_intercept_reward_weight=0.0,
        handoff_prebranch_target_policy="weaving_mild",
        handoff_postbranch_target_policy="weaving_mild",
        handoff_service_envelope_mode=args.service_envelope_mode,
        handoff_service_envelope_profile=profile,
        target_init_range_scale=0.65,
        evaluation_enabled=True,
        eval_interval=max(1, min(16, args.updates)),
        eval_episodes=args.selection_eval_episodes,
        eval_base_seed=830_000,
        save_interval=max(1, min(16, args.updates)),
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


def evaluate_by_profile(args: argparse.Namespace, checkpoint: Path) -> tuple[list[dict[str, object]], dict[str, object]]:
    agent = load_agent(build_config(args), checkpoint)
    device = torch.device(args.device)
    rows: list[dict[str, object]] = []
    with torch.no_grad():
        for profile_index, profile in enumerate(SERVICE_ENVELOPE_PROFILES):
            for episode in range(args.endpoint_episodes_per_profile):
                cfg = build_config(args, profile=profile)
                env = make_env(cfg, 840_000 + profile_index * 10_000 + episode, training=False)
                obs, share_obs, graph = env.reset()
                relay_reconstruct: list[float] = []
                prebranch_reconstruct: list[float] = []
                postbranch_reconstruct: list[float] = []
                info: dict[str, object] = {}
                while True:
                    packed = stack_graphs([graph])
                    action, *_ = agent.get_action_and_value(
                        torch.as_tensor(obs[None, ...], dtype=torch.float32, device=device),
                        torch.as_tensor(packed["node_feat"], dtype=torch.float32, device=device),
                        torch.as_tensor(packed["edge_feat"], dtype=torch.float32, device=device),
                        torch.as_tensor(packed["role"], dtype=torch.long, device=device),
                        torch.as_tensor(packed["adj"], dtype=torch.float32, device=device),
                        torch.as_tensor(share_obs[None, ...], dtype=torch.float32, device=device),
                        relation_adj=torch.as_tensor(packed["relation_adj"], dtype=torch.float32, device=device),
                        deterministic=True,
                    )
                    macro = action.squeeze(0).cpu().numpy()
                    reconstruct = float(macro[1] == 1)
                    relay_reconstruct.append(reconstruct)
                    (postbranch_reconstruct if env.step_count >= env.handoff_config.branch_step else prebranch_reconstruct).append(reconstruct)
                    obs, share_obs, graph, _, dones, info = env.step(macro)
                    if bool(np.all(dones)):
                        rows.append({
                            "profile": profile,
                            "episode": episode,
                            "future_service_required": int(env._future_service_required()),
                            "success": float(info.get("success", 0.0)),
                            "timeout": float(info.get("timeout", 0.0)),
                            "collision": float(info.get("collision", 0.0)),
                            "terminal_service_progress": float(info.get("handoff_service_progress", 0.0)),
                            "relay_reconstruct_fraction": float(np.mean(relay_reconstruct)),
                            "prebranch_reconstruct_fraction": float(np.mean(prebranch_reconstruct)) if prebranch_reconstruct else 0.0,
                            "postbranch_reconstruct_fraction": float(np.mean(postbranch_reconstruct)) if postbranch_reconstruct else 0.0,
                        })
                        break
    summary: dict[str, object] = {}
    for profile in SERVICE_ENVELOPE_PROFILES:
        cell = [row for row in rows if row["profile"] == profile]
        summary[profile] = {
            "n": len(cell),
            "future_service_required": int(cell[0]["future_service_required"]),
            "success_rate": float(np.mean([row["success"] for row in cell])),
            "timeout_rate": float(np.mean([row["timeout"] for row in cell])),
            "collision_rate": float(np.mean([row["collision"] for row in cell])),
            "mean_relay_reconstruct_fraction": float(np.mean([row["relay_reconstruct_fraction"] for row in cell])),
            "mean_prebranch_reconstruct_fraction": float(np.mean([row["prebranch_reconstruct_fraction"] for row in cell])),
            "mean_postbranch_reconstruct_fraction": float(np.mean([row["postbranch_reconstruct_fraction"] for row in cell])),
        }
    report = {
        "protocol": endpoint_protocol(args.service_envelope_mode),
        "env_name": "commitment_handoff_3d",
        "service_envelope_mode": args.service_envelope_mode,
        "checkpoint": str(checkpoint),
        "seed": args.seed,
        "summary": summary,
    }
    return rows, report


def main() -> None:
    args = parse_args()
    if not args.execute:
        raise SystemExit("pass --execute because this command creates a development run")
    if min(args.updates, args.num_envs, args.rollout_steps, args.endpoint_episodes_per_profile) <= 0:
        raise ValueError("training and endpoint counts must be positive")
    if args.out_dir.exists():
        raise FileExistsError(f"refusing to overwrite {args.out_dir}")
    args.out_dir.mkdir(parents=True)
    macro_steps = args.updates * args.num_envs * args.rollout_steps
    manifest = {
        "protocol": training_protocol(args.service_envelope_mode),
        "artifact_class": "DEVELOPMENT_ONLY_G2_LEARNABILITY_PILOT",
        "paper_evidence": False,
        "purpose": "test whether plain MLP MAPPO learns mixed public service envelopes without task saturation",
        "seed": args.seed,
        "macro_decision_steps": macro_steps,
        "physical_environment_steps": macro_steps * 8,
        "profile_schedule": "balanced_v5 deterministic modulo assignment across worker slots",
        "profiles": list(SERVICE_ENVELOPE_PROFILES),
        "fixed_task": {
            "commitment_action_repeat": 8, "service_envelope_mode": args.service_envelope_mode,
            "branch_step": args.branch_step, "future_corridor_lateral_offset": args.future_corridor_lateral_offset,
        },
        "method": "plain capacity-controlled MLP MAPPO; no graph, relation-value head, sampler, or auxiliary loss",
        "actor_action_contract": {"mode": "relay_only", "actor_active_agents": ["relay"], "critic_observes_all_agents": True},
        "status": "running",
    }
    (args.out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    train_ri_gmappo(build_config(args))
    checkpoint = args.out_dir / "actor_critic_latest.pt"
    if not checkpoint.is_file():
        raise FileNotFoundError(f"missing final checkpoint: {checkpoint}")
    rows, endpoint = evaluate_by_profile(args, checkpoint)
    with (args.out_dir / "profile_stratified_endpoint.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (args.out_dir / "profile_stratified_endpoint.json").write_text(json.dumps(endpoint, indent=2) + "\n", encoding="utf-8")
    manifest.update({"status": "completed", "checkpoint": checkpoint.name, "endpoint": endpoint})
    (args.out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
