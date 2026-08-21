"""Run one frozen EDR-D1 development trajectory from scratch exactly once."""
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
from scripts.create_t1_telemetry_native_tape import EPISODES, TAPE_START  # noqa: E402
from scripts.run_t1_telemetry_native_single import (  # noqa: E402
    ENVIRONMENT_STEPS, NUM_ENVS, ROLLOUT_STEPS, RUNTIME_SAVE_INTERVAL, SEEDS, UPDATES,
    config_hash,
)


PROTOCOL = "EDR-D1-FIVE-SEED-DEVELOPMENT-TRAINING-V1"
T1_TAPE_HASH = "3de6e4fabf07bb76fe7c9271b3f3e70a5910262581ac14b3de162533ef83e6c3"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def training_config(seed: int, out_dir: Path) -> RIGMAPPOConfig:
    """The T1 UTR contract with exactly one allowed change: encoder=EDR."""
    return RIGMAPPOConfig(
        env_name="3d_intercept", seed=seed, num_envs=NUM_ENVS, rollout_steps=ROLLOUT_STEPS,
        updates=UPDATES, hidden_dim=115, role_dim=8, intent_dim=8, graph_encoder="edr",
        role_gate_mode="none", target_policy="straight", strict_target_sensing=True,
        agent_target_info_bottleneck=True, relay_dependent_task=True, business_grounded_geometry=True,
        communication_range_scale=1.0, communication_dropout_prob=0.0, message_delay_steps=0,
        radar_dropout_prob=0.0, min_success_step=260, failed_blue_agent=-1,
        node_failure_start_step=0, node_failure_duration_steps=0, evaluation_enabled=False,
        target_kl=None, save_interval=RUNTIME_SAVE_INTERVAL, save_snapshots=False, out_dir=str(out_dir),
        device="cuda" if torch.cuda.is_available() else "cpu", topology_curriculum_schedule="none",
        topology_curriculum_logging=False, fixed_f0_probability=None, drtp_sampler_mode="none",
        fixed_stratified_topology_sampler=True, fixed_stratified_topology_sampler_seed=seed,
        drtp_sampler_logging=True, actor_gradient_mode="utr", actor_gradient_logging=True,
        runtime_state_checkpointing=True, runtime_state_save_interval=RUNTIME_SAVE_INTERVAL,
        resume=None, init_checkpoint=None, runtime_state_resume=None, append_log=False,
    )


def run_one(seed: int, output_root: Path, t1_root: Path) -> dict:
    tape = json.loads((t1_root / "tape_manifest.json").read_text(encoding="utf-8"))
    if tape.get("episode_ids") != list(range(TAPE_START, TAPE_START + EPISODES)) or tape.get("tape_hash") != T1_TAPE_HASH:
        raise RuntimeError("missing or invalid frozen T1 development tape")
    out_dir = output_root / "runs" / "edr_sg" / f"seed{seed}"
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite EDR-D1 trajectory: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=False)
    cfg = training_config(seed, out_dir)
    manifest = {
        "protocol": PROTOCOL, "status": "running", "method": "EDR-SG-MAPPO", "arm": "edr_sg", "seed": seed,
        "parameter_count": 116728, "graph_encoder": "edr", "actor_gradient_mode": "utr",
        "updates": UPDATES, "environment_steps": ENVIRONMENT_STEPS, "num_envs": NUM_ENVS,
        "rollout_steps": ROLLOUT_STEPS, "from_scratch": True, "strict_continuous": True,
        "resume": False, "historical_checkpoint_used": False, "checkpoint_promotion": False,
        "early_stopping": False, "seed_exclusion": False, "final_checkpoint_only": True,
        "canonical_seeds_used": False, "held_out_seeds_used": False, "nominal_anchor": 0.5,
        "failure_groups": ["F0", "TE", "TL", "DS", "DL", "CP"],
        "conditional_failure_exposure": "uniform_fixed_cycle", "drtp_adaptation": False,
        "runtime_state_persistence_from_start": True, "runtime_state_save_interval": RUNTIME_SAVE_INTERVAL,
        "tape_hash": tape["tape_hash"], "tape_start": TAPE_START, "t1_reference_root": str(t1_root),
        "config_hash": config_hash(cfg), "config": cfg.__dict__,
    }
    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    train_ri_gmappo(cfg)
    checkpoint, runtime = out_dir / "actor_critic_latest.pt", out_dir / "actor_critic_runtime_state_latest.pt"
    sampler_manifest, sampler_log = out_dir / "fixed_stratified_topology_sampler_manifest.json", out_dir / "fixed_stratified_topology_sampler_log.csv"
    gradient_log = out_dir / "actor_gradient_telemetry.csv"
    required = (checkpoint, runtime, sampler_manifest, sampler_log, gradient_log, out_dir / "train_log.csv")
    missing = [str(path) for path in required if not path.exists() or path.stat().st_size == 0]
    if missing:
        raise FileNotFoundError(f"incomplete EDR-D1 trajectory: {missing}")
    manifest.update({"status": "completed", "final_checkpoint_sha256": sha256(checkpoint),
                     "runtime_checkpoint_sha256": sha256(runtime), "sampler_manifest_sha256": sha256(sampler_manifest),
                     "sampler_log_sha256": sha256(sampler_log), "actor_gradient_log_sha256": sha256(gradient_log)})
    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"status": "completed", "seed": seed, "checkpoint_sha256": manifest["final_checkpoint_sha256"]}, indent=2))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", choices=SEEDS, type=int, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--t1-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: explicit --execute is required")
    run_one(args.seed, args.output_root, args.t1_root)


if __name__ == "__main__":
    main()
