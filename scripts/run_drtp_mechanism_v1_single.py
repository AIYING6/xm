"""Run one frozen UTR/DRTP Mechanism V1 training trajectory on cloud hardware."""
from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from algorithms.ri_gmappo.simple_ri_gmappo import train_ri_gmappo  # noqa: E402
import run_drtp_sg_strict_10m_single as base  # noqa: E402


PROTOCOL = "DRTP-TRAINING-FAILURE-MECHANISM-V1"
SEEDS = (2601, 2602, 2603)
ARMS = {"utr_sg": "utr", "drtp_sg": "drtp"}
NUM_ENVS, ROLLOUT_STEPS, UPDATES = 4, 64, 3907
MILESTONES = {976: "250k", 1953: "500k", 2930: "750k", 3907: "1m"}
TAPE = ROOT / "diagnostics" / "drtp_mechanism_v1" / "03_tape" / "tape_manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def shared_config_hash(cfg) -> str:
    payload = dict(cfg.__dict__)
    for key in ("seed", "out_dir", "device", "drtp_sampler_seed", "drtp_sampler_mode"):
        payload.pop(key, None)
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode()).hexdigest()


def training_config(arm: str, seed: int, out_dir: Path):
    if arm not in ARMS or seed not in SEEDS:
        raise ValueError("unauthorized Mechanism V1 arm or seed")
    probe = base.training_config("utr_sg", seed, out_dir)
    return replace(
        probe,
        updates=UPDATES,
        save_interval=976,
        milestone_updates=MILESTONES,
        drtp_sampler_mode=ARMS[arm],
        drtp_sampler_seed=seed,
        drtp_sampler_total_updates=UPDATES,
        out_dir=str(out_dir),
        failure_aware_telemetry=True,
        failure_telemetry_pre_steps=20,
        failure_telemetry_post_steps=60,
        failure_telemetry_pseudo_onset=44,
        runtime_state_checkpointing=True,
        runtime_state_save_interval=976,
        evaluation_enabled=False,
    )


def run_one(arm: str, seed: int, output_root: Path) -> dict:
    tape = json.loads(TAPE.read_text(encoding="utf-8"))
    out_dir = output_root / "runs" / arm / f"seed{seed}"
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=False)
    cfg = training_config(arm, seed, out_dir)
    manifest = {
        "protocol": PROTOCOL, "status": "running", "arm": arm, "sampler_mode": ARMS[arm],
        "seed": seed, "updates": UPDATES, "environment_steps": UPDATES * NUM_ENVS * ROLLOUT_STEPS,
        "num_envs": NUM_ENVS, "rollout_steps": ROLLOUT_STEPS, "milestone_updates": MILESTONES,
        "parameter_count": 116728, "from_scratch": True, "strict_continuous": True,
        "runtime_resume_used": False, "warm_restart_used": False, "early_stopping": False,
        "checkpoint_promotion": False, "seed_exclusion": False, "held_out_seeds_used": False,
        "canonical_seeds_used": False, "historical_cohort_merged": False,
        "tape_hash": tape["tape_hash"], "tape_path": str(TAPE),
        "failure_aware_telemetry": True, "telemetry_window": {"pre": 20, "post": 60},
        "shared_config_hash": shared_config_hash(cfg), "config": cfg.__dict__,
        "source_commit": commit(), "started_at": time.time(),
    }
    manifest_path = out_dir / "run_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    try:
        train_ri_gmappo(cfg)
        required = []
        for label in MILESTONES.values():
            required.extend([
                out_dir / f"actor_critic_milestone_{label}.pt",
                out_dir / f"actor_critic_milestone_{label}_training_state.pt",
                out_dir / f"actor_critic_runtime_state_milestone_{label}.pt",
            ])
        required.extend([
            out_dir / "actor_critic_latest.pt", out_dir / "actor_critic_training_state_latest.pt",
            out_dir / "actor_critic_runtime_state_latest.pt", out_dir / "train_log.csv",
            out_dir / "drtp_topology_sampler_log.csv",
            out_dir / "failure_telemetry" / "episode_summary.jsonl",
            out_dir / "failure_telemetry" / "failure_event_window.jsonl",
            out_dir / "failure_telemetry" / "telemetry_manifest.json",
        ])
        missing = [str(path) for path in required if not path.exists() or path.stat().st_size == 0]
        if missing:
            raise RuntimeError("F_MECHANISM_V1_PERSISTENCE: " + ";".join(missing))
        manifest.update({
            "status": "completed", "finished_at": time.time(),
            "final_checkpoint_sha256": sha256(out_dir / "actor_critic_latest.pt"),
            "final_runtime_state_sha256": sha256(out_dir / "actor_critic_runtime_state_latest.pt"),
            "milestone_checkpoint_sha256": {label: sha256(out_dir / f"actor_critic_milestone_{label}.pt") for label in MILESTONES.values()},
            "milestone_runtime_state_sha256": {label: sha256(out_dir / f"actor_critic_runtime_state_milestone_{label}.pt") for label in MILESTONES.values()},
        })
    except Exception as exc:
        manifest.update({"status": "technical_invalid", "error": repr(exc), "finished_at": time.time()})
        manifest_path.write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
        raise
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"status": "completed", "arm": arm, "seed": seed}, indent=2))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=tuple(ARMS), required=True)
    parser.add_argument("--seed", choices=SEEDS, type=int, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: --execute is required")
    if not TAPE.exists():
        raise FileNotFoundError(f"frozen diagnostic tape missing: {TAPE}")
    run_one(args.arm, args.seed, args.output_root)


if __name__ == "__main__":
    main()
