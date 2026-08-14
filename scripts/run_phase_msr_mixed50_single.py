"""Run one frozen 1M-step Mixed-50 SG-MAPPO Stage-MSR cell."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import run_phase_fl_single as fl  # noqa: E402


PROTOCOL = "PHASE-MSR-MIXED50-V1"
SEEDS = (1801, 1802)
UPDATES = 3907
NUM_ENVS = 4
ROLLOUT_STEPS = 64
MILESTONE_UPDATES = {1172: "300k", 1953: "500k", 2930: "750k", 3907: "1m"}
MILESTONE_STEPS = {label: update * NUM_ENVS * ROLLOUT_STEPS for update, label in MILESTONE_UPDATES.items()}


def config_hash(cfg: object) -> str:
    payload = dict(cfg.__dict__)
    # These values bind an otherwise identical frozen configuration to one
    # execution cell.  They must not make the two registered MSR cells look
    # like different protocols in the provenance audit.
    for key in (
        "seed",
        "out_dir",
        "device",
        "fixed_condition_mixture_seed",
        "topology_curriculum_seed",
    ):
        payload.pop(key, None)
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def run_one(seed: int, output_root: Path) -> dict:
    fl.UPDATES = UPDATES
    fl.PROTOCOL = PROTOCOL
    out_dir = output_root / "runs" / "mixed50_sg" / f"seed{seed}"
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite: {out_dir}")
    tape = json.loads((output_root / "tape_manifest.json").read_text(encoding="utf-8"))
    out_dir.mkdir(parents=True, exist_ok=False)
    cfg = fl.training_config("fl_nominal_expert", seed, out_dir)
    cfg.updates = UPDATES
    cfg.save_interval = UPDATES
    cfg.save_snapshots = False
    cfg.milestone_updates = MILESTONE_UPDATES
    cfg.fixed_f0_probability = 0.5
    cfg.fixed_condition_mixture_seed = seed
    cfg.fixed_condition_mixture_logging = True
    cfg.topology_curriculum_schedule = "none"
    cfg.topology_curriculum_logging = False
    manifest = {
        "protocol": PROTOCOL, "status": "running", "arm": "mixed50_sg", "seed": seed,
        "training_condition": "fixed_50_50_nominal_f0", "f0_probability": 0.5,
        "f0": {"failed_blue_agent": 1, "failure_start_step": 44, "failure_duration_steps": 80},
        "graph_encoder": "single", "hidden_dim": 115, "parameter_count": 116728,
        "environment_steps": UPDATES * NUM_ENVS * ROLLOUT_STEPS,
        "updates": UPDATES, "num_envs": NUM_ENVS, "rollout_steps": ROLLOUT_STEPS,
        "milestone_updates": MILESTONE_UPDATES, "milestone_steps": MILESTONE_STEPS,
        "checkpoint_selection": "fixed_final_update_only", "milestones_for_curve_only": True,
        "resume": False, "early_stopping": False, "checkpoint_promotion": False,
        "canonical_seeds_used": False, "tape_start": tape["episode_ids"][0],
        "tape_hash": tape["tape_hash"], "episodes_per_condition": len(tape["episode_ids"]),
        "mixed50_config_hash": config_hash(cfg), "config": cfg.__dict__,
    }
    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    fl.train_ri_gmappo(cfg)
    checkpoint = out_dir / "actor_critic_latest.pt"
    if not checkpoint.exists():
        raise FileNotFoundError(checkpoint)
    milestone_hashes = {}
    for label in MILESTONE_STEPS:
        path = out_dir / f"actor_critic_milestone_{label}.pt"
        if not path.exists():
            raise FileNotFoundError(path)
        milestone_hashes[label] = fl.sha256(path)
    mix_rows = []
    with (out_dir / "fixed_condition_mixture_log.csv").open(newline="", encoding="utf-8") as handle:
        import csv
        mix_rows = list(csv.DictReader(handle))
    counts = {"nominal": 0, "f0": 0}
    for row in mix_rows:
        counts[row["condition"]] += 1
    manifest.update({"status": "completed", "checkpoint": str(checkpoint),
                     "checkpoint_sha256": fl.sha256(checkpoint),
                     "milestone_checkpoint_sha256": milestone_hashes,
                     "realized_condition_counts": counts,
                     "realized_condition_total": sum(counts.values())})
    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"status": "completed", "seed": seed,
                      "checkpoint_sha256": manifest["checkpoint_sha256"],
                      "realized_condition_counts": counts}, indent=2))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", choices=SEEDS, type=int, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("results/development/phase_msr_mature_shared_policy"))
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: Stage MSR requires explicit --execute")
    run_one(args.seed, args.output_root)


if __name__ == "__main__":
    main()
