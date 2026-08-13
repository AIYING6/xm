"""S1 paired nominal/failure robustness validation; no MARL training."""
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
SEEDS = (1401, 1402, 1403)
CONDITIONS = ("nominal", "relay_failure")
OUT = ROOT / "results" / "development" / "phase_s1_paired_robustness"


def eid(ci: int, si: int, ep: int) -> int:
    return 241000 + 10000 * ci + 1000 * si + ep


def set_business_geometry(env: UAVIntercept3DEnv) -> None:
    env.blue_pos[:] = np.asarray([[-2_000.0, -6_000.0, 5_000.0], [-2_000.0, 0.0, 5_000.0], [-2_000.0, 6_000.0, 5_000.0]], dtype=np.float32)
    env.blue_heading[:] = 0.0
    env.blue_gamma[:] = 0.0
    env.blue_speed[:] = np.asarray([185.0, 175.0, 205.0], dtype=np.float32)
    env._update_sensing_and_comm()


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
    commands = np.zeros((3, 3), dtype=np.float32); commands[:, 0] = np.clip(turn, -1.0, 1.0); commands[:, 1] = np.clip(climb, -1.0, 1.0); commands[:, 2] = 1.0
    return np.argmin(((ACTION3D_TABLE[None, :, :] - commands[:, None, :]) ** 2).sum(axis=-1), axis=1)


def mission_position_actions(env: UAVIntercept3DEnv, base: np.ndarray) -> np.ndarray:
    actions = np.asarray(base, dtype=np.int64).copy(); midpoint = .5 * (env.blue_pos[0] + env.blue_pos[2]); rel = midpoint - env.blue_pos[1]
    desired = math.atan2(float(rel[1]), float(rel[0])); turn = angle_diff(desired, float(env.blue_heading[1])) / env.config.blue_types[1].max_turn_rate
    gamma = math.atan2(float(rel[2]), float(np.linalg.norm(rel[:2]) + 1e-6)); climb = (gamma - float(env.blue_gamma[1])) / env.config.blue_types[1].max_climb_rate
    actions[1] = nearest_action(np.asarray([turn, 0.0, 0.0]), np.asarray([climb, 0.0, 0.0]))[0]
    return actions


