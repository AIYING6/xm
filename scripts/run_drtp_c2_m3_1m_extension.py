"""Resume the frozen C2-M3 diagnostic trajectories from 500k to 1M exactly once."""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

from algorithms.ri_gmappo.simple_ri_gmappo import train_ri_gmappo
import run_drtp_sg_strict_10m_single as strict

FREEZE = ROOT / "configs" / "drtp_c2_m3_1m_extension_freeze.json"
ARMS = ("utr_sg", "group_weighted_utr_sg")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _seeds(freeze: dict) -> tuple[int, ...]:
    return tuple(seed for cohort in ("A", "B") for seed in freeze["cohorts"][cohort])


def _last_logged_update(path: Path) -> int:
    rows = path.read_text(encoding="utf-8").strip().splitlines()
    if len(rows) < 2:
        raise RuntimeError("frozen train_log.csv has no data rows")
    return int(rows[-1].split(",", 1)[0])


def _config(arm: str, seed: int, out: Path, freeze: dict):
    base = strict.training_config("utr_sg", strict.SEEDS[0], out)
    weighted = arm == "group_weighted_utr_sg"
    resume = freeze["resume"]
    return replace(
        base,
        seed=seed,
        updates=int(resume["local_updates"]),
        update_offset=int(resume["required_prior_update"]),
        out_dir=str(out),
        append_log=True,
        runtime_state_resume=str(out / resume["required_runtime_checkpoint"]),
        evaluation_enabled=False,
        save_interval=488,
        save_snapshots=False,
        runtime_state_checkpointing=True,
        runtime_state_save_interval=488,
        milestone_updates={int(key): value for key, value in freeze["budget"]["new_milestones"].items()},
        drtp_sampler_mode="none",
        fixed_stratified_topology_sampler=True,
        fixed_stratified_topology_sampler_seed=seed,
        group_weighted_actor_enabled=weighted,
        group_weighted_actor_auto_lagged=weighted,
        group_weighted_actor_scores=None,
        group_weighted_actor_strength=float(freeze["fixed_method"]["group_weighted_actor_strength"]),
        group_weighted_actor_min=float(freeze["fixed_method"]["group_weighted_actor_min"]),
        group_weighted_actor_max=float(freeze["fixed_method"]["group_weighted_actor_max"]),
        group_credit_telemetry=True,
        group_credit_telemetry_interval=int(freeze["telemetry"]["group_credit_interval_updates"]),
        failure_aware_telemetry=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=ARMS, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    if not args.execute or not freeze["authorization"]["extension_training_authorized"]:
        raise RuntimeError("explicit frozen M3 1M-extension authorization is required")
    if args.seed not in _seeds(freeze):
        raise ValueError("unfrozen seed")

    out = args.output_root / "runs" / args.arm / f"seed{args.seed}"
    source_manifest = out / "run_manifest.json"
    checkpoint = out / freeze["resume"]["required_runtime_checkpoint"]
    required = [
        source_manifest, checkpoint, out / "train_log.csv", out / "group_credit_telemetry.csv",
        out / "group_credit_gradient_conflicts.csv", out / "failure_telemetry" / "telemetry_manifest.json",
    ]
    if not all(path.is_file() for path in required):
        raise RuntimeError("missing required frozen 500k trajectory artifact")
    source = json.loads(source_manifest.read_text(encoding="utf-8"))
    if source.get("protocol") != freeze["source_protocol"] or source.get("status") != "completed":
        raise RuntimeError("source run manifest is not a completed frozen C2-M3 trajectory")
    if source.get("arm") != args.arm or int(source.get("seed")) != args.seed:
        raise RuntimeError("source run manifest identity mismatch")
    if _last_logged_update(out / "train_log.csv") != int(freeze["resume"]["required_prior_update"]):
        raise RuntimeError("source train log does not end at the frozen 500k update")

    extension_manifest = out / "m3_1m_extension_manifest.json"
    if extension_manifest.exists():
        raise FileExistsError("this frozen trajectory has already entered the 1M extension")
    for label in freeze["budget"]["new_milestones"].values():
        if (out / f"actor_critic_runtime_state_milestone_{label}.pt").exists():
            raise RuntimeError("a target extension milestone already exists; refusing overwrite")

    manifest = {
        "protocol": freeze["protocol"], "status": "running", "arm": args.arm, "seed": args.seed,
        "source_protocol": freeze["source_protocol"], "source_runtime_checkpoint": checkpoint.name,
        "source_runtime_checkpoint_sha256": _sha256(checkpoint),
        "source_train_log_sha256": _sha256(out / "train_log.csv"),
        "source_update": int(freeze["resume"]["required_prior_update"]),
        "target_update": int(freeze["resume"]["target_update"]), "started_at": time.time(),
        "evaluation_authorized": False, "algorithm_modification_authorized": False,
        "automatic_continuation": False,
    }
    extension_manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    try:
        train_ri_gmappo(_config(args.arm, args.seed, out, freeze))
        target = int(freeze["resume"]["target_update"])
        expected = [out / f"actor_critic_runtime_state_milestone_{label}.pt" for label in freeze["budget"]["new_milestones"].values()]
        if _last_logged_update(out / "train_log.csv") != target or not all(path.is_file() for path in expected):
            raise RuntimeError("1M extension did not produce all frozen endpoint artifacts")
        manifest.update(status="completed", completed_at=time.time(), final_train_log_sha256=_sha256(out / "train_log.csv"))
    except BaseException as exc:
        manifest.update(status="failed", completed_at=time.time(), error=repr(exc))
        raise
    finally:
        extension_manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
