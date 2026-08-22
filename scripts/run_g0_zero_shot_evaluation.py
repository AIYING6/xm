"""G0 frozen-policy, zero-shot evaluation on a pre-frozen topology suite.

This is an evaluation adapter only.  It never invokes optimizer construction,
backpropagation, or a policy update.  Topology descriptors configure the
existing environment before reset and are never supplied to the actor.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOAgent, stack_graphs
from envs.uav_intercept_3d_env import ACTION3D_TABLE, UAVIntercept3DConfig, UAVIntercept3DEnv
from scripts.telemetry_native_t1 import MATCHED_SG_PARAMETER_COUNT, deterministic_checkpoint_policy


PROTOCOL = "G0-ZERO-SHOT-TOPOLOGY-EVALUATION-V1"
UTR_ROOT = ROOT / "results/development/t1_telemetry_native_reference_1m_run1/runs/utr_sg"
STRICT_ROOT = ROOT / "artifacts/drtp_div_a0/source_runtime/results/development/drtp_sg_strict_continuous_10m/runs/drtp_sg"
HELDOUT_ROOT = ROOT / "artifacts/drtp_div_a0/source_runtime/results/heldout/drtp_sg_heldout_v2/runs/drtp_sg"


@dataclass(frozen=True)
class Scenario:
    name: str
    family: str
    failed_blue_agent: int = -1
    start_step: int = 0
    duration_steps: int = 0
    comm_topology_mode: str = "none"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def make_env(episode_id: int, scenario: Scenario) -> UAVIntercept3DEnv:
    return UAVIntercept3DEnv(UAVIntercept3DConfig(
        seed=int(episode_id), target_policy="straight", strict_target_sensing=True,
        agent_target_info_bottleneck=True, relay_dependent_task=True,
        business_grounded_geometry=True, communication_range_scale=1.0,
        communication_dropout_prob=0.0, message_delay_steps=0,
        radar_dropout_prob=0.0, max_steps=260, min_success_step=260,
        failed_blue_agent=scenario.failed_blue_agent,
        node_failure_start_step=scenario.start_step,
        node_failure_duration_steps=scenario.duration_steps,
        comm_topology_mode=scenario.comm_topology_mode,
    ))


def scenario_from_manifest(item: dict[str, Any]) -> Scenario:
    failure = item.get("failure") or {}
    return Scenario(
        name=str(item["id"]), family=str(item["family"]),
        failed_blue_agent=int(failure.get("agent", -1)),
        start_step=int(failure.get("onset", 0)),
        duration_steps=int(failure.get("duration", 0)),
        comm_topology_mode=str(item["comm_topology_mode"]),
    )


def build_from_state(state_path: Path, construction_seed: int) -> RIGMAPPOAgent:
    """Load a frozen DRTP runtime-state model without resuming its trajectory."""
    # Runtime states were written by a newer NumPy package.  This alias only
    # permits deserialization of the locally archived trusted state; no state
    # other than model_state is used by this evaluation adapter.
    sys.modules.setdefault("numpy._core", np.core)
    sys.modules.setdefault("numpy._core.multiarray", np.core.multiarray)
    torch.manual_seed(int(construction_seed))
    probe = make_env(0, Scenario("probe", "probe"))
    _, share_obs, graph = probe.reset()
    agent = RIGMAPPOAgent(
        obs_dim=probe.obs_dim, node_feat_dim=int(graph["node_feat"].shape[-1]),
        edge_feat_dim=int(graph["edge_feat"].shape[-1]), share_obs_dim=int(share_obs.shape[-1]),
        action_dim=probe.action_dim, num_agents=probe.num_agents,
        num_roles=max(4, int(np.max(graph["role"])) + 1), hidden_dim=115,
        role_dim=8, intent_dim=8, graph_encoder="single", role_gate_mode="none",
        use_intent_context=False,
    )
    if sum(parameter.numel() for parameter in agent.parameters()) != MATCHED_SG_PARAMETER_COUNT:
        raise RuntimeError("matched-SG parameter mismatch while building DRTP actor")
    state = torch.load(state_path, map_location="cpu")
    agent.load_state_dict(state["model_state"], strict=True)
    agent.eval()
    return agent


def run_episode(episode_id: int, scenario: Scenario, policy: Callable[[np.ndarray, np.ndarray, dict[str, Any]], np.ndarray]) -> dict[str, Any]:
    env = make_env(episode_id, scenario)
    obs, share_obs, graph = env.reset()
    rewards_total = 0.0
    distance = 0.0
    control = 0.0
    previous = env.blue_pos.copy()
    failure_active = False
    direct_count = relay_count = support_count = legal_count = 0
    active_count = 0
    paths: list[str] = []
    terminal_info: dict[str, Any] = {}
    while True:
        actions = np.asarray(policy(obs.copy(), share_obs.copy(), graph), dtype=np.int64)
        if actions.shape != (env.num_agents,) or np.any(actions < 0) or np.any(actions >= env.action_dim):
            raise RuntimeError("frozen policy emitted invalid action")
        obs, share_obs, graph, rewards, dones, info = env.step(actions)
        rewards_total += float(np.sum(rewards))
        distance += float(np.linalg.norm(env.blue_pos - previous, axis=1).sum())
        previous = env.blue_pos.copy()
        control += float(np.abs(ACTION3D_TABLE[actions, :2]).sum())
        active = bool(info.get("node_failure_active", 0.0))
        failure_active = failure_active or active
        path = str(info.get("attacker_cache_paths_t") or "")
        paths.append(path)
        if active:
            active_count += 1
            direct_count += int(path == "0-2")
            relay_count += int(path == "0-1-2")
            support_count += int(info.get("chain_support_t") or 0)
            legal_count += int(info.get("attacker_legal_target_information_t") or 0)
        terminal_info = info
        if np.all(dones):
            break
    denom = max(1, active_count)
    terminal_step = int(terminal_info.get("step", 0))
    onset = int(scenario.start_step)
    risk_set = int(onset > 0 and terminal_step >= onset)
    return {
        "protocol": PROTOCOL, "episode_id": int(episode_id), "condition": scenario.name,
        "family": scenario.family, "J": rewards_total, "terminal_step": terminal_step,
        "success": int(terminal_info.get("success") or 0), "collision": int(terminal_info.get("collision") or 0),
        "timeout": int(terminal_info.get("timeout") or 0), "constraint_violation": int(terminal_info.get("constraint_violation") or 0),
        "failure_exposed": int(failure_active), "alive_at_onset": risk_set,
        "failure_trigger_success": int(failure_active) if risk_set else "",
        "pre_trigger_collision": int(bool(terminal_info.get("collision") or 0) and onset > 0 and terminal_step < onset),
        "episode_length": terminal_step, "traveled_distance": distance, "control_effort": control,
        "direct_path_fraction_during_failure": direct_count / denom,
        "relay_path_fraction_during_failure": relay_count / denom,
        "task_support_fraction_during_failure": support_count / denom,
        "legal_information_fraction_during_failure": legal_count / denom,
        "path_switch_count": sum(left != right for left, right in zip(paths, paths[1:])),
    }


def policy_inventory() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for seed in (2201, 2202, 2203, 2204, 2205):
        path = UTR_ROOT / f"seed{seed}" / "actor_critic_latest.pt"
        records.append({"method": "UTR-SG-MAPPO", "contract": "T1_clean_development_1M", "seed": seed, "path": path, "kind": "checkpoint"})
    for seed in (1901, 1902):
        path = STRICT_ROOT / f"seed{seed}" / "actor_critic_runtime_state_milestone_10m.pt"
        records.append({"method": "DRTP-SG-MAPPO", "contract": "strict_development_10M", "seed": seed, "path": path, "kind": "runtime_state"})
    for seed in (2001, 2002, 2003):
        path = HELDOUT_ROOT / f"seed{seed}" / "actor_critic_runtime_state_milestone_10m.pt"
        records.append({"method": "DRTP-SG-MAPPO", "contract": "heldout_v2_10M_historical_FAIL", "seed": seed, "path": path, "kind": "runtime_state"})
    for item in records:
        if not item["path"].exists():
            raise FileNotFoundError(item["path"])
        item["sha256"] = sha256(item["path"])
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts/g0")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("G0 requires explicit --execute for frozen-policy evaluation")
    manifest_path = ROOT / "artifacts/g0/topology_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "FROZEN_BEFORE_EVALUATION" or not manifest.get("development_only"):
        raise RuntimeError("invalid G0 topology manifest")
    scenarios = [scenario_from_manifest(item) for item in manifest["evaluation_conditions"]]
    episode_ids = list(range(950000, 950000 + int(manifest["episodes_per_condition"])))
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    raw_path = output / "g0_episode_results.csv"
    if raw_path.exists():
        raise FileExistsError(f"refusing to overwrite existing G0 evidence: {raw_path}")
    inventory = policy_inventory()
    inventory_path = output / "g0_checkpoint_inventory.json"
    inventory_path.write_text(json.dumps({"protocol": PROTOCOL, "policies": [{**item, "path": str(item["path"])} for item in inventory]}, indent=2) + "\n", encoding="utf-8")
    rows: list[dict[str, Any]] = []
    total = len(inventory) * len(scenarios) * len(episode_ids)
    completed = 0
    for item in inventory:
        if item["kind"] == "checkpoint":
            from scripts.telemetry_native_t1 import build_matched_sg_agent
            agent = build_matched_sg_agent(item["path"], int(item["seed"]), device="cpu")
        else:
            agent = build_from_state(item["path"], int(item["seed"]))
        policy = deterministic_checkpoint_policy(agent)
        for scenario in scenarios:
            for episode_id in episode_ids:
                row = run_episode(episode_id, scenario, policy)
                row.update({"method": item["method"], "training_contract": item["contract"], "training_seed": item["seed"], "checkpoint_sha256": item["sha256"]})
                rows.append(row)
                completed += 1
            print(f"G0 progress {completed}/{total} ({100.0 * completed / total:.2f}%) {item['method']} seed{item['seed']} {scenario.name}", flush=True)
        del agent
    keys = list(rows[0])
    with raw_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)
    (output / "g0_evaluation_manifest.json").write_text(json.dumps({
        "protocol": PROTOCOL, "status": "completed", "topology_manifest_sha256": sha256(manifest_path),
        "episode_count_per_condition": len(episode_ids), "conditions": [scenario.name for scenario in scenarios],
        "policy_inventory": [{key: (str(value) if key == "path" else value) for key, value in item.items()} for item in inventory],
        "optimizer_steps": 0, "training": "not performed", "raw_episode_results": str(raw_path),
    }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
