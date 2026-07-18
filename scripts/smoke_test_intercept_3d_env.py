from __future__ import annotations

import csv
import math
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from envs import RELATION_COMMUNICATION, UAVIntercept3DConfig, UAVIntercept3DEnv


OUT_CSV = ROOT / "results" / "intercept_3d_smoke_test.csv"
OUT_MD = ROOT / "docs" / "intercept_3d_smoke_test.md"


def geometric_policy(env: UAVIntercept3DEnv) -> np.ndarray:
    actions = []
    target = env.red_pos[0]
    for i in range(env.config.num_blue):
        rel = target - env.blue_pos[i]
        desired_heading = math.atan2(float(rel[1]), float(rel[0]))
        heading_error = angle_diff(desired_heading, float(env.blue_heading[i]))
        turn = -1 if heading_error < -0.05 else 1 if heading_error > 0.05 else 0

        desired_gamma = math.atan2(float(rel[2]), float(np.linalg.norm(rel[:2]) + 1e-6))
        gamma_error = desired_gamma - float(env.blue_gamma[i])
        climb = -1 if gamma_error < -0.02 else 1 if gamma_error > 0.02 else 0

        dist = float(np.linalg.norm(rel))
        accel = 1 if dist > 5_500 else -1 if dist < 2_000 else 0
        actions.append(action_index(turn, climb, accel))
    return np.asarray(actions, dtype=np.int64)


def action_index(turn: int, climb: int, accel: int) -> int:
    return (turn + 1) * 9 + (climb + 1) * 3 + (accel + 1)


def angle_diff(target: float, source: float) -> float:
    return (target - source + math.pi) % (2 * math.pi) - math.pi


def assert_shapes(env: UAVIntercept3DEnv, obs: np.ndarray, share_obs: np.ndarray, graph_obs: dict[str, np.ndarray]) -> None:
    assert obs.shape == (env.config.num_blue, env.obs_dim), obs.shape
    assert share_obs.shape == (env.config.num_blue, env.share_obs_dim), share_obs.shape
    assert graph_obs["node_feat"].shape == (env.config.num_blue + env.config.num_red, env.node_feat_dim)
    assert graph_obs["edge_feat"].shape == (
        env.config.num_blue + env.config.num_red,
        env.config.num_blue + env.config.num_red,
        env.edge_feat_dim,
    )
    assert graph_obs["adj"].shape == (
        env.config.num_blue + env.config.num_red,
        env.config.num_blue + env.config.num_red,
    )
    assert graph_obs["relation_adj"].shape == (
        env.relation_count,
        env.config.num_blue + env.config.num_red,
        env.config.num_blue + env.config.num_red,
    )
    assert graph_obs["role"].shape == (env.config.num_blue + env.config.num_red,)
    assert np.all(np.isfinite(graph_obs["relation_adj"]))
    assert np.all(graph_obs["relation_adj"] >= 0.0)
    assert np.all(graph_obs["relation_adj"] <= 1.0)
    assert np.all(graph_obs["adj"] + 1e-6 >= np.max(graph_obs["relation_adj"], axis=0))


def assert_multirelation_semantics() -> None:
    env = UAVIntercept3DEnv(UAVIntercept3DConfig(seed=71))
    env.reset()
    env.detected_by[:] = np.asarray([1.0, 0.0, 0.0], dtype=np.float32)
    env.comm_adj[:] = 1.0
    env.attack_window[:] = np.asarray([0.0, 0.0, 1.0], dtype=np.float32)
    graph = env._get_graph_obs()
    perception, communication, support = graph["relation_adj"]
    target = env.config.num_blue

    assert perception[0, target] == 1.0
    assert np.count_nonzero(perception[:, :target]) == 0
    assert np.count_nonzero(communication[:, target:]) == 0
    # Graph convention: A[receiver, sender] = 1.
    assert support[2, 0] == 1.0  # attacker receives target-support information from scout
    assert support[0, 1] == 1.0 and support[2, 1] == 1.0  # scout/attacker receive relay support
    assert support[1, 2] == 1.0  # relay receives attacker attack-window feedback
    assert support[0, 2] == 0.0

    env.detected_by[:] = 0.0
    env.comm_adj[:] = np.eye(env.config.num_blue, dtype=np.float32)
    env.attack_window[:] = 0.0
    inactive = env._get_graph_obs()["relation_adj"][2]
    assert np.count_nonzero(inactive) == 0

    ablated = UAVIntercept3DEnv(UAVIntercept3DConfig(seed=71, graph_relation_ablation="no_task_support"))
    ablated.reset()
    ablated.detected_by[:] = np.asarray([1.0, 0.0, 0.0], dtype=np.float32)
    ablated.comm_adj[:] = 1.0
    ablated.attack_window[:] = np.asarray([0.0, 0.0, 1.0], dtype=np.float32)
    ablated_graph = ablated._get_graph_obs()
    assert np.count_nonzero(ablated_graph["relation_adj"][2]) == 0
    assert ablated_graph["edge_feat"][2, 0, 13] == 0.0


