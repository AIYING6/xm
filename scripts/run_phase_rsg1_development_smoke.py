"""Run the frozen RSG-1 development smoke and paired final-checkpoint evaluation."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import (  # noqa: E402
    RIGMAPPOAgent,
    RIGMAPPOConfig,
    RSG_TC_EDGE_FEATURE_INDICES,
    load_matching_state_dict,
    make_env,
    stack_graphs,
    train_ri_gmappo,
)
from envs.uav_intercept_3d_env import ACTION3D_TABLE, UAVIntercept3DConfig, UAVIntercept3DEnv  # noqa: E402


PROTOCOL = "PHASE-RSG-1-V1"
SEEDS = (1501, 1502, 1503)
TAPE_START = 340000
EPISODES = 100
UPDATES = 782
NUM_ENVS = 4
ROLLOUT_STEPS = 64
METHODS = {
    "mappo": {"graph_encoder": "no_graph", "hidden_dim": 64},
    "matched_single_graph": {"graph_encoder": "single", "hidden_dim": 115},
    "rsg_tc": {"graph_encoder": "rsg_tc", "hidden_dim": 114},
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def frozen_env(seed: int, failure_on: bool) -> UAVIntercept3DEnv:
    return UAVIntercept3DEnv(UAVIntercept3DConfig(
        seed=seed, target_policy="straight", strict_target_sensing=True,
        agent_target_info_bottleneck=True, relay_dependent_task=True,
        business_grounded_geometry=True, communication_range_scale=1.0,
        communication_dropout_prob=0.0, message_delay_steps=0,
        radar_dropout_prob=0.0, max_steps=260, min_success_step=260,
        failed_blue_agent=1 if failure_on else -1,
        node_failure_start_step=44 if failure_on else 0,
        node_failure_duration_steps=80 if failure_on else 0,
    ))


def training_config(method: dict[str, int | str], seed: int, out_dir: Path) -> RIGMAPPOConfig:
    return RIGMAPPOConfig(
        env_name="3d_intercept", seed=seed, num_envs=NUM_ENVS,
        rollout_steps=ROLLOUT_STEPS, updates=UPDATES,
        hidden_dim=int(method["hidden_dim"]), role_dim=8, intent_dim=8,
        graph_encoder=str(method["graph_encoder"]), role_gate_mode="none",
        target_policy="straight", strict_target_sensing=True,
        agent_target_info_bottleneck=True, relay_dependent_task=True,
        business_grounded_geometry=True, communication_range_scale=1.0,
        communication_dropout_prob=0.0, message_delay_steps=0,
        radar_dropout_prob=0.0, min_success_step=1000,
        failed_blue_agent=1, node_failure_start_step=44,
        node_failure_duration_steps=80, evaluation_enabled=False,
        target_kl=None, save_interval=UPDATES, save_snapshots=False,
        out_dir=str(out_dir), device="cuda" if torch.cuda.is_available() else "cpu",
    )


def build_agent(method: dict[str, int | str], checkpoint: Path, seed: int) -> RIGMAPPOAgent:
    env = frozen_env(seed, False)
    _, share, graph = env.reset()
    agent = RIGMAPPOAgent(
        obs_dim=env.obs_dim, node_feat_dim=graph["node_feat"].shape[-1],
        edge_feat_dim=graph["edge_feat"].shape[-1], share_obs_dim=share.shape[-1],
        action_dim=env.action_dim, num_agents=env.num_agents,
        num_roles=max(4, int(np.max(graph["role"])) + 1),
        hidden_dim=int(method["hidden_dim"]), role_dim=8, intent_dim=8,
        graph_encoder=str(method["graph_encoder"]), role_gate_mode="none",
        use_intent_context=False,
    )
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    agent.to(device)
    load_matching_state_dict(agent, str(checkpoint), device)
    agent.eval()
    return agent


def policy_action(agent: RIGMAPPOAgent, obs: np.ndarray, share: np.ndarray, graph: dict) -> np.ndarray:
    device = next(agent.parameters()).device
    packed = stack_graphs([graph])
    with torch.no_grad():
        actions, *_ = agent.get_action_and_value(
            torch.as_tensor(obs[None], dtype=torch.float32, device=device),
            torch.as_tensor(packed["node_feat"], dtype=torch.float32, device=device),
            torch.as_tensor(packed["edge_feat"], dtype=torch.float32, device=device),
            torch.as_tensor(packed["role"], dtype=torch.long, device=device),
            torch.as_tensor(packed["adj"], dtype=torch.float32, device=device),
            torch.as_tensor(share[None], dtype=torch.float32, device=device),
            relation_adj=torch.as_tensor(packed["relation_adj"], dtype=torch.float32, device=device),
            deterministic=True,
            intent_label=torch.as_tensor(packed["intent_label"], dtype=torch.long, device=device),
        )
    return actions.squeeze(0).cpu().numpy()


def bias_observations(agent: RIGMAPPOAgent, graph: dict, phase: str, condition: str) -> list[dict]:
    if agent.actor.graph_encoder != "rsg_tc":
        return []
    device = next(agent.parameters()).device
    packed = stack_graphs([graph])
    relation = torch.as_tensor(packed["relation_adj"], dtype=torch.float32, device=device)
    edge = torch.as_tensor(packed["edge_feat"], dtype=torch.float32, device=device)
    rows = []
    with torch.no_grad():
        for layer_id, layer in enumerate((agent.actor.rsg_tc_gat1, agent.actor.rsg_tc_gat2), start=1):
            context = torch.cat((relation.permute(0, 2, 3, 1), edge[..., list(RSG_TC_EDGE_FEATURE_INDICES)]), dim=-1)
            bias = layer.relation_bias(context).squeeze(-1)[0].cpu().numpy()
            rel_np = relation[0].cpu().numpy()
            adj_np = packed["adj"][0]
            n = adj_np.shape[0]
            for i in range(n):
                for j in range(n):
                    if i == j or adj_np[i, j] <= 0.0:
                        continue
                    combo = "".join(name for bit, name in zip(rel_np[:, i, j], ("P", "C", "T")) if bit > 0.5) or "none"
                    rows.append({"layer": layer_id, "phase": phase, "condition": condition,
                                 "relation_combo": combo, "bias": float(bias[i, j])})
    return rows


def evaluate_episode(agent: RIGMAPPOAgent, method: str, train_seed: int, episode_id: int, condition: str) -> tuple[dict, list[dict]]:
    failure = condition == "relay_failure"
    env = frozen_env(episode_id, failure)
    obs, share, graph = env.reset()
    reward_sum = distance = control_effort = 0.0
    paths, traces, bias_rows = [], [], []
    previous = env.blue_pos.copy()
    while True:
        step = int(env.step_count)
        phase = "pre_failure" if step < 44 else "post_failure"
        bias_rows.extend(bias_observations(agent, graph, phase, condition))
        actions = policy_action(agent, obs, share, graph)
        control_effort += float(np.abs(ACTION3D_TABLE[actions, :2]).sum())
        obs, share, graph, rewards, dones, info = env.step(actions)
        reward_sum += float(np.sum(rewards))
        distance += float(np.linalg.norm(env.blue_pos - previous, axis=1).sum())
        previous = env.blue_pos.copy()
        path = str(info.get("attacker_cache_paths_t", ""))
        paths.append(path)
        traces.append({"relay_failure_active": int(info.get("node_failure_active", 0.0) > .5),
                       "path": path, "task_support": int(info.get("chain_support_t", 0.0) > .5),
                       "legal_info": int(info.get("attacker_legal_target_information_t", 0.0) > .5),
                       "cache_age": float(info.get("target_cache_age_mean", 0.0))})
        if np.all(dones):
            break
    active = [row for row in traces if row["relay_failure_active"]]
    denom = max(1, len(active))
    return ({"protocol": PROTOCOL, "development_episode_id": episode_id,
             "method": method, "train_seed": train_seed, "condition": condition,
             "J": reward_sum, "success_at_horizon": float(info["success"]),
             "collision": float(info["collision"]), "timeout": float(info["timeout"]),
             "constraint_violation": float(info["constraint_violation"]),
             "terminal_step": int(info["step"]), "failure_exposed": int(bool(active)),
             "direct_path_fraction_during_failure": float(sum(row["path"] == "0-2" for row in active) / denom),
             "relay_path_fraction_during_failure": float(sum(row["path"] == "0-1-2" for row in active) / denom),
             "task_support_fraction_during_failure": float(sum(row["task_support"] for row in active) / denom),
             "legal_information_fraction_during_failure": float(sum(row["legal_info"] for row in active) / denom),
             "mean_cache_age_during_failure": float(np.mean([row["cache_age"] for row in active])) if active else math.nan,
             "path_switch_count": sum(a != b for a, b in zip(paths, paths[1:])),
             "traveled_distance": distance, "control_effort": control_effort}, bias_rows)


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def run(args: argparse.Namespace) -> dict:
    out = args.output_root
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"refusing to overwrite RSG-1 output: {out}")
    out.mkdir(parents=True, exist_ok=True)
    all_rows, all_bias, manifests = [], [], []
    for method_name, method in METHODS.items():
        for seed in SEEDS:
            run_dir = out / "runs" / method_name / f"seed{seed}"
            run_dir.mkdir(parents=True, exist_ok=False)
            cfg = training_config(method, seed, run_dir)
            manifest = {"protocol": PROTOCOL, "status": "running", "method": method_name,
                        "seed": seed, "updates": UPDATES, "num_envs": NUM_ENVS,
                        "rollout_steps": ROLLOUT_STEPS, "environment_steps": UPDATES * NUM_ENVS * ROLLOUT_STEPS,
                        "checkpoint_selection": "fixed_final_update_only", "resume": False,
                        "early_stopping": False, "canonical_data_used": False,
                        "graph_encoder": method["graph_encoder"], "config": cfg.__dict__}
            (run_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
            train_ri_gmappo(cfg)
            checkpoint = run_dir / "actor_critic_latest.pt"
            if not checkpoint.exists():
                raise FileNotFoundError(checkpoint)
            agent = build_agent(method, checkpoint, seed)
            raw = []
            for episode in range(EPISODES):
                eid = TAPE_START + episode
                for condition in ("nominal", "relay_failure"):
                    row, bias = evaluate_episode(agent, method_name, seed, eid, condition)
                    raw.append(row); all_bias.extend([{**item, "method": method_name, "train_seed": seed, "development_episode_id": eid} for item in bias])
            write_csv(run_dir / "raw_episode_metrics.csv", raw)
            nominal = {row["development_episode_id"]: row for row in raw if row["condition"] == "nominal"}
            paired = [{"protocol": PROTOCOL, "development_episode_id": row["development_episode_id"],
                       "method": method_name, "train_seed": seed, "J_nominal": nominal[row["development_episode_id"]]["J"],
                       "J_failure": row["J"], "delta_J": nominal[row["development_episode_id"]]["J"] - row["J"],
                       "success_nominal": nominal[row["development_episode_id"]]["success_at_horizon"],
                       "success_failure": row["success_at_horizon"], "failure_exposed": row["failure_exposed"]}
                      for row in raw if row["condition"] == "relay_failure"]
            write_csv(run_dir / "paired_metrics.csv", paired)
            manifest.update({"status": "completed", "checkpoint": str(checkpoint), "checkpoint_sha256": sha256(checkpoint),
                             "evaluation_tape_start": TAPE_START, "evaluation_episodes_per_condition": EPISODES,
                             "evaluation_success_metric": "success_at_horizon_min_success_step_260"})
            (run_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
            all_rows.extend(raw); manifests.append(manifest)
    write_csv(out / "raw_episode_metrics.csv", all_rows)
    write_csv(out / "bias_telemetry.csv", all_bias)
    summary = []
    for method_name in METHODS:
        for seed in SEEDS:
            cell = [row for row in all_rows if row["method"] == method_name and row["train_seed"] == seed]
            nominal = {row["development_episode_id"]: row for row in cell if row["condition"] == "nominal"}
            failures = [row for row in cell if row["condition"] == "relay_failure"]
            deltas = [nominal[row["development_episode_id"]]["J"] - row["J"] for row in failures]
            summary.append({"method": method_name, "train_seed": seed, "episodes": len(failures),
                            "J_nominal_mean": float(np.mean([nominal[row["development_episode_id"]]["J"] for row in failures])),
                            "J_failure_mean": float(np.mean([row["J"] for row in failures])),
                            "delta_J_mean": float(np.mean(deltas)),
                            "success_nominal_mean": float(np.mean([nominal[row["development_episode_id"]]["success_at_horizon"] for row in failures])),
                            "success_failure_mean": float(np.mean([row["success_at_horizon"] for row in failures])),
                            "collision_nominal_mean": float(np.mean([nominal[row["development_episode_id"]]["collision"] for row in failures])),
                            "collision_failure_mean": float(np.mean([row["collision"] for row in failures])),
                            "timeout_nominal_mean": float(np.mean([nominal[row["development_episode_id"]]["timeout"] for row in failures])),
                            "timeout_failure_mean": float(np.mean([row["timeout"] for row in failures])),
                            "constraint_nominal_mean": float(np.mean([nominal[row["development_episode_id"]]["constraint_violation"] for row in failures])),
                            "constraint_failure_mean": float(np.mean([row["constraint_violation"] for row in failures]))})
    write_csv(out / "per_seed_summary.csv", summary)
    manifest = {"protocol": PROTOCOL, "status": "completed", "training_started": True,
                "formal_training": True, "methods": list(METHODS), "seeds": list(SEEDS),
                "environment_steps_per_run": UPDATES * NUM_ENVS * ROLLOUT_STEPS,
                "tape_start": TAPE_START, "episodes_per_condition": EPISODES,
                "checkpoint_selection": "fixed_final_update_only", "manifests": manifests,
                "bias_telemetry_rows": len(all_bias)}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"status": "completed", "output_root": str(out), "bias_rows": len(all_bias)}, indent=2))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=ROOT / "results/development/phase_rsg1_development_smoke")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: RSG-1 requires explicit --execute")
    run(args)


if __name__ == "__main__":
    main()
