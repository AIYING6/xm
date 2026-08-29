"""Execute exactly one future-authorized Stable-DRTP R1 trajectory."""
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
from algorithms.ri_gmappo.simple_ri_gmappo import train_ri_gmappo  # noqa: E402
import run_drtp_sg_strict_10m_single as strict  # noqa: E402

PROTOCOL = "DRTP-STABLE-R1-DEVELOPMENT-V1"
SEEDS, UPDATES, NUM_ENVS, ROLLOUT_STEPS = (3001, 3002, 3003, 3004, 3005), 3907, 4, 64
ARMS = {"utr_sg": "utr", "drtp_sg": "drtp", "conservative_drtp_sg": "conservative_drtp"}
MILESTONES = {976: "250k", 1953: "500k", 2930: "750k", 3907: "1m"}
TAPE, FREEZE = ROOT / "configs" / "drtp_stable_r1_development_tape.json", ROOT / "configs" / "drtp_stabilization_s0_freeze.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def config(arm: str, seed: int, out: Path):
    template = strict.training_config("utr_sg", strict.SEEDS[0], out)
    return replace(template, seed=seed, updates=UPDATES, save_interval=976,
                   milestone_updates=MILESTONES, out_dir=str(out),
                   drtp_sampler_mode=ARMS[arm], drtp_sampler_seed=seed,
                   drtp_sampler_total_updates=UPDATES, runtime_state_checkpointing=True,
                   runtime_state_save_interval=976, evaluation_enabled=False)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--arm", choices=ARMS, required=True)
    p.add_argument("--seed", type=int, choices=SEEDS, required=True)
    p.add_argument("--output-root", type=Path, required=True)
    p.add_argument("--execute", action="store_true")
    a = p.parse_args()
    if not a.execute:
        raise SystemExit("--execute required")
    tape, freeze = json.loads(TAPE.read_text(encoding="utf-8")), json.loads(FREEZE.read_text(encoding="utf-8"))
    out = a.output_root / "runs" / a.arm / f"seed{a.seed}"
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"refusing overwrite/rerun: {out}")
    out.mkdir(parents=True, exist_ok=False)
    cfg = config(a.arm, a.seed, out)
    manifest = {"protocol": PROTOCOL, "status": "running", "commit": commit(), "arm": a.arm,
                "sampler_mode": ARMS[a.arm], "seed": a.seed, "updates": UPDATES,
                "environment_steps": UPDATES * NUM_ENVS * ROLLOUT_STEPS,
                "num_envs": NUM_ENVS, "rollout_steps": ROLLOUT_STEPS,
                "milestone_updates": MILESTONES, "from_scratch": True,
                "early_stopping": False, "checkpoint_promotion": False,
                "seed_replacement": False, "rerun_authorized": False,
                "continuation_authorized": False, "parameter_count": 116728,
                "tape_hash": tape["tape_hash"], "delta_q_l1": freeze["delta_q_l1"],
                "uniform_anchor": freeze["s2_uniform_anchor"], "adaptive_mass": freeze["s2_adaptive_mass"],
                "config": cfg.__dict__, "started_at": time.time()}
    path = out / "run_manifest.json"
    path.write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    try:
        train_ri_gmappo(cfg)
        required = [out / "actor_critic_latest.pt", out / "actor_critic_runtime_state_latest.pt",
                    out / "train_log.csv", out / "drtp_topology_sampler_log.csv"]
        for label in MILESTONES.values():
            required += [out / f"actor_critic_milestone_{label}.pt", out / f"actor_critic_runtime_state_milestone_{label}.pt"]
        missing = [str(x) for x in required if not x.exists() or x.stat().st_size == 0]
        if missing:
            raise RuntimeError("R1 persistence failure: " + "; ".join(missing))
        manifest.update({"status": "completed", "finished_at": time.time(), "final_checkpoint_sha256": sha256(out / "actor_critic_latest.pt")})
    except Exception as exc:
        manifest.update({"status": "technical_invalid", "finished_at": time.time(), "error": repr(exc)})
        path.write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
        raise
    path.write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
