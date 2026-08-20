"""T0 telemetry-native evaluation primitives.

This module is intentionally independent of historical result CSVs.  A raw
step JSONL stream is the sole evidence source; every episode aggregate is
derived from that stream and can be re-derived without an environment or a
checkpoint.  It is a technical-evidence utility, not a training algorithm.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable

import numpy as np

from envs.uav_intercept_3d_env import ACTION3D_TABLE, UAVIntercept3DConfig, UAVIntercept3DEnv


PROTOCOL = "T0-TELEMETRY-NATIVE-V1"
SCHEMA_VERSION = 1
ACTOR_LEGAL = "actor_legal"
DIAGNOSTIC_ONLY = "diagnostic_only"


@dataclass(frozen=True)
class FailureScenario:
    """A frozen environment descriptor; no global topology truth is exposed to the actor."""

    name: str
    failed_blue_agent: int = -1
    start_step: int = 0
    duration_steps: int = 0


NOMINAL = FailureScenario("nominal")
F0 = FailureScenario("f0_44_80", failed_blue_agent=1, start_step=44, duration_steps=80)

# ``cac`` remains compatible with Python 3.8, where builtin ``dict`` is not
# subscriptable at runtime in a type-alias expression.
ActionPolicy = Callable[[np.ndarray, np.ndarray, Dict[str, Any]], np.ndarray]


def json_safe(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def canonical_line(value: dict[str, Any]) -> str:
    return json.dumps(json_safe(value), sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def make_env(episode_id: int, scenario: FailureScenario) -> UAVIntercept3DEnv:
    """Build the frozen S2 task without changing its dynamics or reward."""
    return UAVIntercept3DEnv(UAVIntercept3DConfig(
        seed=int(episode_id), target_policy="straight", strict_target_sensing=True,
        agent_target_info_bottleneck=True, relay_dependent_task=True,
        business_grounded_geometry=True, communication_range_scale=1.0,
        communication_dropout_prob=0.0, message_delay_steps=0,
        radar_dropout_prob=0.0, max_steps=260, min_success_step=260,
        failed_blue_agent=scenario.failed_blue_agent,
        node_failure_start_step=scenario.start_step,
        node_failure_duration_steps=scenario.duration_steps,
    ))


def zero_policy(obs: np.ndarray, share_obs: np.ndarray, graph: dict[str, Any]) -> np.ndarray:
    """Deterministic legal smoke policy; receives only actor-legal inputs."""
    del share_obs, graph
    # The graph includes a target node, while ``obs`` has exactly one row per
    # controllable blue agent.
    return np.zeros(obs.shape[0], dtype=np.int64)


def actor_view(obs: np.ndarray, share_obs: np.ndarray, graph: dict[str, Any]) -> dict[str, Any]:
    """Record exactly the policy-side inputs, separately from diagnostics."""
    return {
        "classification": ACTOR_LEGAL,
        "obs": np.asarray(obs, dtype=np.float32),
        "share_obs": np.asarray(share_obs, dtype=np.float32),
        "graph_node_feat": np.asarray(graph["node_feat"], dtype=np.float32),
        "graph_edge_feat": np.asarray(graph["edge_feat"], dtype=np.float32),
        "graph_adj": np.asarray(graph["adj"], dtype=np.float32),
        "graph_relation_adj": np.asarray(graph["relation_adj"], dtype=np.float32),
        "graph_role": np.asarray(graph["role"], dtype=np.int64),
    }


def diagnostic_view(env: UAVIntercept3DEnv, info: dict[str, Any]) -> dict[str, Any]:
    """Simulator state retained for audit only and never handed to a policy."""
    keys = (
        "node_failure_active", "chain_support_t", "attacker_cache_paths_t",
        "attacker_legal_target_information_t", "target_cache_age_mean", "collision",
        "timeout", "constraint_violation", "success", "step",
    )
    return {
        "classification": DIAGNOSTIC_ONLY,
        "blue_position": env.blue_pos.copy(),
        "red_position": env.red_pos.copy(),
        "blue_speed": env.blue_speed.copy(),
        "blue_heading": env.blue_heading.copy(),
        "blue_gamma": env.blue_gamma.copy(),
        "info": {key: json_safe(info.get(key)) for key in keys},
    }


def summarize_steps(step_rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(step_rows)
    if not rows:
        raise ValueError("cannot aggregate an empty episode")
    final = rows[-1]
    active = [row for row in rows if int(row["failure_active_post"]) == 1]
    denom = max(1, len(active))
    paths = [str(row["diagnostic"]["info"].get("attacker_cache_paths_t") or "") for row in rows]
    return {
        "protocol": PROTOCOL,
        "schema_version": SCHEMA_VERSION,
        "episode_id": int(final["episode_id"]),
        "scenario": str(final["scenario"]),
        "scheduled_failure_onset": int(final["scheduled_failure_onset"]),
        "scheduled_failure_duration": int(final["scheduled_failure_duration"]),
        "J": float(sum(float(row["reward_sum_step"]) for row in rows)),
        "traveled_distance": float(sum(float(row["movement_distance"]) for row in rows)),
        "control_effort": float(sum(float(row["control_effort"]) for row in rows)),
        "terminal_step": int(final["post_step"]),
        "success": int(final["diagnostic"]["info"].get("success") or 0),
        "collision": int(final["diagnostic"]["info"].get("collision") or 0),
        "timeout": int(final["diagnostic"]["info"].get("timeout") or 0),
        "constraint_violation": int(final["diagnostic"]["info"].get("constraint_violation") or 0),
        "failure_exposed": int(bool(active)),
        "direct_path_fraction_during_failure": float(sum(
            str(row["diagnostic"]["info"].get("attacker_cache_paths_t") or "") == "0-2" for row in active
        ) / denom),
        "relay_path_fraction_during_failure": float(sum(
            str(row["diagnostic"]["info"].get("attacker_cache_paths_t") or "") == "0-1-2" for row in active
        ) / denom),
        "task_support_fraction_during_failure": float(sum(
            int(row["diagnostic"]["info"].get("chain_support_t") or 0) for row in active
        ) / denom),
        "legal_information_fraction_during_failure": float(sum(
            int(row["diagnostic"]["info"].get("attacker_legal_target_information_t") or 0) for row in active
        ) / denom),
        "mean_cache_age_during_failure": (
            float(np.mean([float(row["diagnostic"]["info"].get("target_cache_age_mean") or 0.0) for row in active]))
            if active else None
        ),
        "path_switch_count": int(sum(left != right for left, right in zip(paths, paths[1:]))),
        "step_count": len(rows),
    }


def run_episode(episode_id: int, scenario: FailureScenario, policy: ActionPolicy = zero_policy) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Run one episode while preventing diagnostic state from reaching ``policy``."""
    env = make_env(episode_id, scenario)
    obs, share_obs, graph = env.reset()
    previous = env.blue_pos.copy()
    rows: list[dict[str, Any]] = []
    while True:
        pre_step = int(env.step_count)
        legal = actor_view(obs, share_obs, graph)
        # The policy receives only the S2 decentralized actor interface.
        actions = np.asarray(policy(obs.copy(), share_obs.copy(), graph), dtype=np.int64)
        if actions.shape != (env.num_agents,) or np.any(actions < 0) or np.any(actions >= env.action_dim):
            raise ValueError("policy emitted an invalid action vector")
        obs, share_obs, graph, rewards, dones, info = env.step(actions)
        movement = float(np.linalg.norm(env.blue_pos - previous, axis=1).sum())
        previous = env.blue_pos.copy()
        diagnostic = diagnostic_view(env, info)
        rows.append({
            "protocol": PROTOCOL, "schema_version": SCHEMA_VERSION,
            "episode_id": int(episode_id), "scenario": scenario.name,
            "timestep": pre_step, "post_step": int(info["step"]),
            "scheduled_failure_onset": int(scenario.start_step),
            "scheduled_failure_duration": int(scenario.duration_steps),
            "actor": legal,
            "action_index": actions,
            "applied_action_components": ACTION3D_TABLE[actions].astype(np.float32),
            "control_effort": float(np.abs(ACTION3D_TABLE[actions, :2]).sum()),
            "reward_sum_step": float(np.sum(rewards)),
            "movement_distance": movement,
            "failure_active_post": int(bool(info.get("node_failure_active", 0.0))),
            "terminal": int(bool(np.all(dones))),
            "diagnostic": diagnostic,
        })
        if np.all(dones):
            break
    return rows, summarize_steps(rows)


