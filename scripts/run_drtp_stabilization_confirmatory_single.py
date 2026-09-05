"""Run one frozen 10M final-method confirmation trajectory."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOConfig, train_ri_gmappo  # noqa: E402
from scripts.drtp_stabilization_confirmation_contracts import ARMS, cohort_names, cohort_spec  # noqa: E402


DEFAULT = cohort_spec("A")
PROTOCOL = DEFAULT["training_protocol"]
FREEZE = DEFAULT["freeze_path"]
SEEDS = DEFAULT["seeds"]
UPDATES, NUM_ENVS, ROLLOUT = 39063, 4, 64
STEPS = UPDATES * NUM_ENVS * ROLLOUT
MILESTONES = {3907: "1m", 11719: "3m", 39063: "10m"}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def source_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "package-provenance-only"


def load_tape(output_root: Path, spec: dict) -> dict:
    tape = json.loads((output_root / "tape" / "tape_manifest.json").read_text(encoding="utf-8"))
    if (tape.get("protocol") != spec["tape_protocol"] or tape.get("episode_ids") != spec["episode_ids"]
            or tape.get("training_access") != "forbidden" or tape.get("cohort") != spec["cohort"]):
        raise RuntimeError("invalid frozen cohort tape")
    return tape


def training_config(arm: str, seed: int, out_dir: Path) -> RIGMAPPOConfig:
    mode, alpha = ARMS[arm]
    return RIGMAPPOConfig(
        env_name="3d_intercept", seed=seed, num_envs=NUM_ENVS, rollout_steps=ROLLOUT, updates=UPDATES,
        hidden_dim=115, role_dim=8, intent_dim=8, graph_encoder="single", role_gate_mode="none",
        target_policy="straight", strict_target_sensing=True, agent_target_info_bottleneck=True,
        relay_dependent_task=True, business_grounded_geometry=True, communication_range_scale=1.0,
        communication_dropout_prob=0.0, message_delay_steps=0, radar_dropout_prob=0.0,
        min_success_step=260, failed_blue_agent=-1, node_failure_start_step=0, node_failure_duration_steps=0,
        evaluation_enabled=False, target_kl=None, save_interval=UPDATES, save_snapshots=False,
        milestone_updates=MILESTONES, out_dir=str(out_dir), device="cuda" if torch.cuda.is_available() else "cpu",
        topology_curriculum_schedule="none", topology_curriculum_logging=False, fixed_f0_probability=None,
        drtp_sampler_mode=mode, drtp_sampler_seed=seed,
        drtp_sampler_anchor_alpha=1.0 if alpha is None else alpha, drtp_sampler_logging=True,
        runtime_state_checkpointing=True, runtime_state_save_interval=UPDATES,
    )


def run_one(arm: str, seed: int, output_root: Path, cohort: str = "A") -> dict:
    spec = cohort_spec(cohort)
    if arm not in ARMS or seed not in spec["seeds"]:
        raise ValueError("unfrozen cohort arm or seed")
    tape = load_tape(output_root, spec)
    out = output_root / "runs" / arm / f"seed{seed}"
    if out.exists():
        raise FileExistsError(f"refusing to overwrite {out}")
    out.mkdir(parents=True)
    config = training_config(arm, seed, out)
    manifest = {
        "protocol": spec["training_protocol"], "cohort": cohort, "status": "running", "arm": arm, "seed": seed,
        "sampler_mode": ARMS[arm][0], "anchor_alpha": ARMS[arm][1], "updates": UPDATES,
        "environment_steps": STEPS, "num_envs": NUM_ENVS, "rollout_steps": ROLLOUT,
        "milestone_updates": MILESTONES, "from_scratch": True, "resume": False,
        "early_stopping": False, "checkpoint_promotion": False, "seed_replacement": False,
        "evaluation_during_training": False, "fixed_final_budget_only": True,
        "tape_hash": tape["tape_hash"], "tape_not_read_by_training": True,
        "freeze_sha256": digest(spec["freeze_path"]), "source_commit": source_commit(), "config": config.__dict__,
    }
    (out / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    train_ri_gmappo(config)
    required = [out / "actor_critic_latest.pt", out / "actor_critic_runtime_state_latest.pt",
                out / "drtp_topology_sampler_manifest.json", out / "drtp_topology_sampler_log.csv"]
    for label in MILESTONES.values():
        required.extend((out / f"actor_critic_milestone_{label}.pt", out / f"actor_critic_runtime_state_milestone_{label}.pt"))
    if missing := [str(path) for path in required if not path.is_file()]:
        raise FileNotFoundError("missing confirmation artifacts: " + ", ".join(missing))
    manifest.update({
        "status": "completed", "checkpoint_sha256": digest(out / "actor_critic_latest.pt"),
        "runtime_state_sha256": digest(out / "actor_critic_runtime_state_latest.pt"),
        "sampler_manifest_sha256": digest(out / "drtp_topology_sampler_manifest.json"),
    })
    (out / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"status": "completed", "arm": arm, "seed": seed}, indent=2))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cohort", choices=cohort_names(), default="A")
    parser.add_argument("--arm", choices=tuple(ARMS), required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("explicit --execute is required")
    run_one(args.arm, args.seed, args.output_root, args.cohort)


if __name__ == "__main__":
    main()
