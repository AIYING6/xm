"""Read-only TLI0 diagnostic for the L0 PPO/heuristic gap."""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import make_env  # noqa: E402
from scripts.run_new_project_n2_development_pilot import agent_actions, load_agent  # noqa: E402
from envs.uav_intercept_3d_env import GUIDANCE_FLIGHT_ACTION_DIM, GUIDANCE_ACTION_TABLE  # noqa: E402
from scripts.run_new_project_l0_single_interceptor import heuristic_action, l0_cfg  # noqa: E402


SEEDS = tuple(range(820000, 820008))


def angle_diff(a: float, b: float) -> float:
    return (a - b + math.pi) % (2 * math.pi) - math.pi


def state_metrics(env) -> dict[str, float]:
    rel = env.red_pos[0] - env.blue_pos[0]
    los = math.atan2(float(rel[1]), float(rel[0]))
    heading_err = abs(angle_diff(los, float(env.blue_heading[0])))
    blue_vel = env.blue_speed[0] * np.asarray([math.cos(env.blue_heading[0]), math.sin(env.blue_heading[0]), math.tan(env.blue_gamma[0])], dtype=np.float32)
    red_vel = env.red_speed[0] * np.asarray([math.cos(env.red_heading[0]), math.sin(env.red_heading[0]), math.tan(env.red_gamma[0])], dtype=np.float32)
    closure = float(np.dot(blue_vel - red_vel, rel / max(float(np.linalg.norm(rel)), 1e-6)))
    return {"range": float(np.linalg.norm(rel)), "heading_error": heading_err, "altitude_error": abs(float(rel[2])), "closing_speed": closure, "geometry": float(env._in_true_standoff_envelope(0, env.config.blue_types[0]))}


def trajectory(cfg, seed: int, mode: str, agent=None, limit: int = 180) -> list[dict]:
    env = make_env(cfg, seed, training=False)
    obs, share, graph = env.reset()
    rows = []
    for step in range(limit):
        before = state_metrics(env)
        action = heuristic_action(obs) if mode == "heuristic" else agent_actions(agent, obs, share, graph)
        obs, share, graph, reward, dones, _info = env.step(action)
        after = state_metrics(env)
        rows.append({"step": step, "action": int(action[0]), "reward": float(reward[0, 0]), **{f"before_{k}": v for k, v in before.items()}, **{f"after_{k}": v for k, v in after.items()}})
        if bool(np.all(dones)): break
    return rows


def observation_stats(cfg) -> dict:
    env = make_env(cfg, SEEDS[0], training=False)
    obs, _share, _graph = env.reset()
    rows = [obs[0]]
    for _ in range(32):
        action = heuristic_action(obs)
        obs, _share, _graph, _reward, dones, _info = env.step(action)
        rows.append(obs[0])
        if bool(np.all(dones)): break
    arr = np.asarray(rows)
    return {"dimensions": int(arr.shape[1]), "min": arr.min(axis=0).round(6).tolist(), "max": arr.max(axis=0).round(6).tolist(), "mean_abs": np.mean(np.abs(arr), axis=0).round(6).tolist(), "field_names": list(getattr(__import__("envs.uav_intercept_3d_env", fromlist=["OBS3D_FIELD_NAMES"]), "OBS3D_FIELD_NAMES"))}


def action_and_reward_diagnostic(cfg, agent) -> dict:
    env = make_env(cfg, SEEDS[0], training=False)
    obs, share, graph = env.reset()
    heuristic_ids = []
    ppo_ids = []
    progress = []
    potential = []
    for _ in range(80):
        h = int(heuristic_action(obs)[0]); p = int(agent_actions(agent, obs, share, graph)[0])
        heuristic_ids.append(h % GUIDANCE_FLIGHT_ACTION_DIM); ppo_ids.append(p % GUIDANCE_FLIGHT_ACTION_DIM)
        before_phi = float(env._mission_progress_potential()); before_range = float(np.linalg.norm(env.red_pos[0] - env.blue_pos[0]))
        obs, share, graph, reward, dones, _info = env.step(np.asarray([h], dtype=np.int64))
        progress.append(before_range - float(np.linalg.norm(env.red_pos[0] - env.blue_pos[0])))
        potential.append(float(env._mission_progress_potential()) - before_phi)
        if bool(np.all(dones)): break
    return {"heuristic_unique_guidance_actions": sorted(set(heuristic_ids)), "ppo_unique_guidance_actions": sorted(set(ppo_ids)), "heuristic_action_histogram": {str(i): heuristic_ids.count(i) for i in sorted(set(heuristic_ids))}, "initial_action_disagreement_rate": float(np.mean(np.asarray(heuristic_ids) != np.asarray(ppo_ids))), "range_progress_potential_corr": float(np.corrcoef(progress, potential)[0, 1]) if np.std(progress) > 1e-9 and np.std(potential) > 1e-9 else 0.0, "mean_range_progress": float(np.mean(progress)), "mean_potential_delta": float(np.mean(potential))}


def timescale(cfg) -> list[dict]:
    result = []
    for repeat in (1, 2, 4, 8):
        env = make_env(cfg, SEEDS[0], training=False); env.reset(); start = env.blue_pos.copy(); start_heading = float(env.blue_heading[0]); start_speed = float(env.blue_speed[0]); action = np.asarray([GUIDANCE_FLIGHT_ACTION_DIM // 2], dtype=np.int64)
        for _ in range(repeat): env.step(action)
        result.append({"action_repeat": repeat, "displacement": float(np.linalg.norm(env.blue_pos[0] - start[0])), "heading_change": abs(float(env.blue_heading[0] - start_heading)), "speed_change": float(env.blue_speed[0] - start_speed)})
    return result


def main() -> None:
    output = ROOT / "results" / "tli0_l0_learning_interface_diagnostic_v2"
    if output.exists() and any(output.iterdir()): raise FileExistsError(output)
    output.mkdir(parents=True, exist_ok=True)
    cfg = l0_cfg(8101, output / "template", updates=1)
    checkpoint = ROOT / "results/new_project_l0_single_interceptor_v2/vanilla_mappo_l0_seed8101/actor_critic_latest.pt"
    agent = load_agent(cfg, checkpoint)
    traj_rows = []
    for seed in SEEDS:
        h = trajectory(cfg, seed, "heuristic")
        p = trajectory(cfg, seed, "ppo", agent)
        for i in range(min(len(h), len(p))):
            traj_rows.append({"seed": seed, "step": i, "heuristic_action": h[i]["action"], "ppo_action": p[i]["action"], "heuristic_range": h[i]["after_range"], "ppo_range": p[i]["after_range"], "heuristic_heading_error": h[i]["after_heading_error"], "ppo_heading_error": p[i]["after_heading_error"], "heuristic_closing_speed": h[i]["after_closing_speed"], "ppo_closing_speed": p[i]["after_closing_speed"], "heuristic_geometry": h[i]["after_geometry"], "ppo_geometry": p[i]["after_geometry"]})
    with (output / "aligned_trajectories.csv").open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(traj_rows[0])); writer.writeheader(); writer.writerows(traj_rows)
    diagnostics = {"observation": observation_stats(cfg), "action_reward": action_and_reward_diagnostic(cfg, agent), "timescale": timescale(cfg), "checkpoint": str(checkpoint), "source_commit": __import__("subprocess").check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(), "performance_use_prohibited": True, "no_training": True}
    (output / "TLI0_DIAGNOSTIC.json").write_text(json.dumps(diagnostics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(diagnostics, indent=2), flush=True)


if __name__ == "__main__": main()
