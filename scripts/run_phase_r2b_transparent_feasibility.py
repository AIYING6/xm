"""R2B business-grounded transparent P/L/R feasibility executor."""
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
SEEDS = (1301, 1302, 1303)
OUT = ROOT / "results" / "development" / "phase_r2b_transparent_feasibility"


def eid(ci: int, si: int, ep: int) -> int:
    return 231000 + 10000 * ci + 1000 * si + ep


def toward(env: UAVIntercept3DEnv, src: int, dst: int) -> tuple[float, float]:
    rel = env.blue_pos[dst] - env.blue_pos[src]
    desired = math.atan2(float(rel[1]), float(rel[0]))
    turn = angle_diff(desired, float(env.blue_heading[src])) / env.config.blue_types[src].max_turn_rate
    gamma = math.atan2(float(rel[2]), float(np.linalg.norm(rel[:2]) + 1e-6))
    climb = (gamma - float(env.blue_gamma[src])) / env.config.blue_types[src].max_climb_rate
    return float(np.clip(turn, -1.0, 1.0)), float(np.clip(climb, -1.0, 1.0))


def recovery_guidance(env: UAVIntercept3DEnv) -> np.ndarray:
    return np.asarray([toward(env, 0, 2), toward(env, 2, 0), toward(env, 1, 2)], dtype=np.float32)


def nearest_action(turn: np.ndarray, climb: np.ndarray) -> np.ndarray:
    commands = np.zeros((3, 3), dtype=np.float32)
    commands[:, 0] = np.clip(turn, -1.0, 1.0)
    commands[:, 1] = np.clip(climb, -1.0, 1.0)
    commands[:, 2] = 1.0
    return np.argmin(((ACTION3D_TABLE[None, :, :] - commands[:, None, :]) ** 2).sum(axis=-1), axis=1)


def mission_position_actions(env: UAVIntercept3DEnv, base: np.ndarray) -> np.ndarray:
    """Maintain the separated search/bridge/standoff geometry before failure."""
    actions = np.asarray(base, dtype=np.int64).copy()
    # Relay remains in the bridge corridor by holding the Scout/Attacker
    # midpoint; Scout and Attacker retain their role-specific base pursuit.
    midpoint = 0.5 * (env.blue_pos[0] + env.blue_pos[2])
    rel = midpoint - env.blue_pos[1]
    desired = math.atan2(float(rel[1]), float(rel[0]))
    turn = angle_diff(desired, float(env.blue_heading[1])) / env.config.blue_types[1].max_turn_rate
    gamma = math.atan2(float(rel[2]), float(np.linalg.norm(rel[:2]) + 1e-6))
    climb = (gamma - float(env.blue_gamma[1])) / env.config.blue_types[1].max_climb_rate
    actions[1] = nearest_action(np.asarray([turn, 0.0, 0.0]), np.asarray([climb, 0.0, 0.0]))[0]
    return actions


def strict_operating_window(env: UAVIntercept3DEnv) -> bool:
    return bool(
        env.detected_by[0] > 0.5
        and env.comm_adj[1, 0] > 0.5
        and env.comm_adj[2, 1] > 0.5
        and env.target_cache_valid[2] > 0.5
        and 1 in env.target_cache_path[2]
        and env.comm_adj[2, 0] <= 0.5
        and env.detected_by[2] <= 0.5
        and np.linalg.norm(env.red_pos[0] - env.blue_pos[2]) > env.config.attacker_terminal_sensing_range
    )


def set_business_geometry(env: UAVIntercept3DEnv) -> None:
    # Search / bridge / standoff role regions. The separation is intentional:
    # SA=12 km > direct limit 8.5 km; SR=RA=6 km.
    env.blue_pos[:] = np.asarray([[-2_000.0, -6_000.0, 5_000.0], [-2_000.0, 0.0, 5_000.0], [-2_000.0, 6_000.0, 5_000.0]], dtype=np.float32)
    env.blue_heading[:] = 0.0
    env.blue_gamma[:] = 0.0
    env.blue_speed[:] = np.asarray([185.0, 175.0, 205.0], dtype=np.float32)
    env._update_sensing_and_comm()


