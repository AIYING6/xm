"""Run one future-authorized Stable-v2 0.5M pilot trajectory (cloud only)."""
from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
from algorithms.ri_gmappo.simple_ri_gmappo import train_ri_gmappo  # noqa: E402
import run_drtp_sg_strict_10m_single as strict  # noqa: E402


PROTOCOL = "DRTP-STABLE-V2-PILOT-STAGE1-V1"
ALGORITHM_FREEZE_COMMIT = "3c17bf62"
SEEDS = (3101, 3102, 3103)
UPDATES, NUM_ENVS, ROLLOUT_STEPS = 1953, 4, 64
MILESTONES = {976: "250k", 1953: "500k"}
ARMS = {
    "utr_sg": {"sampler": "utr", "guard": "none", "target_kl": None},
    "drtp_sg": {"sampler": "drtp", "guard": "none", "target_kl": None},
    "drtp_klr_sg": {"sampler": "drtp", "guard": "post_step_actor_rollback", "target_kl": 0.02},
}
TAPE = ROOT / "configs" / "drtp_stable_v2_pilot_tape.json"
D1_AUDIT = ROOT / "docs" / "drtp_stable_v2_d1_20260829" / "STABLE_V2_D1_TECHNICAL_AUDIT.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_commit() -> str:
    marker = ROOT / "SOURCE_COMMIT.txt"
    if marker.exists():
        return marker.read_text(encoding="utf-8").strip()
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNAVAILABLE"


def training_config(arm: str, seed: int, output: Path):
    if arm not in ARMS or seed not in SEEDS:
        raise ValueError("Stable-v2 pilot permits only three frozen arms × seeds 3101-3103")
    spec = ARMS[arm]
    template = strict.training_config("utr_sg", strict.SEEDS[0], output)
    return replace(
        template,
        seed=seed,
        updates=UPDATES,
        save_interval=976,
        milestone_updates=MILESTONES,
        out_dir=str(output),
        drtp_sampler_mode=spec["sampler"],
        drtp_sampler_seed=seed,
        drtp_sampler_total_updates=UPDATES,
        policy_update_guard_mode=spec["guard"],
        target_kl=spec["target_kl"],
        runtime_state_checkpointing=True,
        runtime_state_save_interval=976,
        evaluation_enabled=False,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=tuple(ARMS), required=True)
    parser.add_argument("--seed", type=int, choices=SEEDS, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("--execute required")
    tape = json.loads(TAPE.read_text(encoding="utf-8"))
    audit = json.loads(D1_AUDIT.read_text(encoding="utf-8"))
    if audit.get("status") != "D1_TECHNICAL_PASS":
        raise RuntimeError("Stable-v2 D1 technical audit is not PASS")
    output = args.output_root / "runs" / args.arm / f"seed{args.seed}"
    if output.exists():
        raise FileExistsError(f"refusing overwrite/performance rerun: {output}")
    output.mkdir(parents=True, exist_ok=False)
    cfg = training_config(args.arm, args.seed, output)
    manifest_path = output / "run_manifest.json"
    manifest = {
        "protocol": PROTOCOL,
        "status": "running",
        "algorithm_freeze_commit": ALGORITHM_FREEZE_COMMIT,
        "delivery_commit": source_commit(),
        "arm": args.arm,
        "seed": args.seed,
        "sampler_mode": cfg.drtp_sampler_mode,
        "policy_update_guard_mode": cfg.policy_update_guard_mode,
        "target_kl": cfg.target_kl,
        "updates": UPDATES,
        "environment_steps": UPDATES * NUM_ENVS * ROLLOUT_STEPS,
        "num_envs": NUM_ENVS,
        "rollout_steps": ROLLOUT_STEPS,
        "milestone_updates": MILESTONES,
        "from_scratch": True,
        "early_stopping": False,
        "checkpoint_promotion": False,
        "seed_replacement": False,
        "rerun_authorized": False,
        "continuation_authorized": False,
        "parameter_count": 116728,
        "final_checkpoint_selection": "common_500k_final_only",
        "tape_hash": tape["tape_hash"],
        "tape_sha256": sha256(TAPE),
        "d1_audit_sha256": sha256(D1_AUDIT),
        "config": cfg.__dict__,
        "started_at": time.time(),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    try:
        train_ri_gmappo(cfg)
        required = [
            output / "actor_critic_latest.pt",
            output / "actor_critic_runtime_state_latest.pt",
            output / "train_log.csv",
            output / "drtp_topology_sampler_log.csv",
        ]
        for label in MILESTONES.values():
            required.extend([
                output / f"actor_critic_milestone_{label}.pt",
                output / f"actor_critic_runtime_state_milestone_{label}.pt",
            ])
        missing = [str(path) for path in required if not path.exists() or path.stat().st_size == 0]
        if missing:
            raise RuntimeError("Stable-v2 persistence failure: " + "; ".join(missing))
        manifest.update({
            "status": "completed",
            "finished_at": time.time(),
            "final_checkpoint_sha256": sha256(output / "actor_critic_latest.pt"),
            "final_runtime_state_sha256": sha256(output / "actor_critic_runtime_state_latest.pt"),
        })
    except Exception as exc:
        manifest.update({"status": "technical_invalid", "finished_at": time.time(), "error": repr(exc)})
        manifest_path.write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
        raise
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
