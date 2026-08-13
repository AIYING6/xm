"""R1-R2 transparent recovery controller; no training or checkpoint reads."""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from envs.uav_intercept_3d_env import ACTION3D_TABLE, UAVIntercept3DConfig, UAVIntercept3DEnv, angle_diff
from run_phase2ia6_task_feasibility import controller_actions

CONTROLLERS = ("structural_oracle", "legal_observation")
SEEDS = (1201, 1202, 1203)
OUT = ROOT / "results" / "development" / "phase_r1_r2_recovery_controller"


def eid(ci: int, si: int, ep: int) -> int:
    return 221000 + 10000 * ci + 1000 * si + ep


def guidance_toward(env: UAVIntercept3DEnv, src: int, dst: int) -> tuple[float, float]:
    rel = env.blue_pos[dst] - env.blue_pos[src]
    desired_heading = math.atan2(float(rel[1]), float(rel[0]))
    turn = angle_diff(desired_heading, float(env.blue_heading[src])) / env.config.blue_types[src].max_turn_rate
    desired_gamma = math.atan2(float(rel[2]), float(np.linalg.norm(rel[:2]) + 1e-6))
    climb = (desired_gamma - float(env.blue_gamma[src])) / env.config.blue_types[src].max_climb_rate
    return float(np.clip(turn, -1.0, 1.0)), float(np.clip(climb, -1.0, 1.0))


def recovery_guidance(env: UAVIntercept3DEnv) -> np.ndarray:
    guidance = np.zeros((env.num_agents, 2), dtype=np.float32)
    guidance[0] = guidance_toward(env, 0, 2)
    guidance[2] = guidance_toward(env, 2, 0)
    guidance[1] = guidance_toward(env, 1, 2)
    return guidance


def nearest_action(env: UAVIntercept3DEnv, turn: np.ndarray, climb: np.ndarray) -> np.ndarray:
    commands = np.zeros((env.num_agents, 3), dtype=np.float32)
    commands[:, 0] = np.clip(turn, -1.0, 1.0)
    commands[:, 1] = np.clip(climb, -1.0, 1.0)
    commands[:, 2] = 1.0
    return np.argmin(((ACTION3D_TABLE[None, :, :] - commands[:, None, :]) ** 2).sum(axis=-1), axis=1)


def formation_actions(env: UAVIntercept3DEnv, base: np.ndarray) -> np.ndarray:
    """Add only peer-geometry formation control before failure.

    Target pursuit remains in ``base``. The relay is steered toward the
    Scout/Attacker midpoint, using no target truth for its formation term.
    """
    actions = np.asarray(base, dtype=np.int64).copy()
    midpoint = 0.5 * (env.blue_pos[0] + env.blue_pos[2])
    rel = midpoint - env.blue_pos[1]
    desired_heading = math.atan2(float(rel[1]), float(rel[0]))
    turn = angle_diff(desired_heading, float(env.blue_heading[1])) / env.config.blue_types[1].max_turn_rate
    desired_gamma = math.atan2(float(rel[2]), float(np.linalg.norm(rel[:2]) + 1e-6))
    climb = (desired_gamma - float(env.blue_gamma[1])) / env.config.blue_types[1].max_climb_rate
    actions[1] = nearest_action(env, np.asarray([turn, 0.0, 0.0]), np.asarray([climb, 0.0, 0.0]))[0]
    return actions


