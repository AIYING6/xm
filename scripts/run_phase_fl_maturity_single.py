"""Run one frozen Phase-FL training-maturity expert to the 1M-step ceiling."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import run_phase_fl_single as fl  # noqa: E402


PROTOCOL = "PHASE-FL-MATURITY-V1"
SEEDS = (1801, 1802)
UPDATES = 3907
NUM_ENVS = 4
ROLLOUT_STEPS = 64
MILESTONE_UPDATES = {1172: "300k", 1953: "500k", 2930: "750k", 3907: "1m"}
MILESTONE_STEPS = {label: update * NUM_ENVS * ROLLOUT_STEPS for update, label in MILESTONE_UPDATES.items()}


def run_one(arm: str, seed: int, output_root: Path) -> dict:
    fl.UPDATES = UPDATES
    fl.PROTOCOL = PROTOCOL
    out_dir = output_root / "runs" / arm / f"seed{seed}"
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite: {out_dir}")
    tape = json.loads((output_root / "tape_manifest.json").read_text(encoding="utf-8"))
    out_dir.mkdir(parents=True, exist_ok=False)
    cfg = fl.training_config(arm, seed, out_dir)
    cfg.updates = UPDATES
    cfg.save_interval = UPDATES
    cfg.save_snapshots = False
    cfg.milestone_updates = MILESTONE_UPDATES
    spec = fl.ARMS[arm]
    manifest = {
        "protocol": PROTOCOL, "status": "running", "arm": arm, "seed": seed,
        "training_condition": "nominal" if arm == "fl_nominal_expert" else "F0",
        "failure_spec": spec, "graph_encoder": "single", "hidden_dim": 115,
        "parameter_count": 116728, "environment_steps": UPDATES * NUM_ENVS * ROLLOUT_STEPS,
        "updates": UPDATES, "num_envs": NUM_ENVS, "rollout_steps": ROLLOUT_STEPS,
        "milestone_updates": MILESTONE_UPDATES, "milestone_steps": MILESTONE_STEPS,
        "checkpoint_selection": "fixed_final_update_only", "milestones_for_curve_only": True,
        "resume": False, "early_stopping": False, "checkpoint_promotion": False,
        "canonical_seeds_used": False, "tape_start": fl.TAPE_START,
        "tape_hash": tape["tape_hash"], "episodes_per_condition": fl.EPISODES,
        "config": cfg.__dict__,
    }
    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    fl.train_ri_gmappo(cfg)
    checkpoint = out_dir / "actor_critic_latest.pt"
    if not checkpoint.exists():
        raise FileNotFoundError(checkpoint)
    agent = fl.build_agent({"graph_encoder": "single", "hidden_dim": 115}, checkpoint, seed)
    fl.evaluate(agent, arm, seed, out_dir)
    milestone_hashes = {}
    for label in MILESTONE_STEPS:
        path = out_dir / f"actor_critic_milestone_{label}.pt"
        if not path.exists():
            raise FileNotFoundError(path)
        milestone_hashes[label] = fl.sha256(path)
    manifest.update({"status": "completed", "checkpoint": str(checkpoint),
                     "checkpoint_sha256": fl.sha256(checkpoint),
                     "milestone_checkpoint_sha256": milestone_hashes,
                     "raw_rows": 100, "paired_rows": 50})
    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"status": "completed", "arm": arm, "seed": seed,
                      "checkpoint_sha256": manifest["checkpoint_sha256"],
                      "milestone_checkpoint_sha256": milestone_hashes}, indent=2))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=tuple(fl.ARMS), required=True)
    parser.add_argument("--seed", choices=SEEDS, type=int, required=True)
    parser.add_argument("--output-root", type=Path, default=Path("results/development/phase_fl_maturity"))
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: Phase FL maturity requires explicit --execute")
    run_one(args.arm, args.seed, args.output_root)


if __name__ == "__main__":
    main()
