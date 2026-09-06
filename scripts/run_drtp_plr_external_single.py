"""Run one frozen 10M UTR, Original-DRTP, or PLR-style trajectory."""
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
from scripts.drtp_plr_external_contracts import ARMS, FREEZE, MILESTONES, NUM_ENVS, ROLLOUT, SEEDS, STEPS, UPDATES, tape_payload  # noqa: E402

PROTOCOL = "DRTP-PLR-EXTERNAL-FORMAL-TRAINING-V1"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def source_commit() -> str:
    try: return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError): return "package-provenance-only"


def config(arm: str, seed: int, output: Path) -> RIGMAPPOConfig:
    return RIGMAPPOConfig(
        env_name="3d_intercept", seed=seed, num_envs=NUM_ENVS, rollout_steps=ROLLOUT, updates=UPDATES,
        hidden_dim=115, role_dim=8, intent_dim=8, graph_encoder="single", role_gate_mode="none",
        target_policy="straight", strict_target_sensing=True, agent_target_info_bottleneck=True,
        relay_dependent_task=True, business_grounded_geometry=True, communication_range_scale=1.0,
        communication_dropout_prob=0.0, message_delay_steps=0, radar_dropout_prob=0.0,
        min_success_step=260, failed_blue_agent=-1, node_failure_start_step=0, node_failure_duration_steps=0,
        evaluation_enabled=False, target_kl=None, save_interval=UPDATES, save_snapshots=False,
        milestone_updates=MILESTONES, out_dir=str(output), device="cuda" if torch.cuda.is_available() else "cpu",
        topology_curriculum_schedule="none", topology_curriculum_logging=False, fixed_f0_probability=None,
        drtp_sampler_mode=ARMS[arm], drtp_sampler_seed=seed, drtp_sampler_logging=True,
        runtime_state_checkpointing=True, runtime_state_save_interval=UPDATES,
    )


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--arm", choices=tuple(ARMS), required=True); parser.add_argument("--seed", type=int, required=True); parser.add_argument("--output-root", type=Path, required=True); parser.add_argument("--execute", action="store_true"); args = parser.parse_args()
    if not args.execute: raise SystemExit("explicit --execute is required")
    if args.seed not in SEEDS: raise ValueError("seed is outside frozen PLR comparator cohort")
    tape = json.loads((args.output_root / "tape" / "tape_manifest.json").read_text(encoding="utf-8"))
    if tape != tape_payload(): raise RuntimeError("invalid frozen PLR endpoint tape")
    run = args.output_root / "runs" / args.arm / f"seed{args.seed}"
    if run.exists(): raise FileExistsError(f"refusing to overwrite {run}")
    run.mkdir(parents=True); cfg = config(args.arm, args.seed, run)
    manifest = {"protocol": PROTOCOL, "status": "running", "arm": args.arm, "seed": args.seed, "sampler_mode": ARMS[args.arm], "updates": UPDATES, "environment_steps": STEPS, "from_scratch": True, "resume": False, "early_stopping": False, "checkpoint_promotion": False, "evaluation_during_training": False, "endpoint_tape_hash": tape["tape_hash"], "endpoint_tape_not_read_by_training": True, "freeze_sha256": digest(FREEZE), "source_commit": source_commit(), "config": cfg.__dict__}
    (run / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    train_ri_gmappo(cfg)
    required = [run / "actor_critic_latest.pt", run / "actor_critic_runtime_state_latest.pt"]
    required += [run / f"actor_critic_milestone_{name}.pt" for name in MILESTONES.values()]
    required += [run / f"actor_critic_runtime_state_milestone_{name}.pt" for name in MILESTONES.values()]
    if ARMS[args.arm] == "plr": required += [run / "plr_topology_sampler_manifest.json", run / "plr_topology_sampler_log.csv"]
    else: required += [run / "drtp_topology_sampler_manifest.json", run / "drtp_topology_sampler_log.csv"]
    if missing := [str(path) for path in required if not path.is_file()]: raise FileNotFoundError("missing frozen training artifact: " + ", ".join(missing))
    manifest.update({"status": "completed", "checkpoint_sha256": digest(run / "actor_critic_latest.pt"), "runtime_state_sha256": digest(run / "actor_critic_runtime_state_latest.pt")})
    (run / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"status": "completed", "arm": args.arm, "seed": args.seed}, indent=2), flush=True)


if __name__ == "__main__": main()
