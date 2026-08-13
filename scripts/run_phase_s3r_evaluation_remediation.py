"""Read-only S3-R shared-tape evaluation and learnability diagnosis.

This script never trains, saves checkpoints, or overwrites S3 evidence.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from envs.uav_intercept_3d_env import ACTION3D_TABLE, UAVIntercept3DConfig, UAVIntercept3DEnv  # noqa: E402

PROTOCOL = "PHASE-S3-R-V1"
METHODS = ("mappo", "matched_single_graph", "full")
SEEDS = (1501, 1502, 1503)
TAPE_START = 340000
DEFAULT_EPISODES = 100


def load_s3_module():
    spec = importlib.util.spec_from_file_location("phase_s3_runner", ROOT / "scripts" / "run_phase_s3_development_smoke.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load S3 runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


S3 = load_s3_module()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def env_for(episode_id: int, failure_on: bool) -> UAVIntercept3DEnv:
    """Use end-of-horizon success so no episode can terminate early from success."""
    return UAVIntercept3DEnv(UAVIntercept3DConfig(
        seed=episode_id, target_policy="straight", strict_target_sensing=True,
        agent_target_info_bottleneck=True, relay_dependent_task=True,
        business_grounded_geometry=True, communication_range_scale=1.0,
        communication_dropout_prob=0.0, message_delay_steps=0,
        radar_dropout_prob=0.0, max_steps=260, min_success_step=260,
        failed_blue_agent=1 if failure_on else -1,
        node_failure_start_step=44 if failure_on else 0,
        node_failure_duration_steps=80 if failure_on else 0,
    ))


def evaluate_episode(agent, method: str, train_seed: int, episode_id: int, condition: str) -> dict:
    env = env_for(episode_id, condition == "relay_failure")
    obs, share, graph = env.reset()
    reward_sum = distance = control_effort = 0.0
    path_switches = 0
    previous_path = None
    failure_steps = 0
    direct_active_steps = 0
    relay_active_steps = 0
    legal_info_steps = 0
    task_support_steps = 0
    cache_ages = []
    previous_pos = env.blue_pos.copy()
    while True:
        actions = S3.policy_action(agent, obs, share, graph)
        control_effort += float(np.abs(ACTION3D_TABLE[actions, :2]).sum())
        obs, share, graph, rewards, dones, info = env.step(actions)
        reward_sum += float(np.sum(rewards))
        distance += float(np.linalg.norm(env.blue_pos - previous_pos, axis=1).sum())
        previous_pos = env.blue_pos.copy()
        path = str(info.get("attacker_cache_paths_t", ""))
        path_switches += int(previous_path is not None and path != previous_path)
        previous_path = path
        active = bool(info.get("node_failure_active", 0.0) > 0.5)
        failure_steps += int(active)
        if active:
            direct_active_steps += int(path == "0-2")
            relay_active_steps += int(path == "0-1-2")
            legal_info_steps += int(info.get("attacker_legal_target_information_t", 0.0) > 0.5)
            task_support_steps += int(info.get("chain_support_t", 0.0) > 0.5)
            cache_ages.append(float(info.get("target_cache_age_mean", 0.0)))
        if np.all(dones):
            break
    denom = max(1, failure_steps)
    return {
        "protocol": PROTOCOL, "development_episode_id": episode_id,
        "method": method, "train_seed": train_seed, "condition": condition,
        "J": reward_sum, "success_at_horizon": float(info["success"]),
        "collision": float(info["collision"]), "timeout": float(info["timeout"]),
        "constraint_violation": float(info["constraint_violation"]),
        "terminal_step": int(info["step"]), "failure_exposed": int(failure_steps > 0),
        "failure_active_steps": failure_steps,
        "direct_path_fraction_during_failure": direct_active_steps / denom,
        "relay_path_fraction_during_failure": relay_active_steps / denom,
        "legal_information_fraction_during_failure": legal_info_steps / denom,
        "task_support_fraction_during_failure": task_support_steps / denom,
        "mean_cache_age_during_failure": float(np.mean(cache_ages)) if cache_ages else math.nan,
        "path_switch_count": path_switches, "traveled_distance": distance,
        "control_effort": control_effort,
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def learning_summary(log_path: Path) -> dict:
    with log_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    rewards = np.asarray([float(row["train_avg_reward"]) for row in rows], dtype=float)
    window = min(100, len(rewards))
    x = np.arange(window, dtype=float)
    slope = float(np.polyfit(x, rewards[-window:], 1)[0]) if window >= 2 else math.nan
    final = rows[-1]
    return {
        "updates_logged": len(rows), "early_reward_mean": float(np.mean(rewards[:window])),
        "middle_reward_mean": float(np.mean(rewards[max(0, len(rewards)//2-window//2):len(rewards)//2+window//2])),
        "final_reward_mean": float(np.mean(rewards[-window:])), "final_reward_slope": slope,
        "final_loss": float(final["loss"]), "final_approx_kl": float(final["approx_kl"]),
        "final_grad_norm": float(final["grad_norm"]),
        "final_explained_variance": float(final["explained_variance"]),
        "finite_final_diagnostics": bool(all(np.isfinite(float(final[key])) for key in ("loss", "approx_kl", "grad_norm", "explained_variance"))),
    }


def paired_rows(rows: list[dict]) -> list[dict]:
    nominal = {row["development_episode_id"]: row for row in rows if row["condition"] == "nominal"}
    output = []
    for failure in (row for row in rows if row["condition"] == "relay_failure"):
        base = nominal[failure["development_episode_id"]]
        output.append({
            "protocol": PROTOCOL, "development_episode_id": failure["development_episode_id"],
            "method": failure["method"], "train_seed": failure["train_seed"],
            "J_nominal": base["J"], "J_failure": failure["J"],
            "delta_J": base["J"] - failure["J"],
            "success_nominal": base["success_at_horizon"],
            "success_failure": failure["success_at_horizon"],
            "failure_exposed": failure["failure_exposed"],
        })
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="S3-R read-only shared-tape remediation")
    parser.add_argument("--input-root", type=Path, default=ROOT / "archival" / "provenance" / "phase_s3_cloud_a4f2076" / "results" / "development" / "phase_s3_three_method_smoke" / "runs")
    parser.add_argument("--output-root", type=Path, default=ROOT / "results" / "development" / "phase_s3r_evaluation_remediation")
    parser.add_argument("--episodes", type=int, default=DEFAULT_EPISODES)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: read-only evaluation requires explicit --execute")
    if args.output_root.exists():
        raise FileExistsError("Refusing to overwrite existing S3-R output")

    all_episode_rows, all_paired_rows, diagnostics = [], [], []
    deterministic_probe = None
    for method in METHODS:
        spec = S3.METHODS[method]
        for seed in SEEDS:
            run_dir = args.input_root / method / f"seed{seed}"
            manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
            checkpoint = run_dir / "actor_critic_latest.pt"
            if sha256(checkpoint) != manifest["checkpoint_sha256"]:
                raise RuntimeError("checkpoint SHA256 mismatch: {}".format(run_dir))
            agent = S3.agent_for_checkpoint(spec, checkpoint, seed)
            rows = []
            for episode in range(args.episodes):
                episode_id = TAPE_START + episode
                rows.append(evaluate_episode(agent, method, seed, episode_id, "nominal"))
                rows.append(evaluate_episode(agent, method, seed, episode_id, "relay_failure"))
            if deterministic_probe is None:
                repeat = evaluate_episode(agent, method, seed, TAPE_START, "relay_failure")
                deterministic_probe = all(rows[1][key] == repeat[key] for key in ("J", "success_at_horizon", "terminal_step", "failure_exposed", "path_switch_count"))
            paired = paired_rows(rows)
            all_episode_rows.extend(rows); all_paired_rows.extend(paired)
            diag = {"method": method, "train_seed": seed, "checkpoint_sha256": manifest["checkpoint_sha256"], **learning_summary(run_dir / "train_log.csv")}
            diagnostics.append(diag)

    ids = {row["development_episode_id"] for row in all_episode_rows}
    integrity = {
        "checkpoint_hashes_match": True,
        "shared_tape_exact": ids == set(range(TAPE_START, TAPE_START + args.episodes)),
        "nominal_failure_pairing_complete": len(all_paired_rows) == len(METHODS) * len(SEEDS) * args.episodes,
        "failure_exposure_all": all(row["failure_exposed"] == 1 for row in all_paired_rows),
        "deterministic_replay": bool(deterministic_probe),
        "training_started": False,
    }
    args.output_root.mkdir(parents=True)
    write_csv(args.output_root / "raw_episode_metrics.csv", all_episode_rows)
    write_csv(args.output_root / "paired_metrics.csv", all_paired_rows)
    write_csv(args.output_root / "learning_curve_diagnostics.csv", diagnostics)
    summary = []
    for method in METHODS:
        for seed in SEEDS:
            cell = [row for row in all_paired_rows if row["method"] == method and row["train_seed"] == seed]
            summary.append({"method": method, "train_seed": seed, "episodes": len(cell),
                            "J_nominal_mean": float(np.mean([row["J_nominal"] for row in cell])),
                            "J_failure_mean": float(np.mean([row["J_failure"] for row in cell])),
                            "delta_J_mean": float(np.mean([row["delta_J"] for row in cell])),
                            "success_nominal_mean": float(np.mean([row["success_nominal"] for row in cell])),
                            "success_failure_mean": float(np.mean([row["success_failure"] for row in cell]))})
    write_csv(args.output_root / "per_seed_summary.csv", summary)
    (args.output_root / "manifest.json").write_text(json.dumps({"protocol": PROTOCOL, "input_root": str(args.input_root), "tape_start": TAPE_START, "episodes": args.episodes, "success_metric": "success_at_horizon_min_success_step_260", "integrity": integrity, "training_started": False}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"integrity": integrity, "output_root": str(args.output_root)}, indent=2))
    if not all(value for key, value in integrity.items() if key != "training_started"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
