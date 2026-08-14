"""Train one frozen UTR-SG or DRTP-SG development trajectory from scratch."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOConfig, train_ri_gmappo  # noqa: E402


PROTOCOL = "DRTP-SG-DEVELOPMENT-TRAINING-V1"
SEEDS = (1901, 1902)
ARMS = {"utr_sg": "utr", "drtp_sg": "drtp"}
NUM_ENVS, ROLLOUT_STEPS = 4, 64
BUDGETS = {
    "1m": {"updates": 3907, "milestones": {1954: "500k", 2930: "750k", 3907: "1m"}},
    "2m": {"updates": 7813, "milestones": {5859: "1500k", 7813: "2m"}},
    "3m": {"updates": 11719, "milestones": {9766: "2500k", 11719: "3m"}},
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def config_hash(cfg: RIGMAPPOConfig) -> str:
    payload = dict(cfg.__dict__)
    for key in ("seed", "out_dir", "device", "drtp_sampler_seed"):
        payload.pop(key, None)
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def training_config(arm: str, seed: int, out_dir: Path, budget: str) -> RIGMAPPOConfig:
    cell = BUDGETS[budget]
    return RIGMAPPOConfig(
        env_name="3d_intercept", seed=seed, num_envs=NUM_ENVS,
        rollout_steps=ROLLOUT_STEPS, updates=cell["updates"], hidden_dim=115,
        role_dim=8, intent_dim=8, graph_encoder="single", role_gate_mode="none",
        target_policy="straight", strict_target_sensing=True,
        agent_target_info_bottleneck=True, relay_dependent_task=True,
        business_grounded_geometry=True, communication_range_scale=1.0,
        communication_dropout_prob=0.0, message_delay_steps=0,
        radar_dropout_prob=0.0, min_success_step=260,
        failed_blue_agent=-1, node_failure_start_step=0, node_failure_duration_steps=0,
        evaluation_enabled=False, target_kl=None, save_interval=cell["updates"],
        save_snapshots=False, milestone_updates=cell["milestones"], out_dir=str(out_dir),
        device="cuda" if torch.cuda.is_available() else "cpu",
        topology_curriculum_schedule="none", topology_curriculum_logging=False,
        fixed_f0_probability=None, drtp_sampler_mode=ARMS[arm],
        drtp_sampler_seed=seed, drtp_sampler_logging=True,
    )


def run_one(arm: str, seed: int, budget: str, output_root: Path) -> dict:
    tape = json.loads((output_root / "tape_manifest.json").read_text(encoding="utf-8"))
    if tape.get("episode_ids") != list(range(420000, 420100)) or tape.get("canonical") is not False:
        raise RuntimeError("missing or invalid frozen 420k development tape")
    out_dir = output_root / "runs" / budget / arm / f"seed{seed}"
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=False)
    cfg = training_config(arm, seed, out_dir, budget)
    updates = BUDGETS[budget]["updates"]
    manifest = {
        "protocol": PROTOCOL, "status": "running", "arm": arm, "sampler_mode": ARMS[arm],
        "seed": seed, "budget": budget, "updates": updates,
        "environment_steps": updates * NUM_ENVS * ROLLOUT_STEPS,
        "num_envs": NUM_ENVS, "rollout_steps": ROLLOUT_STEPS,
        "milestone_updates": BUDGETS[budget]["milestones"],
        "milestones_for_curve_only": True, "checkpoint_selection": "fixed_final_budget_only",
        "from_scratch": True, "resume": False, "early_stopping": False,
        "checkpoint_promotion": False, "seed_exclusion": False,
        "canonical_seeds_used": False, "graph_encoder": "single", "parameter_count": 116728,
        "nominal_anchor": 0.5, "topology_group_universe": ["N", "F0", "TE", "TL", "DS", "DL", "CP"],
        "tape_hash": tape["tape_hash"], "tape_start": 420000,
        "config_hash": config_hash(cfg), "config": cfg.__dict__,
    }
    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    train_ri_gmappo(cfg)
    final_checkpoint = out_dir / "actor_critic_latest.pt"
    if not final_checkpoint.exists():
        raise FileNotFoundError(final_checkpoint)
    milestone_hashes = {}
    for label in BUDGETS[budget]["milestones"].values():
        checkpoint = out_dir / f"actor_critic_milestone_{label}.pt"
        if not checkpoint.exists():
            raise FileNotFoundError(checkpoint)
        milestone_hashes[label] = sha256(checkpoint)
    sampler_manifest = json.loads((out_dir / "drtp_topology_sampler_manifest.json").read_text(encoding="utf-8"))
    sampler_log = out_dir / "drtp_topology_sampler_log.csv"
    if not sampler_log.exists():
        raise FileNotFoundError(sampler_log)
    manifest.update({
        "status": "completed", "final_checkpoint": str(final_checkpoint),
        "checkpoint_sha256": sha256(final_checkpoint), "milestone_checkpoint_sha256": milestone_hashes,
        "sampler_manifest_hash": hashlib.sha256(json.dumps(sampler_manifest, sort_keys=True).encode("utf-8")).hexdigest(),
        "sampler_log": str(sampler_log),
    })
    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"status": "completed", "arm": arm, "seed": seed, "budget": budget,
                      "checkpoint_sha256": manifest["checkpoint_sha256"]}, indent=2))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=tuple(ARMS), required=True)
    parser.add_argument("--seed", choices=SEEDS, type=int, required=True)
    parser.add_argument("--budget", choices=tuple(BUDGETS), required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: explicit --execute is required")
    run_one(args.arm, args.seed, args.budget, args.output_root)


if __name__ == "__main__":
    main()
