"""Run exactly one frozen H2-confirmation Stage-1 UTR/DRTP trajectory."""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import replace
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

from algorithms.ri_gmappo.simple_ri_gmappo import train_ri_gmappo  # noqa: E402
import run_drtp_sg_strict_10m_single as strict  # noqa: E402

PROTOCOL = "DRTP-B-LINE-H2-CONFIRMATION-STAGE1-V1"
SEEDS = (2801, 2802, 2803, 2804, 2805)
ARMS = {"utr_sg": "utr", "drtp_sg": "drtp"}
UPDATES, NUM_ENVS, ROLLOUT_STEPS = 1953, 4, 64
MILESTONES = {976: "250k", 1953: "500k"}
TAPE = ROOT / "configs" / "drtp_h2_confirmation_development_tape.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_commit() -> str:
    lock = ROOT / "docs" / "drtp_bline_h2_confirmation" / "H2_CONFIRMATION_SOURCE_COMMIT.txt"
    if lock.exists():
        value = lock.read_text(encoding="utf-8").strip()
        if value and value != "PENDING_FIRST_SOURCE_COMMIT":
            return value
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "H2_CONFIRMATION_FROZEN_DELIVERY"


def training_config(arm: str, seed: int, output: Path):
    if arm not in ARMS or seed not in SEEDS:
        raise ValueError("H2 confirmation permits only UTR/DRTP × seeds 2801–2805")
    template = strict.training_config("utr_sg", strict.SEEDS[0], output)
    return replace(template, seed=seed, updates=UPDATES, save_interval=976,
                   milestone_updates=MILESTONES, out_dir=str(output),
                   drtp_sampler_mode=ARMS[arm], drtp_sampler_seed=seed,
                   drtp_sampler_total_updates=UPDATES,
                   failure_aware_telemetry=True,
                   failure_telemetry_pre_steps=20,
                   failure_telemetry_post_steps=60,
                   failure_telemetry_pseudo_onset=44,
                   runtime_state_checkpointing=True,
                   runtime_state_save_interval=976,
                   evaluation_enabled=False)


def run_one(arm: str, seed: int, output_root: Path) -> None:
    tape = json.loads(TAPE.read_text(encoding="utf-8"))
    out = output_root / "runs" / arm / f"seed{seed}"
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"refusing overwrite/rerun: {out}")
    out.mkdir(parents=True, exist_ok=False)
    cfg = training_config(arm, seed, out)
    manifest = {
        "protocol": PROTOCOL, "status": "running", "source_freeze_commit": source_commit(),
        "arm": arm, "sampler_mode": ARMS[arm], "seed": seed,
        "updates": UPDATES, "environment_steps": UPDATES * NUM_ENVS * ROLLOUT_STEPS,
        "num_envs": NUM_ENVS, "rollout_steps": ROLLOUT_STEPS,
        "milestone_updates": MILESTONES, "from_scratch": True,
        "early_stopping": False, "checkpoint_promotion": False, "seed_replacement": False,
        "strict_continuation_authorized": False, "failure_aware_telemetry": True,
        "telemetry_window": {"pre": 20, "post": 60}, "tape_hash": tape["tape_hash"],
        "config": cfg.__dict__, "started_at": time.time(),
    }
    manifest_path = out / "run_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    try:
        train_ri_gmappo(cfg)
        required = [out / "actor_critic_latest.pt", out / "actor_critic_runtime_state_latest.pt",
                    out / "train_log.csv", out / "drtp_topology_sampler_log.csv",
                    out / "failure_telemetry" / "episode_summary.jsonl",
                    out / "failure_telemetry" / "failure_event_window.jsonl"]
        for label in MILESTONES.values():
            required.extend([out / f"actor_critic_milestone_{label}.pt",
                             out / f"actor_critic_runtime_state_milestone_{label}.pt"])
        missing = [str(path) for path in required if not path.exists() or path.stat().st_size == 0]
        if missing:
            raise RuntimeError("H2 persistence failure: " + "; ".join(missing))
        manifest.update({"status": "completed", "finished_at": time.time(),
                         "final_checkpoint_sha256": sha256(out / "actor_critic_latest.pt")})
    except Exception as exc:
        manifest.update({"status": "technical_invalid", "finished_at": time.time(), "error": repr(exc)})
        manifest_path.write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
        raise
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=tuple(ARMS), required=True)
    parser.add_argument("--seed", type=int, choices=SEEDS, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("--execute required")
    run_one(args.arm, args.seed, args.output_root)
