"""Run exactly one newly authorized Conservative-DRTP S2 trajectory."""
from __future__ import annotations

import argparse, hashlib, json, subprocess, sys, time
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
from algorithms.ri_gmappo.simple_ri_gmappo import train_ri_gmappo  # noqa: E402
import run_drtp_sg_strict_10m_single as strict  # noqa: E402

PROTOCOL, SOURCE_FREEZE = "DRTP-STABILIZATION-S2-STAGE1-V1", "bd836ed2"
SEEDS, UPDATES, NUM_ENVS, ROLLOUT_STEPS = (2901, 2902, 2903), 1953, 4, 64
MILESTONES = {976: "250k", 1953: "500k"}
TAPE, FREEZE = ROOT / "configs" / "drtp_stabilization_s1_development_tape.json", ROOT / "configs" / "drtp_stabilization_s0_freeze.json"

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""): digest.update(chunk)
    return digest.hexdigest()

def current_commit() -> str:
    try: return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError): return SOURCE_FREEZE

def training_config(seed: int, output: Path):
    if seed not in SEEDS: raise ValueError("S2 permits only seeds 2901–2903")
    template = strict.training_config("utr_sg", strict.SEEDS[0], output)
    return replace(template, seed=seed, updates=UPDATES, save_interval=976, milestone_updates=MILESTONES,
                   out_dir=str(output), drtp_sampler_mode="conservative_drtp", drtp_sampler_seed=seed,
                   drtp_sampler_total_updates=UPDATES, runtime_state_checkpointing=True,
                   runtime_state_save_interval=976, evaluation_enabled=False)

def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--seed", type=int, choices=SEEDS, required=True); parser.add_argument("--output-root", type=Path, required=True); parser.add_argument("--s1-root", type=Path, required=True); parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute: raise SystemExit("--execute required")
    decision = json.loads((args.s1_root / "diagnostics" / "s1_05m_gate" / "S1_05M_GATE_DECISION.json").read_text(encoding="utf-8"))
    if decision.get("decision") != "S1_NO_GO": raise RuntimeError("S2 is eligible only after S1_NO_GO")
    tape, freeze = json.loads(TAPE.read_text(encoding="utf-8")), json.loads(FREEZE.read_text(encoding="utf-8"))
    out = args.output_root / "runs" / "conservative_drtp_sg" / f"seed{args.seed}"
    if out.exists() and any(out.iterdir()): raise FileExistsError(f"refusing overwrite/rerun: {out}")
    out.mkdir(parents=True, exist_ok=False); cfg = training_config(args.seed, out); manifest_path = out / "run_manifest.json"
    manifest = {"protocol": PROTOCOL, "status": "running", "source_freeze_commit": SOURCE_FREEZE, "delivery_commit": current_commit(),
                "arm": "conservative_drtp_sg", "sampler_mode": "conservative_drtp", "seed": args.seed, "updates": UPDATES,
                "environment_steps": UPDATES * NUM_ENVS * ROLLOUT_STEPS, "num_envs": NUM_ENVS, "rollout_steps": ROLLOUT_STEPS, "milestone_updates": MILESTONES,
                "from_scratch": True, "early_stopping": False, "checkpoint_promotion": False, "seed_replacement": False, "rerun_authorized": False, "continuation_authorized": False,
                "parameter_count": 116728, "tape_hash": tape["tape_hash"], "s1_gate_sha256": sha256(args.s1_root / "diagnostics" / "s1_05m_gate" / "S1_05M_GATE_DECISION.json"),
                "delta_q_l1": freeze["delta_q_l1"], "uniform_anchor": freeze["s2_uniform_anchor"], "adaptive_mass": freeze["s2_adaptive_mass"], "config": cfg.__dict__, "started_at": time.time()}
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    try:
        train_ri_gmappo(cfg)
        required = [out / "actor_critic_latest.pt", out / "actor_critic_runtime_state_latest.pt", out / "train_log.csv", out / "drtp_topology_sampler_log.csv"]
        for label in MILESTONES.values(): required += [out / f"actor_critic_milestone_{label}.pt", out / f"actor_critic_runtime_state_milestone_{label}.pt"]
        missing = [str(path) for path in required if not path.exists() or path.stat().st_size == 0]
        if missing: raise RuntimeError("S2 persistence failure: " + "; ".join(missing))
        manifest.update({"status": "completed", "finished_at": time.time(), "final_checkpoint_sha256": sha256(out / "actor_critic_latest.pt")})
    except Exception as exc:
        manifest.update({"status": "technical_invalid", "finished_at": time.time(), "error": repr(exc)}); manifest_path.write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8"); raise
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")

if __name__ == "__main__": main()
