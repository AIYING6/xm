"""Frozen S3 development-only three-method robustness smoke.

The runner is intentionally separate from legacy recovery evaluators.  It
trains each arm on the frozen Relay-failure task, retains only the final
checkpoint, and evaluates that checkpoint on shared nominal/failure episode
IDs.  It cannot run canonical seeds or resume a run.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
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
    stack_graphs,
    train_ri_gmappo,
)
from envs.uav_intercept_3d_env import ACTION3D_TABLE, UAVIntercept3DConfig, UAVIntercept3DEnv  # noqa: E402


PROTOCOL = "PHASE-S3-TMDS-V1"
SEEDS = (1501, 1502, 1503)
METHODS = {
    "mappo": {"label": "MAPPO", "encoder": "no_graph", "hidden": 64, "gate": "none"},
    "matched_single_graph": {"label": "Parameter-Matched Single-Graph", "encoder": "single", "hidden": 115, "gate": "none"},
    "full": {"label": "Multi-Relation Full", "encoder": "multi_relation", "hidden": 64, "gate": "relation_conditioned"},
}
NUM_ENVS = 4
ROLLOUT_STEPS = 64
UPDATES = 782
ENV_STEPS = NUM_ENVS * ROLLOUT_STEPS * UPDATES
EVAL_EPISODES = 100
OUT = ROOT / "results" / "development" / "phase_s3_three_method_smoke"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def episode_id(method_index: int, seed_index: int, episode: int) -> int:
    return 310000 + 10000 * method_index + 1000 * seed_index + episode


def frozen_env(seed: int, failure_on: bool) -> UAVIntercept3DEnv:
    return UAVIntercept3DEnv(
        UAVIntercept3DConfig(
            seed=seed,
            target_policy="straight",
            strict_target_sensing=True,
            agent_target_info_bottleneck=True,
            relay_dependent_task=True,
            business_grounded_geometry=True,
            communication_range_scale=1.0,
            communication_dropout_prob=0.0,
            message_delay_steps=0,
            radar_dropout_prob=0.0,
            max_steps=260,
            min_success_step=1000,
            failed_blue_agent=1 if failure_on else -1,
            node_failure_start_step=44 if failure_on else 0,
            node_failure_duration_steps=80 if failure_on else 0,
        )
    )


def training_config(method: dict[str, object], seed: int, out_dir: Path, updates: int) -> RIGMAPPOConfig:
    return RIGMAPPOConfig(
        env_name="3d_intercept", seed=seed, num_envs=NUM_ENVS, rollout_steps=ROLLOUT_STEPS,
        updates=updates, hidden_dim=int(method["hidden"]), role_dim=8, intent_dim=8,
        graph_encoder=str(method["encoder"]), role_gate_mode=str(method["gate"]),
        target_policy="straight", strict_target_sensing=True, agent_target_info_bottleneck=True,
        relay_dependent_task=True, business_grounded_geometry=True,
        communication_range_scale=1.0, communication_dropout_prob=0.0,
        message_delay_steps=0, radar_dropout_prob=0.0, min_success_step=1000,
        failed_blue_agent=1, node_failure_start_step=44, node_failure_duration_steps=80,
        evaluation_enabled=False, target_kl=None, save_interval=updates,
        save_snapshots=False, out_dir=str(out_dir), device="cuda" if torch.cuda.is_available() else "cpu",
    )


def agent_for_checkpoint(method: dict[str, object], checkpoint: Path, seed: int) -> RIGMAPPOAgent:
    env = frozen_env(seed, False)
    obs, share, graph = env.reset()
    agent = RIGMAPPOAgent(
        obs_dim=env.obs_dim, node_feat_dim=graph["node_feat"].shape[-1], edge_feat_dim=graph["edge_feat"].shape[-1],
        share_obs_dim=share.shape[-1], action_dim=env.action_dim, num_agents=env.num_agents,
        num_roles=max(4, int(np.max(graph["role"])) + 1), hidden_dim=int(method["hidden"]), role_dim=8,
        intent_dim=8, graph_encoder=str(method["encoder"]), role_gate_mode=str(method["gate"]),
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


def evaluate_episode(agent: RIGMAPPOAgent, method: str, seed: int, eid: int, condition: str) -> tuple[dict, list[dict]]:
    failure = condition == "relay_failure"
    env = frozen_env(eid, failure)
    obs, share, graph = env.reset()
    reward_sum = 0.0
    distance = 0.0
    control_effort = 0.0
    paths: list[str] = []
    trace: list[dict] = []
    previous = env.blue_pos.copy()
    while True:
        actions = policy_action(agent, obs, share, graph)
        control_effort += float(np.abs(ACTION3D_TABLE[actions, :2]).sum())
        obs, share, graph, rewards, dones, info = env.step(actions)
        distance += float(np.linalg.norm(env.blue_pos - previous, axis=1).sum())
        previous = env.blue_pos.copy()
        path = str(info.get("attacker_cache_paths_t", ""))
        paths.append(path)
        trace.append({
            "development_episode_id": eid, "method": method, "train_seed": seed, "condition": condition,
            "timestep": int(info["step"]), "relay_failure_active": int(info["node_failure_active"] > .5),
            "comm_edge_count": int(np.sum(env.comm_adj) - env.num_agents),
            "scout_relay_comm": int(env.comm_adj[1, 0] > .5), "relay_attacker_comm": int(env.comm_adj[2, 1] > .5),
            "scout_attacker_comm": int(env.comm_adj[2, 0] > .5), "path": path,
            "task_chain_support": int(info["chain_support_t"] > .5),
            "legal_information": int(info["attacker_legal_target_information_t"] > .5),
            "cache_age": float(info["target_cache_age_mean"]), "reward_sum": float(np.sum(rewards)),
            "terminal": int(np.all(dones)),
        })
        reward_sum += float(np.sum(rewards))
        if np.all(dones):
            break
    switches = sum(a != b for a, b in zip(paths, paths[1:]))
    active = [x for x in trace if x["relay_failure_active"]]
    summary = {
        "development_episode_id": eid, "method": method, "train_seed": seed, "condition": condition,
        "J": reward_sum, "success": float(info["success"]), "collision": float(info["collision"]),
        "timeout": float(info["timeout"]), "constraint_violation": float(info["constraint_violation"]),
        "terminal_step": int(info["step"]), "failure_exposed": int(bool(active)),
        "mean_comm_edge_count": float(np.mean([x["comm_edge_count"] for x in trace])),
        "direct_path_fraction": float(np.mean([x["path"] == "0-2" for x in trace])),
        "relay_path_fraction": float(np.mean([x["path"] == "0-1-2" for x in trace])),
        "path_switch_count": switches, "task_chain_availability": float(np.mean([x["task_chain_support"] for x in trace])),
        "legal_information_availability": float(np.mean([x["legal_information"] for x in trace])),
        "mean_cache_age": float(np.mean([x["cache_age"] for x in trace])),
        "traveled_distance": distance, "control_effort": control_effort,
    }
    return summary, trace


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def evaluate_run(method_key: str, method: dict[str, object], seed: int, method_index: int, seed_index: int, checkpoint: Path, out_dir: Path, episodes: int) -> None:
    agent = agent_for_checkpoint(method, checkpoint, seed)
    rows: list[dict] = []
    trace_rows: list[dict] = []
    for episode in range(episodes):
        eid = episode_id(method_index, seed_index, episode)
        nominal, nt = evaluate_episode(agent, method_key, seed, eid, "nominal")
        failure, ft = evaluate_episode(agent, method_key, seed, eid, "relay_failure")
        rows.extend([nominal, failure]); trace_rows.extend(nt); trace_rows.extend(ft)
    write_csv(out_dir / "raw_episode_metrics.csv", rows)
    write_csv(out_dir / "raw_timestep_metrics.csv", trace_rows)
    nominal = {int(r["development_episode_id"]): r for r in rows if r["condition"] == "nominal"}
    paired = []
    for f in (r for r in rows if r["condition"] == "relay_failure"):
        n = nominal[int(f["development_episode_id"])]
        paired.append({"development_episode_id": f["development_episode_id"], "method": method_key, "train_seed": seed,
                       "J_nominal": n["J"], "J_failure": f["J"], "delta_J": n["J"] - f["J"],
                       "success_nominal": n["success"], "success_failure": f["success"],
                       "failure_exposed": f["failure_exposed"]})
    write_csv(out_dir / "paired_metrics.csv", paired)


def run_arm(method_key: str, seed: int, method_index: int, seed_index: int, updates: int, episodes: int, output_root: Path) -> None:
    method = METHODS[method_key]
    out_dir = output_root / "runs" / method_key / f"seed{seed}"
    if out_dir.exists():
        raise FileExistsError(f"Refusing to overwrite existing S3 run: {out_dir}")
    out_dir.mkdir(parents=True)
    cfg = training_config(method, seed, out_dir, updates)
    manifest = {"protocol": PROTOCOL, "status": "running", "artifact_class": "DEVELOPMENT_ONLY", "method": method_key,
                "seed": seed, "updates": updates, "num_envs": NUM_ENVS, "rollout_steps": ROLLOUT_STEPS,
                "environment_steps": updates * NUM_ENVS * ROLLOUT_STEPS, "checkpoint_selection": "fixed_final_update_only",
                "resume": False, "early_stopping": False, "canonical_data_used": False, "training_started": True,
                "commit": git_head(), "config": cfg.__dict__}
    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    train_ri_gmappo(cfg)
    checkpoint = out_dir / "actor_critic_latest.pt"
    if not checkpoint.exists():
        raise FileNotFoundError("fixed final checkpoint missing")
    evaluate_run(method_key, method, seed, method_index, seed_index, checkpoint, out_dir, episodes)
    manifest.update({"status": "completed", "checkpoint": str(checkpoint.relative_to(ROOT)), "checkpoint_sha256": sha256(checkpoint),
                     "evaluation_episodes_per_condition": episodes})
    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--execute", action="store_true")
    p.add_argument("--integration-smoke", action="store_true")
    p.add_argument("--prelaunch", action="store_true")
    p.add_argument("--method", choices=tuple(METHODS), default=None)
    p.add_argument("--seed", type=int, choices=SEEDS, default=None)
    p.add_argument("--output-root", type=Path, default=OUT)
    a = p.parse_args()
    if not a.execute and not a.integration_smoke and not a.prelaunch:
        raise SystemExit("NO-GO: require --execute, --integration-smoke, or --prelaunch")
    if a.prelaunch:
        config_path = ROOT / "configs" / "paper" / "s2_environment_frozen.yaml"
        config_text = config_path.read_text(encoding="utf-8")
        source = Path(__file__).read_text(encoding="utf-8")
        no_resume = all(
            training_config(spec, SEEDS[0], Path("unused"), UPDATES).resume is None
            and training_config(spec, SEEDS[0], Path("unused"), UPDATES).init_checkpoint is None
            and not training_config(spec, SEEDS[0], Path("unused"), UPDATES).evaluation_enabled
            for spec in METHODS.values()
        )
        checks = {
            "three_methods": set(METHODS) == {"mappo", "matched_single_graph", "full"},
            "development_seeds": SEEDS == (1501, 1502, 1503),
            "nine_runs": len(METHODS) * len(SEEDS) == 9,
            "fixed_budget": ENV_STEPS == 200192,
            "final_checkpoint_only": "fixed_final_update_only" in source,
            "no_resume_or_checkpoint_selection": no_resume,
            "frozen_geometry": "business_grounded_geometry: true" in config_text,
            "relay_task_semantics": "relay_dependent_task: true" in config_text,
            "paired_final_evaluation": EVAL_EPISODES == 100,
            "canonical_seeds_excluded": all(seed not in range(5) for seed in SEEDS),
        }
        result = {"protocol": PROTOCOL, "checks": checks, "pass": all(checks.values()), "training_started": False}
        target = a.output_root / "PRELAUNCH_AUDIT.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2))
        if not result["pass"]:
            raise SystemExit(1)
        return
    if a.integration_smoke:
        keys = (a.method or "mappo",); seeds = (a.seed or SEEDS[0],); updates, episodes = 1, 2
        output_root = a.output_root / "integration_smoke"
    else:
        keys = (a.method,) if a.method else tuple(METHODS); seeds = (a.seed,) if a.seed else SEEDS
        updates, episodes, output_root = UPDATES, EVAL_EPISODES, a.output_root
    for method_key in keys:
        for seed in seeds:
            run_arm(method_key, seed, list(METHODS).index(method_key), SEEDS.index(seed), updates, episodes, output_root)


if __name__ == "__main__":
    main()
