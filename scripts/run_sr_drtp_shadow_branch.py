"""Run an exact, update-boundary SR-DRTP shadow continuation.

P0 intentionally supports only ``exact_replay``.  It is a technical proof
that a copied runtime state can continue in a separate directory; it is not a
selector and contains no sampler or PPO intervention path.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import fields
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import (  # noqa: E402
    RIGMAPPOConfig,
    load_runtime_training_checkpoint,
    train_ri_gmappo,
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-checkpoint", type=Path, required=True)
    parser.add_argument("--config-json", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--updates", type=int, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("--execute required")
    if int(args.updates) <= 0:
        raise ValueError("shadow updates must be positive")
    if args.output_dir.exists():
        raise FileExistsError(f"refusing to overwrite shadow output: {args.output_dir}")
    payload = load_runtime_training_checkpoint(args.runtime_checkpoint, device="cpu")
    config_values = json.loads(args.config_json.read_text(encoding="utf-8"))
    allowed = {field.name for field in fields(RIGMAPPOConfig)}
    unknown = sorted(set(config_values).difference(allowed))
    if unknown:
        raise ValueError(f"unknown RIGMAPPOConfig keys in frozen shadow config: {unknown}")
    # P0's branch is only a copied official trajectory.  Explicitly deny every
    # existing or future intervention route instead of relying on defaults.
    forbidden = {
        "policy_update_guard_mode": "none",
        "target_kl": None,
        "intervention_utility_audit_enabled": False,
        "counterfactual_critic_enabled": False,
        "drtp_sampler_mode": "drtp",
    }
    for key, expected in forbidden.items():
        if config_values.get(key, expected) != expected:
            raise ValueError(f"P0 exact shadow forbids {key}={config_values.get(key)!r}")
    args.output_dir.mkdir(parents=True, exist_ok=False)
    config_values.update({
        "updates": int(args.updates),
        "out_dir": str(args.output_dir),
        "runtime_state_resume": str(args.runtime_checkpoint.resolve()),
        "update_offset": int(payload["update"]),
        "append_log": False,
        "diagnostic_rng_branch_mode": "exact_replay",
        "diagnostic_rng_branch_seed": None,
        "evaluation_enabled": False,
        "runtime_state_checkpointing": True,
        "runtime_state_save_interval": 1,
    })
    cfg = RIGMAPPOConfig(**config_values)
    manifest = {
        "protocol": "SR-DRTP-P0-EXACT-SHADOW-BRANCH-V1",
        "status": "running",
        "branch_kind": "exact_replay_only",
        "official_trajectory_modified": False,
        "algorithm_intervention": "none",
        "formal_or_heldout_evaluation_tape_used": False,
        "runtime_checkpoint": str(args.runtime_checkpoint.resolve()),
        "runtime_checkpoint_sha256": sha256(args.runtime_checkpoint),
        "config_sha256": sha256(args.config_json),
        "source_update": int(payload["update"]),
        "continuation_updates": int(args.updates),
    }
    manifest_path = args.output_dir / "shadow_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    try:
        train_ri_gmappo(cfg)
        required = args.output_dir / "actor_critic_runtime_state_latest.pt"
        if not required.exists():
            raise FileNotFoundError("shadow continuation did not emit a runtime checkpoint")
        manifest.update({"status": "completed", "output_runtime_checkpoint": str(required)})
    except BaseException as exc:
        manifest.update({"status": "failed", "error": repr(exc)})
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        raise
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "P0_EXACT_SHADOW_PASS", "manifest": str(manifest_path)}, indent=2))


if __name__ == "__main__":
    main()
