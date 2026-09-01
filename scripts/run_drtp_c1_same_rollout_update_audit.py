"""Execute one frozen C1 same-rollout A/B update audit for a UTR runtime state.

The sequence is deliberately short: one common ordinary-PPO prelude update
produces lagged, training-only group TD-error scores.  The prelude runtime
state is then resumed twice with exact replay: branch A makes an ordinary PPO
update and branch B makes the bounded group-weighted actor update.  No branch
reads an evaluation tape or runs an evaluation episode.
"""

from __future__ import annotations

import argparse
from dataclasses import fields, replace
import csv
import hashlib
import json
from pathlib import Path
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.drtp_topology_sampler import FAILURE_GROUPS  # noqa: E402
from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOConfig, train_ri_gmappo  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_last_row(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise RuntimeError(f"missing train telemetry rows: {path}")
    return rows[-1]


def source_config(path: Path) -> RIGMAPPOConfig:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("status") != "completed" or payload.get("arm") != "utr_sg":
        raise RuntimeError(f"invalid frozen UTR source manifest: {path}")
    raw = payload.get("config")
    if not isinstance(raw, dict):
        raise RuntimeError("source manifest does not contain its training config")
    allowed = {field.name for field in fields(RIGMAPPOConfig)}
    unknown = sorted(set(raw).difference(allowed))
    if unknown:
        raise RuntimeError(f"source config contains unsupported fields: {unknown}")
    return RIGMAPPOConfig(**raw)


def base_branch_config(cfg: RIGMAPPOConfig, runtime: Path, out_dir: Path, update_offset: int) -> RIGMAPPOConfig:
    return replace(
        cfg,
        updates=1,
        update_offset=int(update_offset),
        out_dir=str(out_dir),
        runtime_state_resume=str(runtime),
        append_log=False,
        evaluation_enabled=False,
        actor_gradient_mode="standard",
        target_kl=None,
        policy_update_guard_mode="none",
        intervention_utility_audit_enabled=False,
        counterfactual_critic_enabled=False,
        drtp_sampler_mode="none",
        fixed_stratified_topology_sampler=True,
        fixed_stratified_topology_sampler_seed=int(cfg.seed),
        runtime_state_checkpointing=True,
        runtime_state_save_interval=1,
        diagnostic_rng_branch_mode="exact_replay",
        diagnostic_rng_branch_seed=None,
        group_weighted_actor_enabled=False,
        group_weighted_actor_scores=None,
        group_weighted_actor_telemetry=True,
    )


def required_branch_files(out_dir: Path) -> tuple[Path, Path]:
    log = out_dir / "train_log.csv"
    runtime = out_dir / "actor_critic_runtime_state_latest.pt"
    if not log.is_file() or not runtime.is_file() or runtime.stat().st_size == 0:
        raise RuntimeError(f"incomplete C1 branch: {out_dir}")
    return log, runtime


def run_seed(seed: int, source_root: Path, output_root: Path, freeze: dict) -> Path:
    if seed not in freeze["source"]["training_seeds"]:
        raise ValueError("seed is not frozen for C1")
    source = source_root / f"seed{seed}"
    source_manifest = source / "run_manifest.json"
    source_runtime = source / "actor_critic_runtime_state_latest.pt"
    if not source_manifest.is_file() or not source_runtime.is_file():
        raise FileNotFoundError(f"missing C1 source artifacts: {source}")
    cfg = source_config(source_manifest)
    if int(cfg.updates) != int(freeze["source"]["source_update"]):
        raise RuntimeError("source update does not match frozen C1 contract")
    root = output_root / "runs" / f"seed{seed}"
    if root.exists():
        raise FileExistsError(f"refusing C1 rerun: {root}")
    prelude = root / "prelude"
    ordinary = root / "ordinary"
    weighted = root / "weighted"
    root.mkdir(parents=True, exist_ok=False)
    manifest_path = root / "c1_manifest.json"
    manifest = {
        "protocol": freeze["protocol"], "status": "running", "seed": seed,
        "source_runtime": str(source_runtime.resolve()), "source_runtime_sha256": sha256(source_runtime),
        "source_manifest_sha256": sha256(source_manifest), "source_update": freeze["source"]["source_update"],
        "formal_or_heldout_tape_used": False, "evaluation_enabled": False,
        "common_prelude_updates": 1, "branch_updates": 1,
        "weight_sweep": False, "checkpoint_promotion": False,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    try:
        prelude_cfg = base_branch_config(cfg, source_runtime, prelude, freeze["source"]["source_update"])
        train_ri_gmappo(prelude_cfg)
        prelude_log, prelude_runtime = required_branch_files(prelude)
        prelude_row = read_last_row(prelude_log)
        scores = {group: float(prelude_row[f"group_td_abs_{group}"]) for group in FAILURE_GROUPS}
        if not all(value >= 0.0 for value in scores.values()):
            raise RuntimeError("C1 prelude contains invalid lagged TD-error score")

        ordinary_cfg = base_branch_config(cfg, prelude_runtime, ordinary, freeze["source"]["source_update"] + 1)
        weighted_cfg = base_branch_config(cfg, prelude_runtime, weighted, freeze["source"]["source_update"] + 1)
        weighted_cfg = replace(
            weighted_cfg,
            group_weighted_actor_enabled=True,
            group_weighted_actor_scores=scores,
            group_weighted_actor_strength=float(freeze["candidate"]["failure_weight_strength"]),
            group_weighted_actor_min=float(freeze["candidate"]["failure_weight_min"]),
            group_weighted_actor_max=float(freeze["candidate"]["failure_weight_max"]),
        )
        train_ri_gmappo(ordinary_cfg)
        train_ri_gmappo(weighted_cfg)
        ordinary_log, ordinary_runtime = required_branch_files(ordinary)
        weighted_log, weighted_runtime = required_branch_files(weighted)
        ordinary_row = read_last_row(ordinary_log)
        weighted_row = read_last_row(weighted_log)
        if ordinary_row["group_weighted_actor_batch_sha256"] != weighted_row["group_weighted_actor_batch_sha256"]:
            raise RuntimeError("C1 branches did not consume the same training rollout")
        manifest.update({
            "status": "completed", "lagged_td_abs_scores": scores,
            "prelude_runtime_sha256": sha256(prelude_runtime),
            "ordinary_runtime_sha256": sha256(ordinary_runtime),
            "weighted_runtime_sha256": sha256(weighted_runtime),
            "paired_batch_sha256": ordinary_row["group_weighted_actor_batch_sha256"],
            "finished_at": time.time(),
        })
    except BaseException as exc:
        manifest.update({"status": "technical_invalid", "error": repr(exc), "finished_at": time.time()})
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        raise
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, default=ROOT / "configs" / "drtp_c1_same_rollout_update_audit_freeze.json")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("--execute and the frozen C1 authorization are required")
    freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
    path = run_seed(args.seed, args.source_root, args.output_root, freeze)
    print(json.dumps({"status": "C1_SEED_COMPLETED", "manifest": str(path)}, indent=2))


if __name__ == "__main__":
    main()
