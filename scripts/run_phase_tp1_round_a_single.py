"""Run one frozen TP-1 SG or CTP curriculum cell."""
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
from algorithms.ri_gmappo.topology_curriculum import schedule_hash  # noqa: E402
from run_phase_rsg1_development_smoke import build_agent, evaluate_episode, write_csv  # noqa: E402


PROTOCOL = "PHASE-TP-1-ROUND-A-V1"
SEEDS = (1601, 1602)
TAPE_START = 350000
EPISODES = 50
UPDATES = 1172
NUM_ENVS = 4
ROLLOUT_STEPS = 64
ARMS = {
    "sg": {"graph_encoder": "single", "hidden_dim": 115, "schedule": "none"},
    "ctp_a": {"graph_encoder": "single", "hidden_dim": 115, "schedule": "A"},
    "ctp_c": {"graph_encoder": "single", "hidden_dim": 115, "schedule": "C"},
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
        hidden_dim=spec["hidden_dim"], role_dim=8, intent_dim=8,
        graph_encoder=spec["graph_encoder"], role_gate_mode="none",
        target_policy="straight", strict_target_sensing=True,
        agent_target_info_bottleneck=True, relay_dependent_task=True,
        business_grounded_geometry=True, communication_range_scale=1.0,
        communication_dropout_prob=0.0, message_delay_steps=0,
        radar_dropout_prob=0.0, min_success_step=260,
        failed_blue_agent=1, node_failure_start_step=44,
        node_failure_duration_steps=80, evaluation_enabled=False,
        target_kl=None, save_interval=UPDATES, save_snapshots=False,
        out_dir=str(out_dir), device="cuda" if torch.cuda.is_available() else "cpu",
        topology_curriculum_schedule=spec["schedule"],
        topology_curriculum_seed=seed,
        topology_curriculum_logging=arm in {"ctp_a", "ctp_c"},
    )


def frozen_eval_env(seed: int, failure: bool):
    from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv
    return UAVIntercept3DEnv(UAVIntercept3DConfig(
        seed=seed, target_policy="straight", strict_target_sensing=True,
        agent_target_info_bottleneck=True, relay_dependent_task=True,
        business_grounded_geometry=True, communication_range_scale=1.0,
        communication_dropout_prob=0.0, message_delay_steps=0,
        radar_dropout_prob=0.0, max_steps=260, min_success_step=260,
        failed_blue_agent=1 if failure else -1,
        node_failure_start_step=44 if failure else 0,
        node_failure_duration_steps=80 if failure else 0,
    ))


def evaluate(agent, arm: str, seed: int, out_dir: Path) -> None:
    import run_phase_rsg1_development_smoke as evaluator
    original = evaluator.frozen_env
    evaluator.frozen_env = frozen_eval_env
    try:
        raw, bias = [], []
        method_label = "matched_single_graph" if arm == "sg" else arm
        for episode in range(EPISODES):
            episode_id = TAPE_START + episode
            for condition in ("nominal", "relay_failure"):
                row, bias_rows = evaluate_episode(agent, method_label, seed, episode_id, condition)
                raw.append(row)
                bias.extend(bias_rows)
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
            "protocol": PROTOCOL, "development_episode_id": row["development_episode_id"],
            "arm": arm, "train_seed": seed,
            "J_nominal": nrow["J"], "J_failure": row["J"],
            "delta_J": float(nrow["J"]) - float(row["J"]),
            "collision_nominal": nrow["collision"], "collision_failure": row["collision"],
            "timeout_nominal": nrow["timeout"], "timeout_failure": row["timeout"],
            "constraint_nominal": nrow["constraint_violation"], "constraint_failure": row["constraint_violation"],
            "failure_exposed": row["failure_exposed"],
        })
    write_csv(out_dir / "paired_metrics.csv", paired)
    write_csv(out_dir / "bias_telemetry.csv", bias)


def run_one(arm: str, seed: int, output_root: Path) -> dict:
    spec = ARMS[arm]
    out_dir = output_root / "runs" / arm / f"seed{seed}"
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=False)
    cfg = training_config(arm, seed, out_dir)
    manifest = {
        "protocol": PROTOCOL, "status": "running", "arm": arm, "seed": seed,
        "schedule": spec["schedule"],
        "schedule_hash": schedule_hash(spec["schedule"]) if spec["schedule"] != "none" else None,
        "graph_encoder": spec["graph_encoder"], "hidden_dim": spec["hidden_dim"],
        "environment_steps": UPDATES * NUM_ENVS * ROLLOUT_STEPS,
        "updates": UPDATES, "num_envs": NUM_ENVS, "rollout_steps": ROLLOUT_STEPS,
        "checkpoint_selection": "fixed_final_update_only", "resume": False,
        "early_stopping": False, "checkpoint_promotion": False,
        "canonical_seeds_used": False, "tuning_tape_start": TAPE_START,
        "tuning_episodes_per_condition": EPISODES, "config": cfg.__dict__,
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
    parser.add_argument("--seed", type=int, choices=SEEDS, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("results/phase_tp1_round_a"))
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: TP-1 requires explicit --execute")
    run_one(args.arm, args.seed, args.output_root)


if __name__ == "__main__":
    main()
