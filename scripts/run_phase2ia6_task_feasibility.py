"""Phase 2IA6 non-learning structural and legal-observation feasibility probes."""
from __future__ import annotations

import argparse
import ast
import csv
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT))
from envs.uav_intercept_3d_env import ACTION3D_TABLE, UAVIntercept3DConfig, UAVIntercept3DEnv, angle_diff

CONTROLLERS = ("structural_oracle", "legal_observation")
SEEDS = (601, 602, 603)
OUT = ROOT / "results" / "development" / "phase2ia6_task_feasibility"


def episode_id(controller_index: int, seed_index: int, episode: int) -> int:
    return 610000 + 10000 * controller_index + 1000 * seed_index + episode


def nearest_action(turn: float, climb: float) -> np.ndarray:
    commands = np.zeros((3, 3), dtype=np.float32)
    commands[:, 0] = np.clip(turn, -1.0, 1.0)
    commands[:, 1] = np.clip(climb, -1.0, 1.0)
    commands[:, 2] = 1.0
    distance = ((ACTION3D_TABLE[None, :, :] - commands[:, None, :]) ** 2).sum(axis=-1)
    return np.argmin(distance, axis=1)


def structural_actions(env: UAVIntercept3DEnv) -> np.ndarray:
    rel = env.red_pos[0][None, :] - env.blue_pos
    desired = np.arctan2(rel[:, 1], rel[:, 0])
    turn = np.asarray([angle_diff(float(desired[i]), float(env.blue_heading[i])) / env.config.blue_types[i].max_turn_rate for i in range(env.num_agents)])
    horizontal = np.linalg.norm(rel[:, :2], axis=1) + 1e-6
    desired_gamma = np.arctan2(rel[:, 2], horizontal)
    climb = np.asarray([(desired_gamma[i] - env.blue_gamma[i]) / env.config.blue_types[i].max_climb_rate for i in range(env.num_agents)])
    return nearest_action(turn, climb)


def legal_observation_actions(obs: np.ndarray) -> np.ndarray:
    """Use only per-agent legal observation fields 0..18; no environment state."""
    turn, climb = np.zeros(3), np.zeros(3)
    for i in range(obs.shape[0]):
        # Under the frozen bottleneck these relative fields are zero when the
        # agent has no target information. Neutral search is then deterministic.
        rel_x, rel_y, rel_z = float(obs[i, 8]), float(obs[i, 9]), float(obs[i, 10])
        if abs(rel_x) + abs(rel_y) + abs(rel_z) < 1e-8:
            continue
        current_heading = math.atan2(float(obs[i, 4]), float(obs[i, 5]))
        desired_heading = math.atan2(rel_y, rel_x)
        turn[i] = angle_diff(desired_heading, current_heading) / (0.035 if i == 0 else 0.030 if i == 1 else 0.052)
        desired_gamma = math.atan2(rel_z, math.hypot(rel_x, rel_y) + 1e-6)
        current_gamma = math.atan2(float(obs[i, 6]), float(obs[i, 7]))
        climb[i] = (desired_gamma - current_gamma) / (0.26 if i == 0 else 0.22 if i == 1 else 0.31)
    return nearest_action(turn, climb)


def controller_actions(controller: str, env: UAVIntercept3DEnv, obs: np.ndarray) -> np.ndarray:
    if controller == "structural_oracle":
        return structural_actions(env)
    if controller == "legal_observation":
        return legal_observation_actions(obs)
    raise ValueError(controller)


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)


def run_one(controller: str, controller_index: int, seed: int, seed_index: int, episode: int) -> tuple[dict, list[dict]]:
    env = UAVIntercept3DEnv(UAVIntercept3DConfig(seed=episode_id(controller_index, seed_index, episode), target_policy="straight",
        communication_range_scale=1.0, communication_dropout_prob=.30, message_delay_steps=2, radar_dropout_prob=0.0,
        strict_target_sensing=True, agent_target_info_bottleneck=True, failed_blue_agent=-1, node_failure_duration_steps=0,
        max_steps=260, attack_hold_steps=4))
    obs, _, _ = env.reset(); trace=[]; hold=0; trigger=-1
    while True:
        actions = controller_actions(controller, env, obs)
        obs, _, _, _, dones, info = env.step(actions)
        chain = float(info["chain_closed"]) > .5
        hold = hold + 1 if chain else 0
        if trigger < 0 and hold >= 4 and int(info["step"]) <= 220: trigger=int(info["step"])
        trace.append({"development_episode_id": episode_id(controller_index, seed_index, episode), "controller": controller,
                      "seed": seed, "timestep": int(info["step"]), "chain_closed": float(chain), "hold": hold,
                      "tracking_rate": info["tracking_rate"], "comm_connectivity": info["comm_connectivity"],
                      "attacker_info_attack_window": info["attacker_info_attack_window"], "terminal": float(np.all(dones))})
        if np.all(dones): break
    return {"development_episode_id": episode_id(controller_index, seed_index, episode), "controller": controller, "seed": seed,
            "episode": episode, "feasible_before_cap": float(trigger >= 0), "first_four_step_chain": trigger,
            "censor_time": int(info["step"]), "success": info["success"], "timeout": info["timeout"],
            "controller_information_class": "ORACLE_STRUCTURAL" if controller_index == 0 else "LEGAL_OBSERVATION_ONLY"}, trace


def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument('--out-dir',type=Path,default=OUT); p.add_argument('--episodes',type=int,default=100); p.add_argument('--execute',action='store_true'); args=p.parse_args()
    if not args.execute: raise SystemExit('NO-GO: requires --execute after committed Phase2IA6 launch record')
    raw=args.out_dir/'raw_episode_metrics.csv'
    if raw.exists() or (args.out_dir/'raw_timestep_chain').exists(): raise FileExistsError('Refusing to overwrite Phase2IA6 output')
    rows=[]
    for ci,controller in enumerate(CONTROLLERS):
        for si,seed in enumerate(SEEDS):
            trace=[]
            for ep in range(args.episodes):
                row, episode_trace=run_one(controller,ci,seed,si,ep); rows.append(row); trace.extend(episode_trace)
            write_csv(args.out_dir/'raw_timestep_chain'/f'{controller}_seed{seed}.csv',trace)
    write_csv(raw,rows)
    (args.out_dir/'manifest.json').write_text(json.dumps({'artifact_class':'DEVELOPMENT_ONLY_TASK_FEASIBILITY','protocol':'PHASE2IA6-TF-V1','episodes':len(rows),'canonical_data_used':False},indent=2)+'\n')
    print(json.dumps({'status':'COMPLETE','episodes':len(rows)},indent=2))

if __name__=='__main__': main()
