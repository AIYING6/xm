"""Run one frozen PP-DRTP P4 independent 0.5M trajectory."""
from __future__ import annotations
import argparse, hashlib, json, sys, time
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
from algorithms.ri_gmappo.simple_ri_gmappo import train_ri_gmappo
import run_drtp_sg_strict_10m_single as strict

PROTOCOL = "PP-DRTP-P4-INDEPENDENT-VALIDATION-V1"
SEEDS = (3501, 3502, 3503, 3504, 3505)
UPDATES = 1953
ARMS = {"utr_sg": "utr", "drtp_sg": "drtp", "pp_drtp_sg": "pp_drtp"}
TAPE = ROOT / "configs" / "pp_drtp_p4_validation_tape.json"
FREEZE = ROOT / "configs" / "pp_drtp_p4_validation_freeze.json"
P2 = ROOT / "docs" / "drtp_stable_v2_d8_20260830" / "PP_DRTP_P2_TECHNICAL_AUDIT.json"

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def training_config(arm: str, seed: int, out: Path):
    base = strict.training_config("utr_sg", strict.SEEDS[0], out)
    return replace(
        base, seed=seed, updates=UPDATES, save_interval=UPDATES,
        milestone_updates={976: "250k", 1953: "500k"}, out_dir=str(out),
        drtp_sampler_mode=ARMS[arm], drtp_sampler_seed=seed,
        drtp_sampler_total_updates=UPDATES, drtp_sampler_logging=True,
        runtime_state_checkpointing=True, runtime_state_save_interval=UPDATES,
        evaluation_enabled=False, pp_drtp_probe_count=4, pp_drtp_probe_seed=seed,
    )

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=tuple(ARMS), required=True)
    parser.add_argument("--seed", choices=SEEDS, type=int, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("--execute required")
    if json.loads(P2.read_text())["status"] != "P2_TECHNICAL_PASS":
        raise RuntimeError("PP P2 audit not PASS")
    freeze = json.loads(FREEZE.read_text())
    if freeze["training_seeds"] != list(SEEDS) or freeze["pp_probe_count"] != 4:
        raise RuntimeError("P4 freeze mismatch")
    tape_hash = digest(TAPE)
    out = args.output_root / "runs" / args.arm / f"seed{args.seed}"
    if out.exists():
        raise FileExistsError(f"refusing rerun/overwrite: {out}")
    out.mkdir(parents=True)
    cfg = training_config(args.arm, args.seed, out)
    manifest = {
        "protocol": PROTOCOL, "status": "running", "arm": args.arm,
        "seed": args.seed, "sampler_mode": cfg.drtp_sampler_mode,
        "updates": UPDATES, "environment_steps": UPDATES * 4 * 64,
        "probe_count": 4 if args.arm == "pp_drtp_sg" else 0,
        "checkpoint_selection": "common_final_500k_only",
        "early_stopping": False, "rerun_authorized": False,
        "continuation_authorized": False, "tape_sha256": tape_hash,
        "freeze_sha256": digest(FREEZE), "p2_audit_sha256": digest(P2),
        "config": cfg.__dict__, "started_at": time.time(),
    }
    path = out / "run_manifest.json"
    path.write_text(json.dumps(manifest, indent=2, default=str) + "\n")
    try:
        train_ri_gmappo(cfg)
        required = [
            "actor_critic_latest.pt", "actor_critic_runtime_state_latest.pt",
            "train_log.csv", "drtp_topology_sampler_log.csv",
            "actor_critic_milestone_250k.pt", "actor_critic_milestone_500k.pt",
        ]
        if args.arm == "pp_drtp_sg":
            required.append("pp_drtp_probe_log.csv")
        missing = [name for name in required if not (out / name).exists()]
        if missing:
            raise RuntimeError("missing frozen artifacts: " + ",".join(missing))
        manifest.update(status="completed", finished_at=time.time(),
                        final_checkpoint_sha256=digest(out / "actor_critic_latest.pt"))
    except Exception as exc:
        manifest.update(status="technical_invalid", finished_at=time.time(), error=repr(exc))
        path.write_text(json.dumps(manifest, indent=2, default=str) + "\n")
        raise
    path.write_text(json.dumps(manifest, indent=2, default=str) + "\n")

if __name__ == "__main__":
    main()
