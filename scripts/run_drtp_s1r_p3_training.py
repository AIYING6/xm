"""Run only the two authorized S1-R P3 G/B reference trajectories."""

from __future__ import annotations

import hashlib
import json
import csv
from pathlib import Path
import sys
import time

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.rng_streams import RNGSeedTuple  # noqa: E402
from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOConfig, train_ri_gmappo  # noqa: E402


OUT = ROOT / "results" / "development" / "drtp_s1r_p3"
RUNS = ("R0_G_REF", "R1_B_REF")
UPDATES = 3907
NUM_ENVS = 4
ROLLOUT_STEPS = 64
STEPS = UPDATES * NUM_ENVS * ROLLOUT_STEPS
MILESTONES = {976: "250k", 1953: "500k", 2930: "750k", 3907: "1m"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def frozen() -> tuple[dict, dict]:
    contract = json.loads((ROOT / "artifacts/drtp_s1r_protocol_v2/frozen_contract.json").read_text(encoding="utf-8"))
    rng = json.loads((ROOT / "artifacts/drtp_s1r_protocol_v2/rng_tuples.json").read_text(encoding="utf-8"))
    if contract["selected_G_seed"] != 2001 or contract["selected_B_seed"] != 2002:
        raise RuntimeError("F_P3_FROZEN_ASSET_MISMATCH: G/B")
    if contract["scientific_runs"]["steps_per_run"] != STEPS:
        raise RuntimeError("F_P3_FROZEN_ASSET_MISMATCH: budget")
    return contract, rng


def cfg(seed: int, tuple_values: dict[str, int], out_dir: Path) -> RIGMAPPOConfig:
    return RIGMAPPOConfig(
        env_name="3d_intercept", seed=seed, num_envs=NUM_ENVS, rollout_steps=ROLLOUT_STEPS,
        updates=UPDATES, hidden_dim=115, role_dim=8, intent_dim=8, graph_encoder="single",
        role_gate_mode="none", target_policy="straight", strict_target_sensing=True,
        agent_target_info_bottleneck=True, relay_dependent_task=True,
        business_grounded_geometry=True, communication_range_scale=1.0,
        communication_dropout_prob=0.0, message_delay_steps=0, radar_dropout_prob=0.0,
        min_success_step=260, failed_blue_agent=1, node_failure_start_step=44,
        node_failure_duration_steps=80, evaluation_enabled=False, target_kl=None,
        save_interval=976, save_snapshots=False, milestone_updates=MILESTONES,
        out_dir=str(out_dir), device="cuda" if torch.cuda.is_available() else "cpu",
        topology_curriculum_schedule="none", fixed_f0_probability=None,
        drtp_sampler_mode="drtp", drtp_sampler_seed=tuple_values["topology_seed"],
        drtp_sampler_total_updates=UPDATES, drtp_sampler_logging=True,
        rng_decomposition=True, rng_seed_tuple=tuple_values,
        runtime_state_checkpointing=True, runtime_state_save_interval=976,
    )


def run_one(run: str, seed: int, tuple_values: dict[str, int]) -> dict:
    out = OUT / "runs" / run
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"refusing to overwrite P3 run: {out}")
    out.mkdir(parents=True, exist_ok=False)
    config = cfg(seed, tuple_values, out)
    manifest = {
        "protocol": "DRTP-S1R-P3-G-B-REFERENCE-V1", "status": "running", "run": run,
        "method": "drtp_sg", "seed": seed, "reference_label": "G_REF" if run == "R0_G_REF" else "B_REF",
        "parameter_count": 116728, "updates": UPDATES, "environment_steps": STEPS,
        "num_envs": NUM_ENVS, "rollout_steps": ROLLOUT_STEPS, "milestones": MILESTONES,
        "from_scratch": True, "strict_continuous": True, "resume": False,
        "warm_restart_used": False, "runtime_resume_used": False, "checkpoint_promotion": False,
        "early_stopping": False, "canonical_seeds_used": False, "held_out_seeds_used": False,
        "tape_source": "REL-A0 T0-T4 manifests imported after training",
        "rng_tuple": tuple_values, "runtime_state_checkpointing": True,
        "runtime_state_save_interval": 976, "training_config": config.__dict__,
        "started_at": time.time(), "git_commit": "025bb44",
    }
    write_json(out / "run_manifest.json", manifest)
    train_ri_gmappo(config)
    required = []
    for label in MILESTONES.values():
        required.extend([
            out / f"actor_critic_milestone_{label}.pt",
            out / f"actor_critic_milestone_{label}_training_state.pt",
            out / f"actor_critic_runtime_state_milestone_{label}.pt",
        ])
    required += [out / "actor_critic_latest.pt", out / "actor_critic_training_state_latest.pt",
                 out / "actor_critic_runtime_state_latest.pt", out / "train_log.csv",
                 out / "drtp_topology_sampler_manifest.json", out / "drtp_topology_sampler_log.csv"]
    missing = [str(p) for p in required if not p.exists() or p.stat().st_size == 0]
    if missing:
        manifest.update({"status": "technical_invalid", "missing": missing})
        write_json(out / "run_manifest.json", manifest)
        raise RuntimeError("F_P3_MILESTONE_PERSISTENCE: " + ";".join(missing))
    manifest.update({
        "status": "completed", "finished_at": time.time(),
        "final_checkpoint_sha256": sha256(out / "actor_critic_latest.pt"),
        "final_runtime_checkpoint_sha256": sha256(out / "actor_critic_runtime_state_latest.pt"),
        "milestone_checkpoint_sha256": {label: sha256(out / f"actor_critic_milestone_{label}.pt") for label in MILESTONES.values()},
        "milestone_runtime_checkpoint_sha256": {label: sha256(out / f"actor_critic_runtime_state_milestone_{label}.pt") for label in MILESTONES.values()},
    })
    write_json(out / "run_manifest.json", manifest)
    return manifest