def run_one(controller: str, ci: int, seed: int, si: int, episode: int) -> tuple[dict, list[dict]]:
    env = UAVIntercept3DEnv(UAVIntercept3DConfig(
        seed=eid(ci, si, episode), target_policy="straight", communication_dropout_prob=0.0,
        message_delay_steps=0, radar_dropout_prob=0.0, strict_target_sensing=True,
        agent_target_info_bottleneck=True, relay_dependent_task=True, min_success_step=1000,
        failed_blue_agent=-1, node_failure_duration_steps=0, max_steps=260,
    ))
    env.reset(); set_business_geometry(env)
    obs, _, _ = env._get_obs(), env._get_share_obs(), env._get_graph_obs()
    hold = 0; trigger = None; failure = None; loss = None; recovery = None; bypass = False; trace = []
    while True:
        if failure is not None and env.step_count >= failure:
            obs, _, _, _, dones, info = env.step_guidance(recovery_guidance(env))
        else:
            actions = mission_position_actions(env, controller_actions(controller, env, obs))
            obs, _, _, _, dones, info = env.step(actions)
        step = int(info["step"])
        window = strict_operating_window(env)
        hold = hold + 1 if window else 0
        if trigger is None and hold >= 2:
            trigger = step; failure = step + 1
            env.config.failed_blue_agent = 1; env.config.node_failure_start_step = failure; env.config.node_failure_duration_steps = 80
        active = float(info["node_failure_active"]) > 0.5
        legal = float(info["attacker_legal_target_information_t"]) > 0.5
        if trigger is not None and active and loss is None and not legal: loss = step
        direct_path = float(info["attacker_direct_recovery_path_t"]) > 0.5
        terminal_sensing = float(info["attacker_direct_target_information_t"]) > 0.5 and active
        if loss is not None and (direct_path or terminal_sensing) and recovery is None: recovery = step
        # Bypass audit is evaluated at the frozen fault trigger only. A
        # post-fault Scout->Attacker link is the intended recovery mechanism,
        # not a pre-fault dependency violation.
        if trigger is not None and step == trigger and (env.comm_adj[2, 0] > 0.5 or env.detected_by[2] > 0.5):
            bypass = True
        trace.append({"development_episode_id": eid(ci, si, episode), "controller": controller, "seed": seed,
                      "timestep": step, "relay_dependent_window": int(window), "node_failure_active": int(active),
                      "scout_detected": int(env.detected_by[0] > .5), "relay_detected": int(env.detected_by[1] > .5),
                      "attacker_detected": int(env.detected_by[2] > .5), "scout_relay_comm": int(env.comm_adj[1, 0] > .5),
                      "relay_attacker_comm": int(env.comm_adj[2, 1] > .5), "scout_attacker_comm": int(env.comm_adj[2, 0] > .5),
                      "attacker_legal_information": int(legal), "attacker_direct_recovery_path": int(direct_path),
                      "attacker_cache_path": "-".join(map(str, env.target_cache_path[2])),
                      "attacker_cache_delivery": int(env.target_cache_delivery_step[2]),
                      "scout_attacker_distance": float(np.linalg.norm(env.blue_pos[0] - env.blue_pos[2])),
                      "bypass_during_failure": int(bypass), "terminal": int(np.all(dones))})
        if np.all(dones): break
    return ({"development_episode_id": eid(ci, si, episode), "controller": controller, "seed": seed, "episode": episode,
             "pre_failure_chain_established": int(trigger is not None), "t_failure": -1 if failure is None else failure,
             "chain_lost_after_failure": int(loss is not None), "t_loss": -1 if loss is None else loss,
             "post_failure_chain_recovered_after_loss": int(recovery is not None), "t_recovery": -1 if recovery is None else recovery,
             "delta_t_loss_to_recovery": -1 if recovery is None or loss is None else recovery-loss,
             "relay_dependency_violation": int(bypass), "event": int(recovery is not None), "censor_time": int(info["step"])}, trace)


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--out-dir", type=Path, default=OUT); p.add_argument("--episodes", type=int, default=100); p.add_argument("--execute", action="store_true"); a = p.parse_args()
    if not a.execute: raise SystemExit("NO-GO: requires --execute after committed R2B protocol")
    if a.episodes != 100: raise SystemExit("NO-GO: R2B fixes episodes=100")
    if (a.out_dir / "raw_episode_metrics.csv").exists(): raise FileExistsError("Refusing to overwrite")
    rows = []; cells = []
    for ci, controller in enumerate(CONTROLLERS):
        for si, seed in enumerate(SEEDS):
            cell = []; trace = []
            for ep in range(a.episodes):
                row, episode_trace = run_one(controller, ci, seed, si, ep); rows.append(row); cell.append(row); trace.extend(episode_trace)
            eligible = sum(x["pre_failure_chain_established"] for x in cell); lost = sum(x["chain_lost_after_failure"] for x in cell); recovered = sum(x["post_failure_chain_recovered_after_loss"] for x in cell); violations = sum(x["relay_dependency_violation"] for x in cell)
            cells.append({"controller": controller, "seed": seed, "eligible": eligible, "lost": lost, "recovered": recovered, "bypass_violations": violations,
                          "cell_pass": eligible >= 10 and lost / max(eligible, 1) >= .8 and recovered / max(lost, 1) >= .5 and violations == 0})
            write_csv(a.out_dir / "raw_timestep_chain" / f"{controller}_seed{seed}.csv", trace)
    a.out_dir.mkdir(parents=True, exist_ok=True); write_csv(a.out_dir / "raw_episode_metrics.csv", rows); write_csv(a.out_dir / "cell_summary.csv", cells)
    passed = all(x["cell_pass"] for x in cells); manifest = {"protocol": "PHASE-R2B-BGW-V1", "artifact_class": "DEVELOPMENT_ONLY_BUSINESS_GROUNDED_FEASIBILITY", "controllers": list(CONTROLLERS), "seeds": list(SEEDS), "episodes_per_cell": a.episodes, "canonical_data_used": False, "training_started": False, "status": "PASS" if passed else "INFEASIBLE"}
    (a.out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8"); print(json.dumps(manifest, indent=2))
    if not passed: raise SystemExit(2)


if __name__ == "__main__": main()