def assert_topology_disruption_semantics() -> None:
    env = UAVIntercept3DEnv(
        UAVIntercept3DConfig(
            seed=73,
            communication_range_scale=0.01,
            failed_blue_agent=1,
            node_failure_start_step=0,
            node_failure_duration_steps=20,
        )
    )
    env.reset()
    comm_relation = env._get_graph_obs()["relation_adj"][RELATION_COMMUNICATION]
    other_agents = [i for i in range(env.config.num_blue) if i != 1]
    assert np.all(comm_relation[1, other_agents] == 0.0)
    assert np.all(comm_relation[other_agents, 1] == 0.0)
    assert env._info(timeout=False)["node_failure_active"] == 1.0

    env.config.node_failure_duration_steps = 0
    env.config.communication_range_scale = 10.0
    env._update_sensing_and_comm()
    restored = env._get_graph_obs()["relation_adj"][RELATION_COMMUNICATION]
    off_diag = restored[: env.config.num_blue, : env.config.num_blue][~np.eye(env.config.num_blue, dtype=bool)]
    assert float(np.mean(off_diag)) > 0.0


def run_episode(seed: int, policy: str) -> dict[str, str]:
    cfg = UAVIntercept3DConfig(
        seed=seed,
        communication_dropout_prob=0.10 if policy == "geometric_dropout" else 0.0,
        radar_dropout_prob=0.05 if policy == "geometric_dropout" else 0.0,
        message_delay_steps=2 if policy == "geometric_dropout" else 0,
    )
    env = UAVIntercept3DEnv(cfg)
    obs, share_obs, graph_obs = env.reset()
    assert_shapes(env, obs, share_obs, graph_obs)
    done = False
    info: dict[str, float] = {}
    reward_sum = 0.0
    while not done:
        if policy == "random":
            actions = env.rng.integers(0, env.action_dim, size=env.config.num_blue)
        else:
            actions = geometric_policy(env)
        obs, share_obs, graph_obs, rewards, dones, info = env.step(actions)
        assert_shapes(env, obs, share_obs, graph_obs)
        assert rewards.shape == (env.config.num_blue, 1), rewards.shape
        assert dones.shape == (env.config.num_blue, 1), dones.shape
        assert np.all(np.isfinite(obs))
        assert np.all(np.isfinite(share_obs))
        assert np.all(np.isfinite(graph_obs["node_feat"]))
        assert np.all(np.isfinite(graph_obs["edge_feat"]))
        assert np.all(np.isfinite(graph_obs["adj"]))
        reward_sum += float(np.mean(rewards))
        done = bool(np.all(dones))

    return {
        "policy": policy,
        "seed": str(seed),
        "success": f"{info.get('success', 0.0):.0f}",
        "timeout": f"{info.get('timeout', 0.0):.0f}",
        "collision": f"{info.get('collision', 0.0):.0f}",
        "constraint_violation": f"{info.get('constraint_violation', 0.0):.0f}",
        "steps": f"{info.get('step', 0.0):.0f}",
        "mean_range": f"{info.get('mean_range', 0.0):.3f}",
        "tracking_rate": f"{info.get('tracking_rate', 0.0):.3f}",
        "attack_window_rate": f"{info.get('attack_window_rate', 0.0):.3f}",
        "comm_connectivity": f"{info.get('comm_connectivity', 0.0):.3f}",
        "mean_message_age": f"{info.get('mean_message_age', 0.0):.3f}",
        "reward_sum": f"{reward_sum:.3f}",
    }


def write_outputs(rows: list[dict[str, str]]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys())
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    by_policy: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_policy.setdefault(row["policy"], []).append(row)

    lines = [
        "# 3DOF Interception Environment Smoke Test",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Purpose:",
        "",
        "```text",
        "Validate the first 3DOF heterogeneous UAV interception environment before connecting it to EA-RG-MAPPO-S training.",
        "This is an interface and dynamics smoke test, not a learning result.",
        "```",
        "",
        "## Summary",
        "",
        "| Policy | Episodes | Success | Collision | Constraint Violation | Mean Steps | Mean Tracking | Mean Attack Window | Mean Connectivity | Mean Message Age |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for policy, items in sorted(by_policy.items()):
        n = len(items)
        mean = lambda key: sum(float(row[key]) for row in items) / n
        lines.append(
            f"| {policy} | {n} | {mean('success'):.3f} | {mean('collision'):.3f} | "
            f"{mean('constraint_violation'):.3f} | {mean('steps'):.1f} | {mean('tracking_rate'):.3f} | "
            f"{mean('attack_window_rate'):.3f} | {mean('comm_connectivity'):.3f} | {mean('mean_message_age'):.3f} |"
        )

    lines.extend(
        [
            "",
            "## Interface Checked",
            "",
            "```text",
            "reset -> obs, share_obs, graph_obs",
            "step -> obs, share_obs, graph_obs, rewards, dones, infos",
            "obs shape = (3, 34)",
            "share_obs shape = (3, 47)",
            "node_feat shape = (4, 20)",
            "edge_feat shape = (4, 4, 18)",
            "adj shape = (4, 4)",
            "relation_adj shape = (3, 4, 4)",
            "```",
            "",
            "## Boundary",
            "",
            "```text",
            "The smoke test proves that the 3DOF environment interface, graph observations, and mission-chain metrics are finite and executable.",
            "It does not yet prove trainability or paper-level performance.",
            "```",
            "",
        ]
    )
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    assert_multirelation_semantics()
    assert_topology_disruption_semantics()
    rows = []
    for policy in ("random", "geometric", "geometric_dropout"):
        for seed in range(5):
            rows.append(run_episode(seed, policy))
    write_outputs(rows)
    print(OUT_CSV)
    print(OUT_MD)
    print(f"episodes: {len(rows)}")


if __name__ == "__main__":
    main()