def main() -> None:
    contract, rng = frozen()
    OUT.mkdir(parents=True, exist_ok=True)
    artifact_root = ROOT / "artifacts" / "drtp_s1r_p3"
    artifact_root.mkdir(parents=True, exist_ok=True)
    planned = [
        {"run": "R0_G_REF", "label": "G_REF", "seed": 2001, "rng_tuple": "G"},
        {"run": "R1_B_REF", "label": "B_REF", "seed": 2002, "rng_tuple": "B"},
    ]
    with (artifact_root / "run_manifest.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["run", "label", "seed", "rng_tuple", "budget", "status"])
        writer.writeheader()
        for row in planned:
            writer.writerow({**row, "budget": STEPS, "status": "PLANNED_BEFORE_TRAINING"})
    with (artifact_root / "training_provenance.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["run", "seed", "git_commit", "protocol", "environment_steps", "from_scratch", "runtime_persistence"])
        writer.writeheader()
        for row in planned:
            writer.writerow({"run": row["run"], "seed": row["seed"], "git_commit": "025bb44",
                             "protocol": "DRTP-S1R-P3-G-B-REFERENCE-V1", "environment_steps": STEPS,
                             "from_scratch": True, "runtime_persistence": True})
    (ROOT / "docs" / "DRTP_S1R_P3_RUN_MANIFEST.md").write_text(
        "# DRTP S1-R P3 Run Manifest\n\n"
        "This manifest is frozen before scientific training. Only the two authorized reference runs are present.\n\n"
        "| Run | Reference | Seed | Budget | RNG tuple |\n|---|---|---:|---:|---|\n"
        "| R0_G_REF | G_REF | 2001 | 1,000,192 | RNG_G |\n"
        "| R1_B_REF | B_REF | 2002 | 1,000,192 | RNG_B |\n\n"
        "P4 interventions, new seeds, held-out, and canonical runs are not authorized.\n",
        encoding="utf-8",
    )
    rows = []
    for run, label, seed in (("R0_G_REF", "G", 2001), ("R1_B_REF", "B", 2002)):
        values = {k: int(v) for k, v in rng["tuples"][label].items() if k != "master_seed"}
        values = RNGSeedTuple(**values).__dict__
        rows.append(run_one(run, seed, values))
    write_json(OUT / "p3_training_completion.json", {
        "protocol": "DRTP-S1R-P3-G-B-REFERENCE-V1", "status": "completed",
        "scientific_runs": 2, "scientific_env_steps": 2 * STEPS,
        "runs": rows, "P4_started": False, "heldout_started": False,
        "canonical_seeds_used": False, "contract_protocol": contract["protocol"],
    })


if __name__ == "__main__":
    main()
