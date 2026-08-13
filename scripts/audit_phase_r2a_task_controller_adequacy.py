"""Read-only R2-A diagnosis of pre-chain and post-fault information paths.

This is not a new feasibility result and does not modify the frozen protocol.
It intentionally runs a small diagnostic sample and records causal fields that
the previous R1/R2 summary did not expose.
"""
from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv, angle_diff
from run_phase2ia6_task_feasibility import controller_actions

OUT = ROOT / "results" / "development" / "phase_r2a_adequacy_audit"
CONTROLLERS = ("structural_oracle", "legal_observation")
SEEDS = (1201, 1202, 1203)


def toward(env: UAVIntercept3DEnv, src: int, dst: int) -> tuple[float, float]:
    rel = env.blue_pos[dst] - env.blue_pos[src]
    heading = math.atan2(float(rel[1]), float(rel[0]))
    turn = angle_diff(heading, float(env.blue_heading[src])) / env.config.blue_types[src].max_turn_rate
    gamma = math.atan2(float(rel[2]), float(np.linalg.norm(rel[:2]) + 1e-6))
    climb = (gamma - float(env.blue_gamma[src])) / env.config.blue_types[src].max_climb_rate
    return float(np.clip(turn, -1.0, 1.0)), float(np.clip(climb, -1.0, 1.0))


def guidance(env: UAVIntercept3DEnv) -> np.ndarray:
    return np.asarray([toward(env, 0, 2), toward(env, 2, 0), toward(env, 1, 2)], dtype=np.float32)


def run(controller: str, seed: int, episode: int) -> list[dict]:
    env = UAVIntercept3DEnv(
        UAVIntercept3DConfig(
            seed=seed * 1000 + episode,
            target_policy="straight",
            communication_dropout_prob=0.0,
            message_delay_steps=0,
            radar_dropout_prob=0.0,
            strict_target_sensing=True,
            agent_target_info_bottleneck=True,
            relay_dependent_task=True,
            min_success_step=1000,
            failed_blue_agent=-1,
            node_failure_duration_steps=0,
            max_steps=260,
        )
    )
    obs, _, _ = env.reset()
    hold = 0
    failure = None
    rows: list[dict] = []
    while True:
        if failure is not None and env.step_count >= failure:
            obs, _, _, _, dones, info = env.step_guidance(guidance(env))
        else:
            obs, _, _, _, dones, info = env.step(controller_actions(controller, env, obs))
        step = int(info["step"])
        primary = float(info["relay_dependency_eligible_t"]) > 0.5
        hold = hold + 1 if primary else 0
        if failure is None and hold >= 2 and step <= 220:
            failure = step + 1
            env.config.failed_blue_agent = 1
            env.config.node_failure_start_step = failure
            env.config.node_failure_duration_steps = 80
        paths = [list(path) for path in env.target_cache_path]
        rows.append(
            {
                "controller": controller,
                "seed": seed,
                "episode": episode,
                "timestep": step,
                "failure_step": -1 if failure is None else failure,
                "failure_active": int(info["node_failure_active"] > 0.5),
                "scout_detected": int(env.detected_by[0] > 0.5),
                "relay_detected": int(env.detected_by[1] > 0.5),
                "attacker_detected": int(env.detected_by[2] > 0.5),
                "scout_relay_distance": float(np.linalg.norm(env.blue_pos[0] - env.blue_pos[1])),
                "relay_attacker_distance": float(np.linalg.norm(env.blue_pos[1] - env.blue_pos[2])),
                "scout_attacker_distance": float(np.linalg.norm(env.blue_pos[0] - env.blue_pos[2])),
                "scout_relay_comm": int(env.comm_adj[1, 0] > 0.5),
                "relay_attacker_comm": int(env.comm_adj[2, 1] > 0.5),
                "scout_attacker_comm": int(env.comm_adj[2, 0] > 0.5),
                "cache_valid_0": int(env.target_cache_valid[0] > 0.5),
                "cache_valid_1": int(env.target_cache_valid[1] > 0.5),
                "cache_valid_2": int(env.target_cache_valid[2] > 0.5),
                "cache_path_0": "-".join(map(str, paths[0])),
                "cache_path_1": "-".join(map(str, paths[1])),
                "cache_path_2": "-".join(map(str, paths[2])),
                "cache_delivery_2": int(env.target_cache_delivery_step[2]),
                "cache_generation_2": int(env.target_cache_generation_step[2]),
                "relay_dependency_eligible": int(primary),
                "attacker_legal_information": int(info["attacker_legal_target_information_t"] > 0.5),
                "attacker_direct_recovery_path": int(info["attacker_direct_recovery_path_t"] > 0.5),
                "terminal_sensing_range": float(env.config.attacker_terminal_sensing_range),
                "terminal": int(np.all(dones)),
            }
        )
        if np.all(dones):
            break
    return rows


def main() -> None:
    rows: list[dict] = []
    for controller in CONTROLLERS:
        for seed in SEEDS:
            for episode in range(3):
                rows.extend(run(controller, seed, episode))
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "raw_timestep_diagnostics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = {
        "protocol": "PHASE-R2A-DIAGNOSTIC-V1",
        "artifact_class": "READ_ONLY_CONTROLLER_ADEQUACY_AUDIT",
        "episodes": 18,
        "canonical_data_used": False,
        "training_started": False,
        "notes": "No endpoint, geometry, TTL, seed set, or failure protocol was modified.",
    }
    (OUT / "manifest.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