def run_one(controller: str, condition: str, ci: int, seed: int, si: int, episode: int, action_tape: list[np.ndarray] | None = None) -> tuple[dict, list[dict], list[np.ndarray]]:
    episode_id = eid(ci, si, episode)
    env = UAVIntercept3DEnv(UAVIntercept3DConfig(seed=episode_id, target_policy="straight", communication_dropout_prob=0.0, message_delay_steps=0, radar_dropout_prob=0.0, strict_target_sensing=True, agent_target_info_bottleneck=True, relay_dependent_task=True, min_success_step=1000, failed_blue_agent=-1, node_failure_duration_steps=0, max_steps=260))
    env.reset(); set_business_geometry(env); obs, _, _ = env._get_obs(), env._get_share_obs(), env._get_graph_obs()
    if condition == "relay_failure":
        env.config.failed_blue_agent = 1; env.config.node_failure_start_step = 44; env.config.node_failure_duration_steps = 80
    trace = []; actions_out: list[np.ndarray] = []; info_values = []
    max_steps = 260 if action_tape is None else len(action_tape)
    for step_index in range(max_steps):
        if action_tape is None:
            base = controller_actions(controller, env, obs); actions = mission_position_actions(env, base)
            actions_out.append(np.asarray(actions, dtype=np.int64).copy())
        else:
            actions = action_tape[step_index]
        obs, _, _, rewards, dones, info = env.step(actions)
        legal = float(info["attacker_legal_target_information_t"]) > .5
        chain = float(info["chain_support_t"]) > .5
        age = float(info["target_cache_age_mean"])
        trace.append({"development_episode_id": episode_id, "controller": controller, "seed": seed, "condition": condition, "timestep": int(info["step"]), "relay_failure_active": int(info["node_failure_active"] > .5), "attacker_legal_information": int(legal), "chain_support": int(chain), "target_cache_age_mean": age, "attacker_cache_path": info["attacker_cache_paths_t"], "attacker_direct_target_information": info["attacker_direct_target_information_t"], "scout_relay_comm": int(env.comm_adj[1, 0] > .5), "relay_attacker_comm": int(env.comm_adj[2, 1] > .5), "scout_attacker_comm": int(env.comm_adj[2, 0] > .5), "reward_sum": float(np.sum(rewards)), "terminal": int(np.all(dones))})
        info_values.append(info)
        if np.all(dones):
            break
    valid = np.asarray([x["attacker_legal_information"] for x in trace], dtype=np.float64)
    chain = np.asarray([x["chain_support"] for x in trace], dtype=np.float64)
    ages = np.asarray([x["target_cache_age_mean"] for x in trace], dtype=np.float64)
    reward_sum = float(sum(x["reward_sum"] for x in trace))
    summary = {"development_episode_id": episode_id, "controller": controller, "seed": seed, "episode": episode, "condition": condition, "mission_score": reward_sum, "info_availability": float(valid.mean()), "task_chain_availability": float(chain.mean()), "mean_information_age": float(ages.mean()), "success": float(info_values[-1]["success"]), "collision": float(info_values[-1]["collision"]), "timeout": float(info_values[-1]["timeout"]), "failure_exposed": float(any(x["relay_failure_active"] for x in trace)), "direct_bypass_during_failure": float(any(x["relay_failure_active"] and x["scout_attacker_comm"] for x in trace))}
    return summary, trace, actions_out


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--out-dir", type=Path, default=OUT); p.add_argument("--episodes", type=int, default=100); p.add_argument("--execute", action="store_true"); a = p.parse_args()
    if not a.execute: raise SystemExit("NO-GO: requires --execute after committed S1 protocol")
    if a.episodes != 100: raise SystemExit("NO-GO: S1 fixes episodes=100")
    if (a.out_dir / "raw_episode_metrics.csv").exists(): raise FileExistsError("Refusing to overwrite")
    summaries = []; traces = []; cells = []
    for ci, controller in enumerate(CONTROLLERS):
        for si, seed in enumerate(SEEDS):
            nominal = []; failure = []; cell_trace = []
            for ep in range(a.episodes):
                n, nt, tape = run_one(controller, "nominal", ci, seed, si, ep); f, ft, _ = run_one(controller, "relay_failure", ci, seed, si, ep, tape)
                summaries.extend([n, f]); traces.extend([*nt, *ft]); nominal.append(n); failure.append(f); cell_trace.extend([*nt, *ft])
            n_score = float(np.mean([x["mission_score"] for x in nominal])); f_score = float(np.mean([x["mission_score"] for x in failure])); n_info = float(np.mean([x["info_availability"] for x in nominal])); f_info = float(np.mean([x["info_availability"] for x in failure])); n_age = float(np.mean([x["mean_information_age"] for x in nominal])); f_age = float(np.mean([x["mean_information_age"] for x in failure])); d_j = (n_score - f_score) / max(abs(n_score), 1e-6); d_i = n_info - f_info
            cells.append({"controller": controller, "seed": seed, "nominal_score": n_score, "failure_score": f_score, "D_J": d_j, "nominal_info": n_info, "failure_info": f_info, "D_I": d_i, "nominal_age": n_age, "failure_age": f_age, "failure_exposure_rate": float(np.mean([x["failure_exposed"] for x in failure])), "dynamic_range_pass": int(0.01 < max(d_j, d_i) < 0.99), "cell_pass": int(d_j > 0 or d_i > 0)})
            write_csv(a.out_dir / "raw_timestep" / f"{controller}_seed{seed}.csv", cell_trace)
    a.out_dir.mkdir(parents=True, exist_ok=True); write_csv(a.out_dir / "raw_episode_metrics.csv", summaries); write_csv(a.out_dir / "cell_summary.csv", cells)
    passed = all(bool(x["cell_pass"]) and bool(x["failure_exposure_rate"] > .99) for x in cells); manifest = {"protocol": "PHASE-S1-RV-V1", "artifact_class": "DEVELOPMENT_ONLY_PAIRED_ROBUSTNESS_VALIDATION", "controllers": list(CONTROLLERS), "seeds": list(SEEDS), "episodes_per_cell": a.episodes, "canonical_data_used": False, "training_started": False, "status": "PASS" if passed else "INFEASIBLE"}
    (a.out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8"); print(json.dumps(manifest, indent=2))
    if not passed: raise SystemExit(2)


if __name__ == "__main__": main()
