"""Run the frozen seven-trajectory DRTP-SEED-S1-A screen.

This launcher is intentionally sequential: it never changes the registered
RNG tuple, budget, or run set based on intermediate performance.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
import time
from dataclasses import asdict
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.rng_streams import RNGStreams
from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOConfig, train_ri_gmappo


UPDATES = 5859
NUM_ENVS = 4
ROLLOUT_STEPS = 64
STEPS = UPDATES * NUM_ENVS * ROLLOUT_STEPS
MILESTONES = {976: "250k", 1953: "500k", 2930: "750k", 3907: "1m", 4883: "1250k", 5859: "1500k"}
TAPE_START = 440000
RUNS = ("R0_G_REFERENCE", "R1_B_REFERENCE", "R2_I_INIT", "R3_I_ENV", "R4_I_ACTION", "R5_I_MINIBATCH", "R6_I_TOPOLOGY")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tuples() -> dict[str, dict[str, int]]:
    good = asdict(RNGStreams.from_master(1901).seeds)
    bad = asdict(RNGStreams.from_master(1902).seeds)
    # Evaluation randomness is fixed across the entire intervention matrix.
    bad["eval_seed"] = good["eval_seed"]
    replacements = {
        "R2_I_INIT": "init_seed",
        "R3_I_ENV": "env_seed",
        "R4_I_ACTION": "action_seed",
        "R5_I_MINIBATCH": "minibatch_seed",
        "R6_I_TOPOLOGY": "topology_seed",
    }
    result = {"R0_G_REFERENCE": good, "R1_B_REFERENCE": bad}
    for run, field in replacements.items():
        value = dict(bad)
        value[field] = good[field]
        result[run] = value
    return result


def validate_matrix(matrix: dict[str, dict[str, int]]) -> None:
    required = {"init_seed", "env_seed", "action_seed", "minibatch_seed", "topology_seed", "eval_seed"}
    if set(matrix) != set(RUNS):
        raise RuntimeError("S1-A matrix does not contain exactly seven registered runs")
    for run, values in matrix.items():
        if set(values) != required:
            raise RuntimeError(f"incomplete RNG tuple for {run}")
    bad = matrix["R1_B_REFERENCE"]
    for run, field in {
        "R2_I_INIT": "init_seed", "R3_I_ENV": "env_seed", "R4_I_ACTION": "action_seed",
        "R5_I_MINIBATCH": "minibatch_seed", "R6_I_TOPOLOGY": "topology_seed",
    }.items():
        if sum(matrix[run][key] != bad[key] for key in required) != 1 or matrix[run][field] == bad[field]:
            raise RuntimeError(f"{run} is not a one-factor intervention from B_REFERENCE")
        if matrix[run]["eval_seed"] != bad["eval_seed"]:
            raise RuntimeError(f"evaluation seed changed for {run}")


def config(run: str, values: dict[str, int], out_dir: Path) -> RIGMAPPOConfig:
    training_seed = 1901 if run == "R0_G_REFERENCE" else 1902
    return RIGMAPPOConfig(
        env_name="3d_intercept", seed=training_seed, num_envs=NUM_ENVS,
        rollout_steps=ROLLOUT_STEPS, updates=UPDATES, hidden_dim=115,
        role_dim=8, intent_dim=8, graph_encoder="single", role_gate_mode="none",
        target_policy="straight", strict_target_sensing=True,
        agent_target_info_bottleneck=True, relay_dependent_task=True,
        business_grounded_geometry=True, communication_range_scale=1.0,
        communication_dropout_prob=0.0, message_delay_steps=0, radar_dropout_prob=0.0,
        min_success_step=260, failed_blue_agent=-1, node_failure_start_step=0,
        node_failure_duration_steps=0, evaluation_enabled=False,
        target_kl=None, save_interval=UPDATES, save_snapshots=False,
        milestone_updates=MILESTONES, out_dir=str(out_dir),
        device="cuda" if torch.cuda.is_available() else "cpu",
        topology_curriculum_schedule="none", fixed_f0_probability=None,
        drtp_sampler_mode="drtp", drtp_sampler_seed=values["topology_seed"],
        drtp_sampler_logging=True, rng_decomposition=True,
        rng_seed_tuple=values, runtime_state_checkpointing=True,
        runtime_state_save_interval=UPDATES,
    )


def run_one(run: str, values: dict[str, int], output_root: Path) -> dict:
    out_dir = output_root / "runs" / run
    if out_dir.exists() and any(out_dir.iterdir()):
        existing_path = out_dir / "run_manifest.json"
        existing = json.loads(existing_path.read_text(encoding="utf-8")) if existing_path.exists() else {}
        if existing.get("status") == "completed":
            raise FileExistsError(f"refusing to overwrite completed run {out_dir}")
        invalid_root = output_root / "technical_invalid"
        invalid_root.mkdir(parents=True, exist_ok=True)
        suffix = 1
        archived = invalid_root / f"{run}_attempt{suffix}"
        while archived.exists():
            suffix += 1
            archived = invalid_root / f"{run}_attempt{suffix}"
        shutil.move(str(out_dir), str(archived))
        print(json.dumps({"technical_invalid_archived": str(archived)}), flush=True)
    out_dir.mkdir(parents=True, exist_ok=False)
    cfg = config(run, values, out_dir)
    manifest = {
        "protocol": "DRTP-SEED-S1-A-V1", "run": run, "status": "running",
        "rng_tuple": values, "steps": STEPS, "updates": UPDATES,
        "num_envs": NUM_ENVS, "rollout_steps": ROLLOUT_STEPS,
        "milestones": MILESTONES, "tape_namespace": "440000-440099",
        "post_hoc_development_diagnostic": True, "from_scratch": True,
        "checkpoint_selection": "fixed_milestones_only; no promotion",
        "canonical_seeds_used": False, "heldout_used": False,
        "config": cfg.__dict__, "started_at": time.time(),
    }
    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    train_ri_gmappo(cfg)
    final = out_dir / "actor_critic_latest.pt"
    if not final.exists():
        raise FileNotFoundError(final)
    manifest.update({
        "status": "completed", "finished_at": time.time(),
        "checkpoint_sha256": sha256(final),
        "milestone_checkpoint_sha256": {
            label: sha256(out_dir / f"actor_critic_milestone_{label}.pt")
            for label in MILESTONES.values()
        },
    })
    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: S1-A long-run execution requires explicit --execute")
    tape = json.loads((ROOT / "artifacts/drtp_seed_s1/diagnostic_tape_manifest.json").read_text(encoding="utf-8"))
    if tape["episode_ids"] != list(range(TAPE_START, TAPE_START + 100)):
        raise RuntimeError("S1 diagnostic tape mismatch")
    matrix = tuples()
    validate_matrix(matrix)
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "s1a_rng_intervention_matrix.json").write_text(json.dumps(matrix, indent=2) + "\n", encoding="utf-8")
    results = []
    for run in RUNS:
        results.append(run_one(run, matrix[run], args.output_root))
    (args.output_root / "s1a_completion.json").write_text(json.dumps({"status": "completed", "runs": results}, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"status": "completed", "runs": RUNS, "total_steps": len(RUNS) * STEPS}, indent=2))


if __name__ == "__main__":
    main()
