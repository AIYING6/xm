"""S3-R2 minimal Full simplification: multi-relation graph without Role-Gate."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import run_phase_s3_development_smoke as s3  # noqa: E402
from scripts import run_phase_s3r_evaluation_remediation as s3r  # noqa: E402

PROTOCOL = "PHASE-S3-R2-V1"
METHOD_KEY = "simple_full_no_role_gate"
METHOD_SPEC = {"label": "Multi-Relation Full without Role-Gate", "encoder": "multi_relation", "hidden": 64, "gate": "none"}
SEEDS = (1501, 1502, 1503)
UPDATES = s3.UPDATES
EPISODES = 100


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def prelaunch(output_root: Path) -> None:
    cfg = s3.training_config(METHOD_SPEC, SEEDS[0], output_root / "unused", UPDATES)
    checks = {
        "protocol": PROTOCOL,
        "single_component_change": cfg.graph_encoder == "multi_relation" and cfg.role_gate_mode == "none",
        "fixed_budget": UPDATES * s3.NUM_ENVS * s3.ROLLOUT_STEPS == 200192,
        "development_seeds_only": SEEDS == (1501, 1502, 1503) and all(seed not in range(5) for seed in SEEDS),
        "no_resume": cfg.resume is None and cfg.init_checkpoint is None,
        "no_in_training_evaluation": cfg.evaluation_enabled is False,
        "s2_geometry_preserved": cfg.business_grounded_geometry and cfg.relay_dependent_task,
        "s2_failure_preserved": cfg.failed_blue_agent == 1 and cfg.node_failure_start_step == 44 and cfg.node_failure_duration_steps == 80,
        "shared_tape": s3r.TAPE_START == 340000 and EPISODES == 100,
        "canonical_training": False,
    }
    result = {"protocol": PROTOCOL, "checks": checks, "pass": all(value for key, value in checks.items() if key != "canonical_training"), "training_started": False, "commit": git_head()}
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "PRELAUNCH_AUDIT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if not result["pass"]:
        raise SystemExit(1)


def run_seed(seed: int, output_root: Path, updates: int, episodes: int) -> None:
    run_dir = output_root / "runs" / METHOD_KEY / f"seed{seed}"
    if run_dir.exists():
        raise FileExistsError(f"refusing to overwrite {run_dir}")
    run_dir.mkdir(parents=True)
    cfg = s3.training_config(METHOD_SPEC, seed, run_dir, updates)
    manifest = {
        "protocol": PROTOCOL, "status": "running", "artifact_class": "DEVELOPMENT_ONLY",
        "method": METHOD_KEY, "architecture_family": "multi_relation_without_role_gate",
        "seed": seed, "updates": updates, "num_envs": s3.NUM_ENVS,
        "rollout_steps": s3.ROLLOUT_STEPS, "environment_steps": updates * s3.NUM_ENVS * s3.ROLLOUT_STEPS,
        "checkpoint_selection": "fixed_final_update_only", "resume": False,
        "early_stopping": False, "canonical_data_used": False, "training_started": True,
        "role_gate_mode": "none", "graph_encoder": "multi_relation", "commit": git_head(),
        "config": cfg.__dict__,
    }
    (run_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    s3.train_ri_gmappo(cfg)
    checkpoint = run_dir / "actor_critic_latest.pt"
    if not checkpoint.exists():
        raise FileNotFoundError(f"missing final checkpoint: {checkpoint}")
    agent = s3.agent_for_checkpoint(METHOD_SPEC, checkpoint, seed)
    rows = []
    for episode in range(episodes):
        eid = s3r.TAPE_START + episode
        rows.append(s3r.evaluate_episode(agent, METHOD_KEY, seed, eid, "nominal"))
        rows.append(s3r.evaluate_episode(agent, METHOD_KEY, seed, eid, "relay_failure"))
    s3r.write_csv(run_dir / "raw_episode_metrics.csv", rows)
    paired = s3r.paired_rows(rows)
    s3r.write_csv(run_dir / "paired_metrics.csv", paired)
    manifest.update({"status": "completed", "checkpoint": str(checkpoint.resolve().relative_to(ROOT.resolve())), "checkpoint_sha256": sha256(checkpoint), "evaluation_episodes_per_condition": episodes, "evaluation_tape_start": s3r.TAPE_START, "evaluation_success_metric": "success_at_horizon_min_success_step_260"})
    (run_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=ROOT / "results" / "development" / "phase_s3r2_simple_full")
    parser.add_argument("--seed", type=int, choices=SEEDS)
    parser.add_argument("--updates", type=int, default=UPDATES)
    parser.add_argument("--episodes", type=int, default=EPISODES)
    parser.add_argument("--prelaunch", action="store_true")
    parser.add_argument("--integration-smoke", action="store_true")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.prelaunch:
        prelaunch(args.output_root)
        return
    if not args.integration_smoke and not args.execute:
        raise SystemExit("NO-GO: require --prelaunch, --integration-smoke, or --execute")
    if args.integration_smoke:
        run_seed(args.seed or SEEDS[0], args.output_root / "integration_smoke", 1, 2)
        return
    seeds = (args.seed,) if args.seed is not None else SEEDS
    for seed in seeds:
        run_seed(seed, args.output_root, args.updates, args.episodes)


if __name__ == "__main__":
    main()
