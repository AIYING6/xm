"""L0 single-interceptor learnability development protocol."""

from __future__ import annotations

import csv
import json
import math
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import (  # noqa: E402
    make_env,
    RIGMAPPOConfig,
    train_ri_gmappo,
)
from scripts.run_new_project_n2_development_pilot import agent_actions, load_agent  # noqa: E402
from envs.uav_intercept_3d_env import (  # noqa: E402
    ACTION3D_TABLE,
    GUIDANCE_ACTION_TABLE,
    GUIDANCE_FLIGHT_ACTION_DIM,
    ROLE_ATTACKER,
    UAV3DType,
)
from scripts.calibrate_new_project_n1_mission_timing import scripted_oracle_actions  # noqa: E402


TRAIN_SEEDS = (8101, 8102)
EVAL_SEEDS = tuple(range(820000, 820032))
UPDATES = 60
RMTN_HORIZON = 180
PROTOCOL_VERSION = "NEW_PROJECT_L0_SINGLE_INTERCEPTOR_V2_REACHABILITY_CORRECTED"


def source_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNAVAILABLE"


def l0_cfg(seed: int, out_dir: Path, updates: int = UPDATES) -> RIGMAPPOConfig:
    default = UAV3DType(ROLE_ATTACKER, 270.0, 135.0, 22.0, 0.052, 50.0, 0.31, 7.0, 11_000.0, math.radians(95), math.radians(42), 8_500.0, 1_400.0, 5_200.0, math.radians(50), 1.15)
    return RIGMAPPOConfig(
        env_name="3d_intercept", seed=seed, num_blue=1, blue_types=[default], num_envs=4,
        rollout_steps=128, updates=updates, hidden_dim=128, role_dim=8, intent_dim=8,
        graph_encoder="no_graph", graph_relation_ablation="none", graph_message_ablation="none",
        graph_input_ablation="none", lr=3e-4, entropy_coef=0.01, intent_coef=0.0,
        chain_aux_coef=0.0, role_gate_prior_strength=0.0, multi_relation_global_residual_weight=0.0,
        ppo_epochs=4, minibatch_graphs=256, eval_interval=1000, eval_episodes=1,
        target_policy="straight", communication_dropout_prob=0.0, message_delay_steps=0,
        radar_dropout_prob=0.0, strict_target_sensing=True, agent_target_info_bottleneck=False,
        mission_neutralization_enabled=True, guidance_level_action_interface=True,
        engage_commit_hold_steps=4, mission_progress_shaping_enabled=False,
        target_escape_radius=35_000.0, mission_max_steps=360, failed_blue_agent=-1,
        node_failure_random_prob=0.0, node_failure_start_step=0, node_failure_duration_steps=0,
        attack_geometry_reward_weight=0.0, post_loss_chain_reclosure_reward_weight=0.0,
        device="cpu", out_dir=str(out_dir), save_interval=updates, save_snapshots=False,
        validation_event_logging=False, run_id=f"l0_single_interceptor_seed{seed}",
        method_label="l0_single_interceptor_vanilla_mappo", protocol_version=PROTOCOL_VERSION,
    )


def guidance_id(turn: float, climb: float) -> int:
    return int(np.argmin(np.linalg.norm(GUIDANCE_ACTION_TABLE - np.asarray((turn, climb), dtype=np.float32)[None, :], axis=1)))


def heuristic_action(obs: np.ndarray) -> np.ndarray:
    row = obs[0]
    rel = row[8:11]
    desired = math.atan2(float(rel[1]), float(rel[0]))
    own = math.atan2(float(row[4]), float(row[5]))
    heading_error = (desired - own + math.pi) % (2 * math.pi) - math.pi
    own_gamma = math.atan2(float(row[6]), float(row[7]))
    desired_gamma = math.atan2(float(rel[2]), float(np.linalg.norm(rel[:2])) + 1e-6)
    turn = 1.0 if heading_error > 0.10 else (-1.0 if heading_error < -0.10 else 0.0)
    climb = 1.0 if desired_gamma - own_gamma > 0.08 else (-1.0 if desired_gamma - own_gamma < -0.08 else 0.0)
    range_norm = float(row[11])
    commit = 1_400 / 50_000 <= range_norm <= 5_200 / 50_000 and abs(float(rel[2])) <= 1_600 / 8_000 and math.cos(heading_error) >= 0.90
    return np.asarray([guidance_id(turn, climb) + (GUIDANCE_FLIGHT_ACTION_DIM if commit else 0)], dtype=np.int64)


