"""Run one prospective UTR/DRTP Q2 formal 10M training trajectory."""
from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from algorithms.ri_gmappo.simple_ri_gmappo import train_ri_gmappo  # noqa: E402
import run_drtp_sg_strict_10m_single as base  # noqa: E402


PROTOCOL = "DRTP-UTR-Q2-FORMAL-PAIRED-5SEED-TRAINING-V1"
SEEDS = (2301, 2302, 2303, 2304, 2305)
ARMS = base.ARMS
UPDATES, MILESTONES = base.UPDATES, base.MILESTONES
NUM_ENVS, ROLLOUT_STEPS = base.NUM_ENVS, base.ROLLOUT_STEPS


def training_config(arm: str, seed: int, out_dir: Path):
    if arm not in ARMS or seed not in SEEDS:
        raise ValueError("unauthorized formal arm or seed")
    probe = base.training_config(arm, base.SEEDS[0], out_dir)
    return replace(probe, seed=seed, drtp_sampler_seed=seed, out_dir=str(out_dir))


def run_one(arm: str, seed: int, output_root: Path) -> dict:
    out_dir = output_root / "runs" / arm / f"seed{seed}"
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=False)
    cfg = training_config(arm, seed, out_dir)
    manifest = {
        "protocol": PROTOCOL, "status": "running", "arm": arm,
        "sampler_mode": ARMS[arm], "seed": seed, "updates": UPDATES,
        "environment_steps": UPDATES * NUM_ENVS * ROLLOUT_STEPS,
        "num_envs": NUM_ENVS, "rollout_steps": ROLLOUT_STEPS,
        "milestone_updates": MILESTONES, "milestones_for_curve_only": True,
        "final_checkpoint_selection": "common_10m_final_only",
        "from_scratch": True, "strict_continuous_trajectory": True,
        "runtime_resume_used": False, "warm_restart_used": False,
        "early_stopping": False, "checkpoint_promotion": False,
        "seed_exclusion": False, "canonical_seeds_used": False,
        "prospective_formal_confirmation": True,
        "parameter_count": 116728, "graph_encoder": "single",
        "nominal_anchor": 0.5,
        "topology_group_universe": ["N", "F0", "TE", "TL", "DS", "DL", "CP"],
        "runtime_state_checkpointing": True,
        "runtime_state_format": "ri_gmappo_runtime_state_v1",
        "config_hash": base.config_hash(cfg), "config": cfg.__dict__,
    }
    manifest_path = out_dir / "run_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    train_ri_gmappo(cfg)
    final_checkpoint = out_dir / "actor_critic_latest.pt"
    final_runtime = out_dir / "actor_critic_runtime_state_latest.pt"
    if not final_checkpoint.exists() or not final_runtime.exists():
        raise FileNotFoundError("missing formal final checkpoint/runtime state")
    checkpoint_hashes, runtime_hashes = {}, {}
    for label in MILESTONES.values():
        checkpoint = out_dir / f"actor_critic_milestone_{label}.pt"
        runtime = out_dir / f"actor_critic_runtime_state_milestone_{label}.pt"
        if not checkpoint.exists() or not runtime.exists():
            raise FileNotFoundError(f"missing fixed milestone {label}")
        checkpoint_hashes[label] = base.sha256(checkpoint)
        runtime_hashes[label] = base.sha256(runtime)
    sampler_log = out_dir / "drtp_topology_sampler_log.csv"
    if not sampler_log.exists():
        raise FileNotFoundError(sampler_log)
    manifest.update({
        "status": "completed", "final_checkpoint": str(final_checkpoint),
        "final_checkpoint_sha256": base.sha256(final_checkpoint),
        "final_runtime_state_sha256": base.sha256(final_runtime),
        "milestone_checkpoint_sha256": checkpoint_hashes,
        "milestone_runtime_state_sha256": runtime_hashes,
        "sampler_log": str(sampler_log),
    })
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
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
        cfg = training_config("utr_sg", SEEDS[0], args.output_root / "config_probe")
        print(json.dumps(base.verify_config(cfg), indent=2, default=str))
        return
    if not args.execute or args.arm is None or args.seed is None:
        raise SystemExit("NO-GO: --execute, --arm, and --seed are required")
    run_one(args.arm, args.seed, args.output_root)


if __name__ == "__main__":
    main()