def run_episode_without_logger(
    episode_id: int, scenario: FailureScenario, policy: ActionPolicy = zero_policy,
) -> dict[str, Any]:
    """Independent no-raw-logger path used only for a noninterference gate.

    It intentionally does not build actor snapshots, diagnostic positions, or
    JSON records.  Its final summary must equal ``run_episode`` for the same
    deterministic seed and policy.
    """
    env = make_env(episode_id, scenario)
    obs, share_obs, graph = env.reset()
    previous = env.blue_pos.copy()
    summary_rows: list[dict[str, Any]] = []
    while True:
        actions = np.asarray(policy(obs.copy(), share_obs.copy(), graph), dtype=np.int64)
        if actions.shape != (env.num_agents,) or np.any(actions < 0) or np.any(actions >= env.action_dim):
            raise ValueError("policy emitted an invalid action vector")
        obs, share_obs, graph, rewards, dones, info = env.step(actions)
        movement = float(np.linalg.norm(env.blue_pos - previous, axis=1).sum())
        previous = env.blue_pos.copy()
        summary_rows.append({
            "protocol": PROTOCOL, "schema_version": SCHEMA_VERSION,
            "episode_id": int(episode_id), "scenario": scenario.name,
            "post_step": int(info["step"]),
            "scheduled_failure_onset": int(scenario.start_step),
            "scheduled_failure_duration": int(scenario.duration_steps),
            "reward_sum_step": float(np.sum(rewards)),
            "movement_distance": movement,
            "control_effort": float(np.abs(ACTION3D_TABLE[actions, :2]).sum()),
            "failure_active_post": int(bool(info.get("node_failure_active", 0.0))),
            "diagnostic": {"info": {
                "attacker_cache_paths_t": info.get("attacker_cache_paths_t"),
                "chain_support_t": info.get("chain_support_t"),
                "attacker_legal_target_information_t": info.get("attacker_legal_target_information_t"),
                "target_cache_age_mean": info.get("target_cache_age_mean"),
                "success": info.get("success"), "collision": info.get("collision"),
                "timeout": info.get("timeout"), "constraint_violation": info.get("constraint_violation"),
            }},
        })
        if np.all(dones):
            break
    return summarize_steps(summary_rows)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(canonical_line(row) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_evidence_bundle(output_root: Path, plans: Iterable[tuple[int, FailureScenario]], policy: ActionPolicy = zero_policy) -> dict[str, Any]:
    """Write raw data, derive aggregates from it, then verify source closure."""
    if output_root.exists() and any(output_root.iterdir()):
        raise FileExistsError(f"refusing to overwrite telemetry-native output: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)
    all_steps: list[dict[str, Any]] = []
    expected: list[dict[str, Any]] = []
    for episode_id, scenario in plans:
        steps, aggregate = run_episode(episode_id, scenario, policy)
        all_steps.extend(steps)
        expected.append(aggregate)
    raw_path = output_root / "raw_step_telemetry.jsonl"
    write_jsonl(raw_path, all_steps)
    restored = read_jsonl(raw_path)
    observed: list[dict[str, Any]] = []
    cursor = 0
    for aggregate in expected:
        count = int(aggregate["step_count"])
        observed.append(summarize_steps(restored[cursor:cursor + count]))
        cursor += count
    if cursor != len(restored) or [canonical_line(row) for row in observed] != [canonical_line(row) for row in expected]:
        raise RuntimeError("raw telemetry aggregation closure failed")
    aggregate_path = output_root / "episode_aggregates.jsonl"
    write_jsonl(aggregate_path, observed)
    manifest = {
        "protocol": PROTOCOL, "schema_version": SCHEMA_VERSION,
        "raw_step_telemetry_sha256": sha256(raw_path),
        "episode_aggregates_sha256": sha256(aggregate_path),
        "episode_count": len(expected), "step_count": len(restored),
        "plans": [{"episode_id": int(episode_id), "scenario": asdict(scenario)} for episode_id, scenario in plans],
        "aggregate_source": "raw_step_telemetry.jsonl only",
        "historical_aggregate_reuse": False,
        "actor_boundary": "policy receives only obs/share_obs/graph; simulator state is diagnostic_only",
        "source_closure_pass": True,
    }
    (output_root / "manifest.json").write_text(canonical_line(manifest) + "\n", encoding="utf-8")
    return manifest
