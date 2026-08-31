"""Run one P1 observational Original-DRTP trajectory; Selective-KLR is absent."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
from algorithms.ri_gmappo.simple_ri_gmappo import train_ri_gmappo
import run_drtp_sg_strict_10m_single as strict

FREEZE = ROOT / "configs" / "drtp_selective_klr_intervention_utility_p1_freeze.json"
SEEDS = tuple(range(3801, 3811))
UPDATES = 1953
MILESTONES = {976: "250k", 1953: "500k"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "UNAVAILABLE"


def config(seed: int, out_dir: Path):
    if seed not in SEEDS:
        raise ValueError("unauthorized P1 seed")
    base = strict.training_config("drtp_sg", 1901, out_dir)
    return replace(
        base, seed=seed, updates=UPDATES, save_interval=976, milestone_updates=MILESTONES,
        out_dir=str(out_dir), drtp_sampler_mode="drtp", drtp_sampler_seed=seed,
        drtp_sampler_total_updates=UPDATES, policy_update_guard_mode="none", target_kl=None,
        intervention_utility_audit_enabled=True, intervention_utility_alarm_kl=0.02,
        intervention_utility_probe_count=4, intervention_utility_probe_seed=seed,
        runtime_state_checkpointing=True, runtime_state_save_interval=976, evaluation_enabled=False,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, choices=SEEDS, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("--execute required")
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    if not freeze["authorization"]["p1_shadow_audit_authorized"]:
        raise RuntimeError("P1 authorization missing")
    out = args.output_root / "runs" / "drtp_sg" / f"seed{args.seed}"
    if out.exists():
        raise FileExistsError(f"refusing rerun/overwrite: {out}")
    out.mkdir(parents=True)
    cfg = config(args.seed, out)
    manifest = {
        "protocol": freeze["protocol"], "status": "running", "delivery_commit": head(),
        "arm": "drtp_sg", "official_trajectory": "Original DRTP", "seed": args.seed,
        "cohort": "A" if args.seed <= 3805 else "B", "updates": UPDATES,
        "official_environment_steps": 499968, "milestones": MILESTONES,
        "alarm_kl": cfg.intervention_utility_alarm_kl, "probe_base_ids": cfg.intervention_utility_probe_count,
        "selector_training": False, "official_branch_selection": "accept_always",
        "formal_evaluation_tape_used": False, "early_stopping": False, "checkpoint_promotion": False,
        "seed_replacement": False, "performance_rerun": False, "automatic_continuation": False,
        "freeze_sha256": sha(FREEZE), "started_at": time.time(),
    }
    (out / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    try:
        train_ri_gmappo(cfg)
        required = [
            out / "actor_critic_milestone_250k.pt", out / "actor_critic_milestone_500k.pt",
            out / "actor_critic_runtime_state_milestone_500k.pt", out / "train_log.csv",
            out / "drtp_topology_sampler_log.csv", out / "intervention_utility" / "manifest.json",
            out / "intervention_utility" / "trigger_probe_events.csv",
        ]
        if not all(path.exists() for path in required):
            raise RuntimeError("missing required P1 trajectory artifact")
        manifest.update({"status": "completed", "completed_at": time.time()})
    except BaseException as exc:
        manifest.update({"status": "failed", "error": repr(exc)})
        (out / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        raise
    (out / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
