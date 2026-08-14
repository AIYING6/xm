"""Run one frozen Phase-FL expert and paired diagnostic evaluation."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOConfig, train_ri_gmappo  # noqa: E402
from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv  # noqa: E402
from run_phase_rsg1_development_smoke import build_agent, evaluate_episode, write_csv  # noqa: E402


PROTOCOL = "PHASE-FL-V1"
SEEDS = (1801, 1802)
TAPE_START = 370000
EPISODES = 50
UPDATES = 1172
NUM_ENVS = 4
ROLLOUT_STEPS = 64
ARMS = {
    "fl_nominal_expert": {"failed_blue_agent": -1, "failure_start": 0, "failure_duration": 0},
    "fl_f0_expert": {"failed_blue_agent": 1, "failure_start": 44, "failure_duration": 80},
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def training_config(arm: str, seed: int, out_dir: Path) -> RIGMAPPOConfig:
    spec = ARMS[arm]
    return RIGMAPPOConfig(
        env_name="3d_intercept", seed=seed, num_envs=NUM_ENVS,
        rollout_steps=ROLLOUT_STEPS, updates=UPDATES,
        hidden_dim=115, role_dim=8, intent_dim=8,
        graph_encoder="single", role_gate_mode="none",
        target_policy="straight", strict_target_sensing=True,
        agent_target_info_bottleneck=True, relay_dependent_task=True,
        business_grounded_geometry=True, communication_range_scale=1.0,
        communication_dropout_prob=0.0, message_delay_steps=0,
        radar_dropout_prob=0.0, min_success_step=260,
        failed_blue_agent=spec["failed_blue_agent"],
        node_failure_start_step=spec["failure_start"],
        node_failure_duration_steps=spec["failure_duration"],
        evaluation_enabled=False, target_kl=None, save_interval=UPDATES,
        save_snapshots=False, out_dir=str(out_dir),
        device="cuda" if torch.cuda.is_available() else "cpu",
        topology_curriculum_schedule="none", topology_curriculum_seed=seed,
        topology_curriculum_logging=False,
    )


def frozen_env(seed: int, failure_on: bool) -> UAVIntercept3DEnv:
    return UAVIntercept3DEnv(UAVIntercept3DConfig(
        seed=seed, target_policy="straight", strict_target_sensing=True,
        agent_target_info_bottleneck=True, relay_dependent_task=True,
        business_grounded_geometry=True, communication_range_scale=1.0,
        communication_dropout_prob=0.0, message_delay_steps=0,
        radar_dropout_prob=0.0, max_steps=260, min_success_step=260,
        failed_blue_agent=1 if failure_on else -1,
        node_failure_start_step=44 if failure_on else 0,
        node_failure_duration_steps=80 if failure_on else 0,
    ))


def evaluate(agent, arm: str, seed: int, out_dir: Path) -> None:
    import run_phase_rsg1_development_smoke as evaluator

    original = evaluator.frozen_env
    evaluator.frozen_env = frozen_env
    try:
        raw = []
        for episode in range(EPISODES):
            episode_id = TAPE_START + episode
            for condition in ("nominal", "relay_failure"):
                row, _ = evaluate_episode(agent, arm, seed, episode_id, condition)
                row["protocol"] = PROTOCOL
                row["fl_tape_id"] = episode_id
                raw.append(row)
    finally:
        evaluator.frozen_env = original
    write_csv(out_dir / "raw_episode_metrics.csv", raw)
    nominal = {int(row["development_episode_id"]): row for row in raw if row["condition"] == "nominal"}
    paired = []
    for row in raw:
        if row["condition"] != "relay_failure":
            continue
        nrow = nominal[int(row["development_episode_id"])]
        paired.append({
            "protocol": PROTOCOL, "fl_tape_id": row["development_episode_id"],
            "arm": arm, "train_seed": seed,
            "J_nominal": nrow["J"], "J_failure": row["J"],
            "delta_J": float(nrow["J"]) - float(row["J"]),
            "collision_nominal": nrow["collision"], "collision_failure": row["collision"],
            "timeout_nominal": nrow["timeout"], "timeout_failure": row["timeout"],
            "constraint_nominal": nrow["constraint_violation"],
            "constraint_failure": row["constraint_violation"],
            "failure_exposed": row["failure_exposed"],
            "episode_length_nominal": nrow["terminal_step"],
            "episode_length_failure": row["terminal_step"],
            "path_switch_count_nominal": nrow["path_switch_count"],
            "path_switch_count_failure": row["path_switch_count"],
            "direct_path_fraction_failure": row["direct_path_fraction_during_failure"],
            "relay_path_fraction_failure": row["relay_path_fraction_during_failure"],
            "task_support_fraction_failure": row["task_support_fraction_during_failure"],
            "legal_information_fraction_failure": row["legal_information_fraction_during_failure"],
            "mean_cache_age_failure": row["mean_cache_age_during_failure"],
            "traveled_distance_failure": row["traveled_distance"],
            "control_effort_failure": row["control_effort"],
        })
    write_csv(out_dir / "paired_metrics.csv", paired)


def run_one(arm: str, seed: int, output_root: Path) -> dict:
    out_dir = output_root / "runs" / arm / f"seed{seed}"
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite: {out_dir}")
    tape = json.loads((output_root / "tape_manifest.json").read_text(encoding="utf-8"))
    if tape["tape_hash"] == "" or tape["episode_ids"] != list(range(TAPE_START, TAPE_START + EPISODES)):
        raise RuntimeError("invalid FL tape manifest")
    out_dir.mkdir(parents=True, exist_ok=False)
    cfg = training_config(arm, seed, out_dir)
    spec = ARMS[arm]
    manifest = {
        "protocol": PROTOCOL, "status": "running", "arm": arm, "seed": seed,
        "training_condition": "nominal" if arm == "fl_nominal_expert" else "F0",
        "failure_spec": spec, "graph_encoder": "single", "hidden_dim": 115,
        "parameter_count": 116728, "environment_steps": UPDATES * NUM_ENVS * ROLLOUT_STEPS,
        "updates": UPDATES, "num_envs": NUM_ENVS, "rollout_steps": ROLLOUT_STEPS,
        "checkpoint_selection": "fixed_final_update_only", "resume": False,
        "early_stopping": False, "checkpoint_promotion": False,
        "canonical_seeds_used": False, "tape_start": TAPE_START,
        "tape_hash": tape["tape_hash"], "episodes_per_condition": EPISODES,
        "config": cfg.__dict__,
    }
    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    train_ri_gmappo(cfg)
    checkpoint = out_dir / "actor_critic_latest.pt"
    if not checkpoint.exists():
        raise FileNotFoundError(checkpoint)
    agent = build_agent({"graph_encoder": "single", "hidden_dim": 115}, checkpoint, seed)
    evaluate(agent, arm, seed, out_dir)
    manifest.update({"status": "completed", "checkpoint": str(checkpoint),
                     "checkpoint_sha256": sha256(checkpoint), "raw_rows": 100,
                     "paired_rows": 50})
    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"status": "completed", "arm": arm, "seed": seed,
                      "checkpoint_sha256": manifest["checkpoint_sha256"]}, indent=2))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=tuple(ARMS), required=True)
    parser.add_argument("--seed", choices=SEEDS, type=int, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("results/development/phase_fl_failure_learnability"))
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: Phase FL requires explicit --execute")
    run_one(args.arm, args.seed, args.output_root)


if __name__ == "__main__":
    main()