def convert_oracle_action(action: int) -> int:
    flight = ACTION3D_TABLE[int(action) % len(ACTION3D_TABLE)]
    result = guidance_id(float(flight[0]), float(flight[1]))
    return result + (GUIDANCE_FLIGHT_ACTION_DIM if int(action) >= len(ACTION3D_TABLE) else 0)


def outcome(info: dict) -> str:
    if info.get("collision", 0.0) > 0.5: return "COLLISION"
    if info.get("constraint_violation", 0.0) > 0.5: return "CONSTRAINT_FAILURE"
    if info.get("target_neutralized", 0.0) > 0.5: return "NEUTRALIZED"
    if info.get("target_escape", 0.0) > 0.5: return "TARGET_ESCAPE"
    return "TIMEOUT"


def episode(cfg, seed: int, mode: str, agent=None) -> dict:
    env = make_env(cfg, seed, training=False)
    obs, share, graph = env.reset()
    entry = False
    while True:
        if mode == "random":
            action = np.asarray([np.random.default_rng(seed + 33).integers(0, env.action_dim)], dtype=np.int64)
        elif mode == "scripted":
            action = heuristic_action(obs)
        elif mode == "oracle":
            action = np.asarray([convert_oracle_action(int(scripted_oracle_actions(env)[0]))], dtype=np.int64)
        else:
            action = agent_actions(agent, obs, share, graph)
        entry = entry or bool(env._in_true_standoff_envelope(0, env.config.blue_types[0]))
        obs, share, graph, _reward, dones, info = env.step(action)
        if bool(np.all(dones)):
            final = outcome(info)
            neutral = final == "NEUTRALIZED" and int(info["step"]) <= RMTN_HORIZON
            return {"mode": mode, "episode_seed": seed, "final_outcome": final, "geometry_entry": int(entry), "neutralized_by_180": int(neutral), "rmtn180": int(info["step"]) if neutral else RMTN_HORIZON}


def main() -> None:
    output = ROOT / "results" / "new_project_l0_single_interceptor_v2"
    if output.exists() and any(output.iterdir()): raise FileExistsError(output)
    output.mkdir(parents=True, exist_ok=True)
    template = l0_cfg(TRAIN_SEEDS[0], output / "template")
    (output / "L0_MANIFEST.json").write_text(json.dumps({"protocol_version": PROTOCOL_VERSION, "performance_use_prohibited": True, "source_commit": source_commit(), "training_seeds": list(TRAIN_SEEDS), "evaluation_seeds": list(EVAL_SEEDS), "updates": UPDATES, "config": asdict(template)}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    trained = []
    for seed in TRAIN_SEEDS:
        run = output / f"vanilla_mappo_l0_seed{seed}"; cfg = l0_cfg(seed, run); ckpt = run / "actor_critic_latest.pt"
        if not ckpt.exists(): train_ri_gmappo(cfg)
        trained.append((f"vanilla_mappo_l0_seed{seed}", cfg, load_agent(cfg, ckpt)))
    rows = []
    eval_cfg = l0_cfg(TRAIN_SEEDS[0], output / "template", updates=1)
    for seed in EVAL_SEEDS:
        for mode in ("random", "scripted", "oracle"):
            rows.append(episode(eval_cfg, seed, mode))
        for name, _cfg, agent in trained: rows.append({**episode(eval_cfg, seed, name, agent), "mode": name})
    with (output / "episode_outcomes.csv").open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    summary = []
    for mode in sorted({r["mode"] for r in rows}):
        group = [r for r in rows if r["mode"] == mode]
        summary.append({"mode": mode, "episodes": len(group), "geometry_entry_rate": float(np.mean([r["geometry_entry"] for r in group])), "neutralization_rate": float(np.mean([r["neutralized_by_180"] for r in group])), "rmtn180": float(np.mean([r["rmtn180"] for r in group]))})
    with (output / "summary.csv").open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0])); writer.writeheader(); writer.writerows(summary)
    learned = [r for r in summary if r["mode"].startswith("vanilla_mappo_l0")]
    pooled = float(np.mean([r["neutralization_rate"] for r in learned])); pooled_rmtn = float(np.mean([r["rmtn180"] for r in learned]))
    verdict = "L0_LEARNABILITY_PASS" if pooled > 0.0 and pooled_rmtn < 180.0 and pooled < 0.90 else "L0_NO_GO"
    (output / "L0_VERDICT.json").write_text(json.dumps({"verdict": verdict, "pooled_learned_neutralization_rate": pooled, "pooled_learned_rmtn180": pooled_rmtn, "summary": summary}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": verdict, "pooled_neutralization": pooled, "pooled_rmtn180": pooled_rmtn}, indent=2), flush=True)


if __name__ == "__main__": main()
