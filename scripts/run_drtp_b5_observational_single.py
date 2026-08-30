"""Run one frozen B5 UTR/Original-DRTP observational trajectory on cloud."""
from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

from algorithms.ri_gmappo.simple_ri_gmappo import train_ri_gmappo  # noqa: E402
import run_drtp_sg_strict_10m_single as base  # noqa: E402


PROTOCOL = "DRTP-B5-OBSERVATIONAL-COHORT-V1"
SEEDS = (3601, 3602, 3603, 3604, 3605)
ARMS = {"utr_sg": "utr", "drtp_sg": "drtp"}
UPDATES, NUM_ENVS, ROLLOUT_STEPS = 3907, 4, 64
MILESTONES = {976: "250k", 1953: "500k", 2930: "750k", 3907: "1m"}
TAPE = ROOT / "configs" / "drtp_b5_observational_tape.json"
FREEZE = ROOT / "configs" / "drtp_b5_observational_freeze.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def delivery_commit() -> str:
    marker = ROOT / "SOURCE_COMMIT.txt"
    return marker.read_text(encoding="utf-8").strip() if marker.is_file() else "working-tree-preparation"


def shared_config_hash(cfg) -> str:
    payload = dict(cfg.__dict__)
    for key in ("seed", "out_dir", "device", "drtp_sampler_seed", "drtp_sampler_mode"):
        payload.pop(key, None)
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def training_config(arm: str, seed: int, out_dir: Path):
    if arm not in ARMS or seed not in SEEDS:
        raise ValueError("B5 permits only UTR/Original DRTP × seeds 3601–3605")
    template = base.training_config("utr_sg", base.SEEDS[0], out_dir)
    return replace(
        template,
        seed=seed,
        updates=UPDATES,
        save_interval=976,
        milestone_updates=MILESTONES,
        out_dir=str(out_dir),
        drtp_sampler_mode=ARMS[arm],
        drtp_sampler_seed=seed,
        drtp_sampler_total_updates=UPDATES,
        failure_aware_telemetry=True,
        failure_telemetry_pre_steps=20,
        failure_telemetry_post_steps=60,
        failure_telemetry_pseudo_onset=44,
        group_credit_telemetry=True,
        group_credit_telemetry_interval=20,
        runtime_state_checkpointing=True,
        runtime_state_save_interval=976,
        evaluation_enabled=False,
    )


def run_one(arm: str, seed: int, output_root: Path) -> None:
    tape = json.loads(TAPE.read_text(encoding="utf-8"))
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    out = output_root / "runs" / arm / f"seed{seed}"
    if out.exists():
        raise FileExistsError(f"refusing overwrite or performance rerun: {out}")
    out.mkdir(parents=True, exist_ok=False)
    cfg = training_config(arm, seed, out)
    manifest = {
        "protocol": PROTOCOL,
        "status": "running",
        "delivery_commit": delivery_commit(),
        "arm": arm,
        "sampler_mode": ARMS[arm],
        "seed": seed,
        "updates": UPDATES,
        "environment_steps": UPDATES * NUM_ENVS * ROLLOUT_STEPS,
        "num_envs": NUM_ENVS,
        "rollout_steps": ROLLOUT_STEPS,
        "milestone_updates": MILESTONES,
        "from_scratch": True,
        "parameter_count": 116728,
        "early_stopping": False,
        "checkpoint_promotion": False,
        "seed_replacement": False,
        "performance_rerun": False,
        "continuation_beyond_1m_authorized": False,
        "group_credit_telemetry": True,
        "group_credit_telemetry_interval": 20,
        "failure_aware_telemetry": True,
        "tape_hash": tape["tape_hash"],
        "tape_sha256": sha256(TAPE),
        "freeze_sha256": sha256(FREEZE),
        "shared_config_hash": shared_config_hash(cfg),
        "config": cfg.__dict__,
        "started_at": time.time(),
    }
    path = out / "run_manifest.json"
    path.write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    try:
        train_ri_gmappo(cfg)
        required = [
            out / "actor_critic_latest.pt",
            out / "actor_critic_training_state_latest.pt",
            out / "actor_critic_runtime_state_latest.pt",
            out / "train_log.csv",
            out / "drtp_topology_sampler_log.csv",
            out / "group_credit_telemetry.csv",
            out / "group_credit_gradient_conflicts.csv",
            out / "failure_telemetry" / "episode_summary.jsonl",
            out / "failure_telemetry" / "failure_event_window.jsonl",
            out / "failure_telemetry" / "telemetry_manifest.json",
        ]
        for label in MILESTONES.values():
            required.extend([
                out / f"actor_critic_milestone_{label}.pt",
                out / f"actor_critic_milestone_{label}_training_state.pt",
                out / f"actor_critic_runtime_state_milestone_{label}.pt",
            ])
        missing = [str(item) for item in required if not item.is_file() or item.stat().st_size == 0]
        if missing:
            raise RuntimeError("B5 persistence failure: " + "; ".join(missing))
        manifest.update({
            "status": "completed",
            "finished_at": time.time(),
            "final_checkpoint_sha256": sha256(out / "actor_critic_latest.pt"),
            "milestone_checkpoint_sha256": {
                label: sha256(out / f"actor_critic_milestone_{label}.pt") for label in MILESTONES.values()
            },
        })
    except Exception as exc:
        manifest.update({"status": "technical_invalid", "finished_at": time.time(), "error": repr(exc)})
        path.write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
        raise
    path.write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=tuple(ARMS), required=True)
    parser.add_argument("--seed", choices=SEEDS, type=int, required=True)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("--execute and separate human authorization are required")
    run_one(args.arm, args.seed, args.output_root)


if __name__ == "__main__":
    main()