def strict_trigger_guard(env: UAVIntercept3DEnv) -> bool:
    paths = env.target_cache_path[2]
    return bool(
        env.detected_by[0] > 0.5
        and env.comm_adj[1, 0] > 0.5
        and env.comm_adj[2, 1] > 0.5
        and env.target_cache_valid[2] > 0.5
        and 1 in paths
        and env.comm_adj[2, 0] <= 0.5
        and env.detected_by[2] <= 0.5
        and np.linalg.norm(env.red_pos[0] - env.blue_pos[2]) > env.config.attacker_terminal_sensing_range
    )


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run_one(controller: str, ci: int, seed: int, si: int, episode: int) -> tuple[dict, list[dict]]:
    env = UAVIntercept3DEnv(
        UAVIntercept3DConfig(
            seed=eid(ci, si, episode), target_policy="straight",
            communication_dropout_prob=0.0, message_delay_steps=0,
            radar_dropout_prob=0.0, strict_target_sensing=True,
            agent_target_info_bottleneck=True, relay_dependent_task=True,
            failed_blue_agent=-1, node_failure_duration_steps=0, max_steps=260,
            min_success_step=1000,
        )
    )
    obs, _, _ = env.reset()
    hold = 0; trigger = None; failure = None; loss = None; recovery = None; trace = []
    while True:
        if failure is not None and int(env.step_count) >= failure:
            actions = None
            guidance = recovery_guidance(env)
            obs, _, _, _, dones, info = env.step_guidance(guidance)
        else:
            actions = formation_actions(env, controller_actions(controller, env, obs))
            obs, _, _, _, dones, info = env.step(actions)
        step = int(info["step"])
        primary = float(info["relay_dependency_eligible_t"]) > 0.5
        hold = hold + 1 if primary else 0
        if trigger is None and hold >= 2 and step <= 220 and strict_trigger_guard(env):
            trigger = step; failure = step + 1
            env.config.failed_blue_agent = 1; env.config.node_failure_start_step = failure
            env.config.node_failure_duration_steps = 80
        active = float(info["node_failure_active"]) > 0.5
        legal = float(info["attacker_legal_target_information_t"]) > 0.5
        if trigger is not None and active and loss is None and not legal:
            loss = step
        direct_path = float(info["attacker_direct_recovery_path_t"]) > 0.5
        terminal_sensing = float(info["attacker_direct_target_information_t"]) > 0.5 and active
        if loss is not None and (direct_path or terminal_sensing) and recovery is None:
            recovery = step
        trace.append({
            "development_episode_id": eid(ci, si, episode), "controller": controller,
            "seed": seed, "timestep": step, "relay_dependency_eligible_t": float(primary),
            "attacker_legal_target_information_t": float(legal),
            "attacker_direct_recovery_path_t": float(direct_path),
            "attacker_direct_target_information_t": info["attacker_direct_target_information_t"],
            "attacker_cache_paths_t": info["attacker_cache_paths_t"],
            "attacker_target_cache_delivery_step_max": info["attacker_target_cache_delivery_step_max"],
            "node_failure_active": float(active), "scout_attacker_distance": float(np.linalg.norm(env.blue_pos[0] - env.blue_pos[2])),
            "terminal": float(np.all(dones)),
        })
        if np.all(dones): break
    return ({
        "development_episode_id": eid(ci, si, episode), "controller": controller, "seed": seed,
        "episode": episode, "pre_failure_chain_established": float(trigger is not None),
        "t_failure": -1 if failure is None else failure, "chain_lost_after_failure": float(loss is not None),
        "t_loss": -1 if loss is None else loss, "post_failure_chain_recovered_after_loss": float(recovery is not None),
        "t_recovery": -1 if recovery is None else recovery,
        "delta_t_loss_to_recovery": -1 if recovery is None or loss is None else recovery - loss,
        "event": float(recovery is not None), "censor_time": int(info["step"]),
    }, trace)


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--out-dir", type=Path, default=OUT)
    p.add_argument("--episodes", type=int, default=100); p.add_argument("--execute", action="store_true")
    a = p.parse_args()
    if not a.execute: raise SystemExit("NO-GO: requires --execute after committed R1-R2 protocol")
    if a.episodes != 100: raise SystemExit("NO-GO: protocol fixes episodes=100")
    if (a.out_dir / "raw_episode_metrics.csv").exists(): raise FileExistsError("Refusing to overwrite")
    rows = []; cells = []
    for ci, controller in enumerate(CONTROLLERS):
        for si, seed in enumerate(SEEDS):
            trace = []; cell = []
            for ep in range(a.episodes):
                row, ep_trace = run_one(controller, ci, seed, si, ep); rows.append(row); cell.append(row); trace.extend(ep_trace)
            eligible = sum(int(x["pre_failure_chain_established"]) for x in cell)
            lost = sum(int(x["chain_lost_after_failure"]) for x in cell)
            recovered = sum(int(x["post_failure_chain_recovered_after_loss"]) for x in cell)
            cells.append({"controller": controller, "seed": seed, "eligible": eligible, "lost": lost, "recovered": recovered,
                          "cell_pass": eligible >= 10 and lost / max(eligible, 1) >= .8 and recovered / max(lost, 1) >= .5})
            write_csv(a.out_dir / "raw_timestep_chain" / f"{controller}_seed{seed}.csv", trace)
    write_csv(a.out_dir / "raw_episode_metrics.csv", rows); write_csv(a.out_dir / "cell_summary.csv", cells)
    passed = all(bool(x["cell_pass"]) for x in cells)
    a.out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {"protocol": "PHASE-R1-R2-RC-V1", "artifact_class": "DEVELOPMENT_ONLY_RECOVERY_FEASIBILITY",
                "controllers": list(CONTROLLERS), "seeds": list(SEEDS), "episodes_per_cell": a.episodes,
                "canonical_data_used": False, "training_started": False, "status": "PASS" if passed else "INFEASIBLE"}
    (a.out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    if not passed: raise SystemExit(2)


if __name__ == "__main__": main()
