"""Continue one Phase-C TCR/SPC trajectory strictly from its runtime state."""
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
from scripts.run_tcr_spc_phase_c_single import ARMS, SEEDS, training_config as phase_c_config  # noqa: E402


PROTOCOL = "TCR-SPC-PHASE-D-1M-3M-CONTINUATION-V1"
SOURCE_UPDATE = 3907
FINAL_UPDATE = 11719
CONTINUATION_UPDATES = FINAL_UPDATE - SOURCE_UPDATE
NUM_ENVS, ROLLOUT_STEPS = 4, 64
FINAL_STEPS = FINAL_UPDATE * NUM_ENVS * ROLLOUT_STEPS
MILESTONES = {5859: "1p5m", 7813: "2m", 9766: "2p5m", 11719: "3m"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def continuation_config(arm: str, seed: int, out_dir: Path, runtime_state: Path) -> RIGMAPPOConfig:
    cfg = phase_c_config(arm, seed, out_dir)
    cfg.updates = CONTINUATION_UPDATES
    cfg.update_offset = SOURCE_UPDATE
    cfg.milestone_updates = MILESTONES
    cfg.save_interval = 500
    cfg.runtime_state_checkpointing = True
    cfg.runtime_state_save_interval = 500
    cfg.runtime_state_resume = str(runtime_state)
    cfg.resume = None
    cfg.init_checkpoint = None
    cfg.append_log = True
    return cfg


def validate_source(source_root: Path, arm: str, seed: int) -> tuple[Path, dict]:
    run_dir = source_root / "runs" / arm / f"seed{seed}"
    manifest_path = run_dir / "run_manifest.json"
    runtime = run_dir / "actor_critic_runtime_state_latest.pt"
    if not manifest_path.exists() or not runtime.exists():
        raise FileNotFoundError(f"missing Phase-C runtime state: {run_dir}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    required = {
        "status": "completed", "updates": SOURCE_UPDATE, "environment_steps": 1_000_192,
        "parameter_count": 116728, "runtime_state_persistence_from_start": True,
        "from_scratch": True, "strict_continuous": True, "canonical_seeds_used": False,
        "held_out_seeds_used": False,
    }
    invalid = [key for key, value in required.items() if manifest.get(key) != value]
    if invalid:
        raise RuntimeError(f"Phase-C source manifest mismatch at {run_dir}: {invalid}")
    return runtime, manifest


def run_one(source_root: Path, output_root: Path, arm: str, seed: int) -> dict:
    if arm not in ARMS or seed not in SEEDS:
        raise ValueError("unauthorized Phase-D arm or seed")
    runtime_state, source_manifest = validate_source(source_root, arm, seed)
    tape_manifest = source_root / "tape_manifest.json"
    if not tape_manifest.exists():
        raise FileNotFoundError(f"missing frozen development tape manifest: {tape_manifest}")
    tape = json.loads(tape_manifest.read_text(encoding="utf-8"))
    out_dir = output_root / "runs" / arm / f"seed{seed}"
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=False)
    cfg = continuation_config(arm, seed, out_dir, runtime_state)
    manifest = {
        "protocol": PROTOCOL, "status": "running", "arm": arm,
        "actor_gradient_mode": ARMS[arm], "seed": seed,
        "source_update": SOURCE_UPDATE, "final_update": FINAL_UPDATE,
        "continuation_updates": CONTINUATION_UPDATES,
        "source_environment_steps": 1_000_192, "final_environment_steps": FINAL_STEPS,
        "num_envs": NUM_ENVS, "rollout_steps": ROLLOUT_STEPS,
        "parameter_count": 116728, "strict_continuation": True,
        "source_runtime_state": str(runtime_state),
        "source_runtime_state_sha256": sha256(runtime_state),
        "warm_restart_used": False, "from_scratch_used": False,
        "early_stopping": False, "checkpoint_promotion": False,
        "seed_exclusion": False, "canonical_seeds_used": False,
        "held_out_seeds_used": False, "final_checkpoint_only": True,
        "milestone_updates": MILESTONES, "milestones_for_curve_only": True,
        "runtime_state_persistence": True,
        "source_phase_c_checkpoint_sha256": source_manifest.get("checkpoint_sha256"),
        "tape_hash": tape["tape_hash"],
        "config": cfg.__dict__,
    }
    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    train_ri_gmappo(cfg)
    final_checkpoint = out_dir / "actor_critic_latest.pt"
    final_runtime = out_dir / "actor_critic_runtime_state_latest.pt"
    required = [final_checkpoint, final_runtime]
    for label in MILESTONES.values():
        required.extend([
            out_dir / f"actor_critic_milestone_{label}.pt",
            out_dir / f"actor_critic_runtime_state_milestone_{label}.pt",
        ])
    missing = [str(path) for path in required if not path.exists() or path.stat().st_size == 0]
    if missing:
        raise FileNotFoundError(f"incomplete Phase-D trajectory: {missing}")
    manifest.update({
        "status": "completed", "final_checkpoint": str(final_checkpoint),
        "final_runtime_state": str(final_runtime),
        "final_checkpoint_sha256": sha256(final_checkpoint),
        "final_runtime_state_sha256": sha256(final_runtime),
        "milestone_checkpoint_sha256": {
            label: sha256(out_dir / f"actor_critic_milestone_{label}.pt")
            for label in MILESTONES.values()
        },
        "milestone_runtime_state_sha256": {
            label: sha256(out_dir / f"actor_critic_runtime_state_milestone_{label}.pt")
            for label in MILESTONES.values()
        },
    })
    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--arm", choices=tuple(ARMS), required=True)
    parser.add_argument("--seed", choices=SEEDS, type=int, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: explicit --execute is required")
    result = run_one(args.source_root.resolve(), args.output_root.resolve(), args.arm, args.seed)
    print(json.dumps({"status": result["status"], "arm": args.arm, "seed": args.seed,
                      "final_checkpoint_sha256": result["final_checkpoint_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
