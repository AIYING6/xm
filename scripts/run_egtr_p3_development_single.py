"""Run one frozen EGTR P3 1M development trajectory from scratch."""
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

PROTOCOL = "EGTR-P3-DEVELOPMENT-TRAINING-V1"
SEEDS = (2501, 2502, 2503)
ARMS = {"utr_sg": "utr", "drtp_sg": "drtp", "egtr_sg": "egtr"}
NUM_ENVS, ROLLOUT_STEPS = 4, 64
UPDATES = 3907
MILESTONES = {1954: "500k", 2930: "750k", 3907: "1m"}
TAPE_START, TAPE_END = 520000, 520099


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "package-provenance-only"


def config_hash(cfg: RIGMAPPOConfig) -> str:
    payload = dict(cfg.__dict__)
    for key in ("seed", "out_dir", "device", "drtp_sampler_seed"):
        payload.pop(key, None)
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_tape(output_root: Path) -> dict:
    path = output_root / "tape" / "tape_manifest.json"
    if not path.exists():
        raise FileNotFoundError(f"missing frozen P3 tape manifest: {path}")
    tape = json.loads(path.read_text(encoding="utf-8"))
    if tape.get("protocol") != "EGTR-P3-DEVELOPMENT-TAPE-V1":
        raise RuntimeError("unexpected P3 tape protocol")
    if tape.get("episode_ids") != list(range(TAPE_START, TAPE_END + 1)):
        raise RuntimeError("unexpected P3 tape namespace")
    if tape.get("canonical") is not False or tape.get("development_only") is not True:
        raise RuntimeError("P3 tape must be development-only and non-canonical")
    return tape


def training_config(arm: str, seed: int, out_dir: Path) -> RIGMAPPOConfig:
    return RIGMAPPOConfig(
        env_name="3d_intercept", seed=seed, num_envs=NUM_ENVS,
        rollout_steps=ROLLOUT_STEPS, updates=UPDATES, hidden_dim=115,
        role_dim=8, intent_dim=8, graph_encoder="single", role_gate_mode="none",
        target_policy="straight", strict_target_sensing=True,
        agent_target_info_bottleneck=True, relay_dependent_task=True,
        business_grounded_geometry=True, communication_range_scale=1.0,
        communication_dropout_prob=0.0, message_delay_steps=0,
        radar_dropout_prob=0.0, min_success_step=260,
        failed_blue_agent=-1, node_failure_start_step=0, node_failure_duration_steps=0,
        evaluation_enabled=False, target_kl=None, save_interval=UPDATES,
        save_snapshots=False, milestone_updates=MILESTONES, out_dir=str(out_dir),
        device="cuda" if torch.cuda.is_available() else "cpu",
        topology_curriculum_schedule="none", topology_curriculum_logging=False,
        fixed_f0_probability=None, drtp_sampler_mode=ARMS[arm],
        drtp_sampler_seed=seed, drtp_sampler_logging=True,
        runtime_state_checkpointing=True, runtime_state_save_interval=UPDATES,
    )


def run_one(arm: str, seed: int, output_root: Path) -> dict:
    if arm not in ARMS or seed not in SEEDS:
        raise ValueError(f"unsupported P3 cell: {arm}/seed{seed}")
    tape = load_tape(output_root)
    out_dir = output_root / "runs" / arm / f"seed{seed}"
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite non-empty run: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=False)
    cfg = training_config(arm, seed, out_dir)
    manifest = {
        "protocol": PROTOCOL, "status": "running", "arm": arm,
        "sampler_mode": ARMS[arm], "seed": seed, "updates": UPDATES,
        "environment_steps": UPDATES * NUM_ENVS * ROLLOUT_STEPS,
        "num_envs": NUM_ENVS, "rollout_steps": ROLLOUT_STEPS,
        "milestone_updates": MILESTONES, "milestones_for_curve_only": True,
        "checkpoint_selection": "fixed_final_budget_only", "from_scratch": True,
        "resume": False, "early_stopping": False, "checkpoint_promotion": False,
        "seed_exclusion": False, "canonical_seeds_used": False,
        "runtime_state_persistence_from_step_zero": True,
        "graph_encoder": "single", "parameter_count": 116728,
        "nominal_anchor": 0.5,
        "topology_group_universe": ["N", "F0", "TE", "TL", "DS", "DL", "CP"],
        "tape_hash": tape["tape_hash"], "tape_start": TAPE_START, "tape_end": TAPE_END,
        "source_commit": source_commit(), "config_hash": config_hash(cfg),
        "config": cfg.__dict__,
    }
    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    train_ri_gmappo(cfg)
    final_checkpoint = out_dir / "actor_critic_latest.pt"
    if not final_checkpoint.exists():
        raise FileNotFoundError(final_checkpoint)
    milestone_hashes = {}
    runtime_hashes = {}
    for label in MILESTONES.values():
        checkpoint = out_dir / f"actor_critic_milestone_{label}.pt"
        runtime = out_dir / f"actor_critic_runtime_state_milestone_{label}.pt"
        if not checkpoint.exists() or not runtime.exists():
            raise FileNotFoundError(f"missing milestone/runtime checkpoint for {label}")
        milestone_hashes[label] = sha256(checkpoint)
        runtime_hashes[label] = sha256(runtime)
    runtime_final = out_dir / "actor_critic_runtime_state_latest.pt"
    sampler_manifest_path = out_dir / "drtp_topology_sampler_manifest.json"
    sampler_log = out_dir / "drtp_topology_sampler_log.csv"
    for path in (runtime_final, sampler_manifest_path, sampler_log):
        if not path.exists():
            raise FileNotFoundError(path)
    manifest.update({
        "status": "completed", "final_checkpoint": str(final_checkpoint),
        "checkpoint_sha256": sha256(final_checkpoint),
        "runtime_state_latest_sha256": sha256(runtime_final),
        "milestone_checkpoint_sha256": milestone_hashes,
        "milestone_runtime_state_sha256": runtime_hashes,
        "sampler_manifest_sha256": sha256(sampler_manifest_path),
        "sampler_log": str(sampler_log),
    })
    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"status": "completed", "arm": arm, "seed": seed,
                      "checkpoint_sha256": manifest["checkpoint_sha256"]}, indent=2))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=tuple(ARMS), required=True)
    parser.add_argument("--seed", choices=SEEDS, type=int, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: explicit --execute is required")
    run_one(args.arm, args.seed, args.output_root)


if __name__ == "__main__":
    main()
