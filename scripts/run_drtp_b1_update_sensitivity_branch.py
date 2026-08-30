"""Run one frozen B1 short RNG branch from a 0.5M runtime checkpoint."""
from __future__ import annotations

import argparse
from dataclasses import asdict, fields, replace
import hashlib
import json
from pathlib import Path
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

from algorithms.ri_gmappo.rng_streams import RNGStreams  # noqa: E402
from algorithms.ri_gmappo.simple_ri_gmappo import (  # noqa: E402
    RIGMAPPOConfig,
    train_ri_gmappo,
)


PROTOCOL = "DRTP-B1-UPDATE-SENSITIVITY-BRANCH-V1"
COHORTS = {
    "formal_positive_2300": tuple(range(2301, 2306)),
    "independent_reversal_2400": tuple(range(2401, 2406)),
    "r1_mixed_3000": tuple(range(3001, 3006)),
    "b5_mixed_3600": tuple(range(3601, 3606)),
}
ARMS = ("utr_sg", "drtp_sg")
FAMILIES = ("rollout", "minibatch")
BRANCHES = tuple(range(4))
SOURCE_UPDATE = 1953
BRANCH_UPDATES = 64
HORIZONS = {1954: "u001", 1957: "u004", 1969: "u016", 2017: "u064"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def seed_tuple(source_seed: int, family: str, branch: int) -> tuple[dict[str, int], int]:
    fixed_master = 81_000_000 + int(source_seed)
    branch_master = 82_000_000 + int(source_seed) * 10 + int(branch)
    fixed = asdict(RNGStreams.from_master(fixed_master).seeds)
    varied = asdict(RNGStreams.from_master(branch_master).seeds)
    if family == "rollout":
        for key in ("env_seed", "action_seed", "topology_seed"):
            fixed[key] = varied[key]
    elif family == "minibatch":
        fixed["minibatch_seed"] = varied["minibatch_seed"]
    else:
        raise ValueError(f"unknown B1 branch family: {family}")
    return fixed, branch_master


def source_config(manifest_path: Path) -> RIGMAPPOConfig:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    raw = manifest.get("config")
    if not isinstance(raw, dict):
        raise ValueError(f"source manifest has no frozen config: {manifest_path}")
    allowed = {field.name for field in fields(RIGMAPPOConfig)}
    unknown = sorted(set(raw) - allowed)
    if unknown:
        raise ValueError(f"source manifest has unsupported config fields: {unknown}")
    return RIGMAPPOConfig(**raw)


def run_branch(cohort: str, arm: str, seed: int, family: str, branch: int,
               assets_root: Path, output_root: Path) -> None:
    if cohort not in COHORTS or seed not in COHORTS[cohort]:
        raise ValueError("invalid B1 cohort/seed binding")
    if arm not in ARMS or family not in FAMILIES or branch not in BRANCHES:
        raise ValueError("invalid B1 branch cell")
    source = assets_root / cohort / arm / f"seed{seed}"
    runtime = source / "actor_critic_runtime_state_milestone_500k.pt"
    source_manifest = source / "run_manifest.json"
    if not runtime.is_file() or not source_manifest.is_file():
        raise FileNotFoundError(f"missing B1 source assets: {source}")
    out = output_root / "branches" / cohort / arm / f"seed{seed}" / family / f"branch{branch}"
    if out.exists():
        raise FileExistsError(f"refusing B1 branch rerun: {out}")
    out.mkdir(parents=True, exist_ok=False)
    tuple_values, branch_master = seed_tuple(seed, family, branch)
    cfg = source_config(source_manifest)
    cfg = replace(
        cfg,
        updates=BRANCH_UPDATES,
        update_offset=SOURCE_UPDATE,
        out_dir=str(out),
        runtime_state_resume=str(runtime),
        append_log=False,
        evaluation_enabled=False,
        save_interval=BRANCH_UPDATES,
        save_snapshots=False,
        milestone_updates=HORIZONS,
        runtime_state_checkpointing=False,
        runtime_state_save_interval=None,
        failure_aware_telemetry=False,
        group_credit_telemetry=False,
        rng_decomposition=True,
        rng_seed_tuple=tuple_values,
        diagnostic_rng_branch_mode=family,
        diagnostic_rng_branch_seed=branch_master,
    )
    manifest = {
        "protocol": PROTOCOL,
        "status": "running",
        "cohort": cohort,
        "arm": arm,
        "source_training_seed": seed,
        "source_update": SOURCE_UPDATE,
        "source_runtime_sha256": sha256(runtime),
        "family": family,
        "branch": branch,
        "branch_master_seed": branch_master,
        "rng_seed_tuple": tuple_values,
        "branch_updates": BRANCH_UPDATES,
        "environment_steps": BRANCH_UPDATES * cfg.num_envs * cfg.rollout_steps,
        "horizons": HORIZONS,
        "independent_unit": "source_training_seed",
        "technical_repetition": "rng_branch",
        "algorithm_modified": False,
        "checkpoint_promoted": False,
        "started_at": time.time(),
    }
    manifest_path = out / "branch_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    try:
        train_ri_gmappo(cfg)
        required = [out / "train_log.csv"] + [out / f"actor_critic_milestone_{label}.pt" for label in HORIZONS.values()]
        missing = [str(path) for path in required if not path.is_file() or path.stat().st_size == 0]
        if missing:
            raise RuntimeError(f"incomplete B1 branch: {missing}")
        manifest.update({
            "status": "completed",
            "finished_at": time.time(),
            "horizon_checkpoint_sha256": {label: sha256(out / f"actor_critic_milestone_{label}.pt") for label in HORIZONS.values()},
        })
    except Exception as exc:
        manifest.update({"status": "technical_invalid", "finished_at": time.time(), "error": repr(exc)})
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        raise
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cohort", choices=tuple(COHORTS), required=True)
    parser.add_argument("--arm", choices=ARMS, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--family", choices=FAMILIES, required=True)
    parser.add_argument("--branch", choices=BRANCHES, type=int, required=True)
    parser.add_argument("--assets-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("--execute and separate human authorization are required")
    run_branch(args.cohort, args.arm, args.seed, args.family, args.branch, args.assets_root, args.output_root)


if __name__ == "__main__":
    main()
