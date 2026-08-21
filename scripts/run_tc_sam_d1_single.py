"""Run exactly one from-scratch TC-SAM-D1 trajectory under the frozen T1 contract."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from algorithms.ri_gmappo.simple_ri_gmappo import train_ri_gmappo  # noqa: E402
from scripts.run_t1_telemetry_native_single import SEEDS, config_hash, training_config  # noqa: E402

PROTOCOL = "TC-SAM-D1-FIVE-SEED-DEVELOPMENT-TRAINING-V1"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda: f.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--seed", choices=SEEDS, type=int, required=True)
    p.add_argument("--output-root", type=Path, required=True)
    p.add_argument("--t1-root", type=Path, required=True)
    p.add_argument("--execute", action="store_true")
    a = p.parse_args()
    if not a.execute:
        raise SystemExit("explicit --execute required")
    provenance = json.loads((a.output_root / "comparator_provenance.json").read_text(encoding="utf-8"))
    if provenance.get("status") != "PASS":
        raise RuntimeError("T1 comparator provenance did not pass")
    out = a.output_root / "runs" / "tc_sam_utr" / f"seed{a.seed}"
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"refusing to overwrite: {out}")
    out.mkdir(parents=True, exist_ok=False)
    cfg = training_config(a.seed, out)
    cfg.sam_enabled, cfg.sam_rho, cfg.sam_epsilon = True, 0.05, 1e-12
    cfg.device = "cuda" if torch.cuda.is_available() else "cpu"
    manifest = {"protocol": PROTOCOL, "status": "running", "method": "TC-SAM-UTR", "arm": "tc_sam_utr",
        "seed": a.seed, "parameter_count": 116728, "graph_encoder": "single", "actor_gradient_mode": "utr",
        "sam_enabled": True, "sam_scope": "actor_only", "sam_rho": 0.05, "sam_epsilon": 1e-12,
        "updates": cfg.updates, "environment_steps": cfg.num_envs * cfg.rollout_steps * cfg.updates,
        "num_envs": cfg.num_envs, "rollout_steps": cfg.rollout_steps, "from_scratch": True,
        "strict_continuous": True, "resume": False, "historical_checkpoint_used": False,
        "checkpoint_promotion": False, "early_stopping": False, "seed_exclusion": False,
        "final_checkpoint_only": True, "canonical_seeds_used": False, "held_out_seeds_used": False,
        "nominal_anchor": 0.5, "failure_groups": ["F0", "TE", "TL", "DS", "DL", "CP"],
        "conditional_failure_exposure": "uniform_fixed_cycle", "drtp_adaptation": False,
        "runtime_state_persistence_from_start": True, "t1_comparator_root": str(a.t1_root),
        "tape_hash": provenance["tape_hash"] if "tape_hash" in provenance else json.loads((a.t1_root / "tape_manifest.json").read_text())["tape_hash"],
        "config_hash": config_hash(cfg), "config": cfg.__dict__}
    (out / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    train_ri_gmappo(cfg)
    required = [out / x for x in ("actor_critic_latest.pt", "actor_critic_runtime_state_latest.pt", "fixed_stratified_topology_sampler_manifest.json", "fixed_stratified_topology_sampler_log.csv", "actor_gradient_telemetry.csv", "train_log.csv")]
    missing = [str(x) for x in required if not x.exists() or not x.stat().st_size]
    if missing:
        raise RuntimeError(f"incomplete run: {missing}")
    manifest.update({"status": "completed", "final_checkpoint_sha256": sha256(required[0]),
                     "runtime_checkpoint_sha256": sha256(required[1]), "sampler_manifest_sha256": sha256(required[2]),
                     "sampler_log_sha256": sha256(required[3]), "actor_gradient_log_sha256": sha256(required[4])})
    (out / "run_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
