"""Run one explicitly authorized DRTP-SG-MAPPO held-out v2 trajectory."""
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
from run_drtp_sg_strict_10m_single import MILESTONES, UPDATES, sha256  # noqa: E402


PROTOCOL = "DRTP-SG-MAPPO-HELDOUT-CONFIRMATION-V2-TRAINING-V1"
SEEDS = (2001, 2002, 2003)
ARMS = {"utr_sg": "utr", "drtp_sg": "drtp"}
NUM_ENVS, ROLLOUT_STEPS = 4, 64


def config_hash(cfg: RIGMAPPOConfig) -> str:
    payload = dict(cfg.__dict__)
    for key in ("seed", "out_dir", "device", "drtp_sampler_seed"):
        payload.pop(key, None)
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")).hexdigest()


def training_config(arm: str, seed: int, out_dir: Path) -> RIGMAPPOConfig:
    if arm not in ARMS or seed not in SEEDS:
        raise ValueError("unauthorized held-out v2 arm or seed")
    return RIGMAPPOConfig(
        env_name="3d_intercept", seed=seed, num_envs=NUM_ENVS,
        rollout_steps=ROLLOUT_STEPS, updates=UPDATES, hidden_dim=115,
        role_dim=8, intent_dim=8, graph_encoder="single", role_gate_mode="none",
        target_policy="straight", strict_target_sensing=True,
        agent_target_info_bottleneck=True, relay_dependent_task=True,
        business_grounded_geometry=True, communication_range_scale=1.0,
        communication_dropout_prob=0.0, message_delay_steps=0,
        radar_dropout_prob=0.0, min_success_step=260,
        failed_blue_agent=-1, node_failure_start_step=0, node_failure_duration_steps=0,
        evaluation_enabled=False, target_kl=None, save_interval=UPDATES,
        save_snapshots=False, milestone_updates=MILESTONES, out_dir=str(out_dir),
        device="cuda" if torch.cuda.is_available() else "cpu",
        topology_curriculum_schedule="none", topology_curriculum_logging=False,
        fixed_f0_probability=None, drtp_sampler_mode=ARMS[arm],
        drtp_sampler_seed=seed, drtp_sampler_total_updates=UPDATES,
        drtp_sampler_logging=True, runtime_state_checkpointing=True,
        runtime_state_save_interval=UPDATES,
    )


def verify_config(cfg: RIGMAPPOConfig) -> dict:
    return {
        "protocol": PROTOCOL, "parameter_count": 116728,
        "updates": cfg.updates, "environment_steps": cfg.updates * cfg.num_envs * cfg.rollout_steps,
        "from_scratch": True, "strict_continuous_trajectory": True,
        "runtime_state_from_update_zero": cfg.runtime_state_checkpointing,
        "legacy_resume": cfg.resume, "runtime_state_resume": cfg.runtime_state_resume,
        "warm_restart": False, "milestones": cfg.milestone_updates,
        "held_out_seeds": list(SEEDS), "canonical_seeds_used": False,
    }


def run_one(arm: str, seed: int, output_root: Path) -> dict:
    out_dir = output_root / "runs" / arm / f"seed{seed}"
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=False)
    cfg = training_config(arm, seed, out_dir)
    manifest = {
        "protocol": PROTOCOL, "status": "running", "arm": arm, "sampler_mode": ARMS[arm],
        "seed": seed, "updates": UPDATES, "environment_steps": UPDATES * NUM_ENVS * ROLLOUT_STEPS,
        "num_envs": NUM_ENVS, "rollout_steps": ROLLOUT_STEPS, "milestone_updates": MILESTONES,
        "milestones_for_curve_only": True, "final_checkpoint_selection": "common_10m_final_only",
        "from_scratch": True, "strict_continuous_trajectory": True,
        "runtime_resume_used": False, "warm_restart_used": False, "early_stopping": False,
        "checkpoint_promotion": False, "seed_exclusion": False, "canonical_seeds_used": False,
        "held_out_seeds_used": True, "parameter_count": 116728, "graph_encoder": "single",
        "nominal_anchor": 0.5, "topology_group_universe": ["N", "F0", "TE", "TL", "DS", "DL", "CP"],
        "runtime_state_checkpointing": True, "runtime_state_format": "ri_gmappo_runtime_state_v1",
        "config_hash": config_hash(cfg), "config": cfg.__dict__,
    }
    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    train_ri_gmappo(cfg)
    final_checkpoint, final_runtime = out_dir / "actor_critic_latest.pt", out_dir / "actor_critic_runtime_state_latest.pt"
    if not final_checkpoint.exists() or not final_runtime.exists():
        raise FileNotFoundError("missing held-out final checkpoint or runtime state")
    checkpoint_hashes, runtime_hashes = {}, {}
    for label in MILESTONES.values():
        checkpoint = out_dir / f"actor_critic_milestone_{label}.pt"
        runtime = out_dir / f"actor_critic_runtime_state_milestone_{label}.pt"
        if not checkpoint.exists() or not runtime.exists():
            raise FileNotFoundError(f"missing fixed milestone {label}")
        checkpoint_hashes[label], runtime_hashes[label] = sha256(checkpoint), sha256(runtime)
    sampler_log = out_dir / "drtp_topology_sampler_log.csv"
    if not sampler_log.exists():
        raise FileNotFoundError(sampler_log)
    manifest.update({
        "status": "completed", "final_checkpoint": str(final_checkpoint),
        "final_checkpoint_sha256": sha256(final_checkpoint), "final_runtime_state_sha256": sha256(final_runtime),
        "milestone_checkpoint_sha256": checkpoint_hashes, "milestone_runtime_state_sha256": runtime_hashes,
        "sampler_log": str(sampler_log),
    })
    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"status": "completed", "arm": arm, "seed": seed,
                      "final_checkpoint_sha256": manifest["final_checkpoint_sha256"]}, indent=2))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=tuple(ARMS))
    parser.add_argument("--seed", choices=SEEDS, type=int)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--verify-config", action="store_true")
    args = parser.parse_args()
    if args.verify_config:
        print(json.dumps(verify_config(training_config("utr_sg", 2001, args.output_root / "config_probe")), indent=2, default=str))
        return
    if not args.execute or args.arm is None or args.seed is None:
        raise SystemExit("NO-GO: --execute, --arm, and --seed are required")
    run_one(args.arm, args.seed, args.output_root)


if __name__ == "__main__":
    main()
