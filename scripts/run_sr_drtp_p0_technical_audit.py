"""P0 technical audit for read-only SR-DRTP instrumentation.

This is intentionally a CPU smoke test: it creates no development tape, uses
no historical checkpoint, and starts no long training.  It proves the narrow
engineering properties required before a future *separately authorized* P1
shadow study could be considered.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import numpy as np
import torch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import (  # noqa: E402
    RIGMAPPOConfig,
    load_runtime_training_checkpoint,
    train_ri_gmappo,
)


OUT = ROOT / "results" / "development" / "sr_drtp_p0_technical_audit"


def config(out_dir: Path, updates: int, *, telemetry: bool = False) -> RIGMAPPOConfig:
    return RIGMAPPOConfig(
        env_name="3d_intercept", seed=99201, num_envs=4, rollout_steps=64,
        updates=updates, hidden_dim=115, role_dim=8, intent_dim=8,
        graph_encoder="single", role_gate_mode="none", target_policy="straight",
        strict_target_sensing=True, agent_target_info_bottleneck=True,
        relay_dependent_task=True, business_grounded_geometry=True,
        communication_range_scale=1.0, communication_dropout_prob=0.0,
        message_delay_steps=0, radar_dropout_prob=0.0, min_success_step=260,
        failed_blue_agent=-1, node_failure_start_step=0, node_failure_duration_steps=0,
        evaluation_enabled=False, target_kl=None, policy_update_guard_mode="none",
        intervention_utility_audit_enabled=False, counterfactual_critic_enabled=False,
        save_interval=1, save_snapshots=False, out_dir=str(out_dir), device="cpu",
        topology_curriculum_schedule="none", fixed_f0_probability=None,
        drtp_sampler_mode="drtp", drtp_sampler_seed=99201,
        drtp_sampler_total_updates=2, drtp_sampler_logging=True,
        runtime_state_checkpointing=True, runtime_state_save_interval=1,
        sr_drtp_telemetry=telemetry, sr_drtp_telemetry_interval=1,
    )


def exact_equal(left: Any, right: Any, path: str = "root") -> None:
    if isinstance(left, torch.Tensor):
        assert isinstance(right, torch.Tensor), path
        assert left.dtype == right.dtype and left.shape == right.shape, path
        assert torch.equal(left, right), path
        return
    if isinstance(left, np.ndarray):
        assert isinstance(right, np.ndarray), path
        assert left.dtype == right.dtype and left.shape == right.shape, path
        assert np.array_equal(left, right, equal_nan=True), path
        return
    if isinstance(left, dict):
        assert isinstance(right, dict) and set(left) == set(right), path
        for key in left:
            exact_equal(left[key], right[key], f"{path}.{key}")
        return
    if isinstance(left, (list, tuple)):
        assert isinstance(right, type(left)) and len(left) == len(right), path
        for index, (item_left, item_right) in enumerate(zip(left, right)):
            exact_equal(item_left, item_right, f"{path}[{index}]")
        return
    assert left == right, path


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=OUT)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("--execute required")
    root = args.output_root.resolve()
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"refusing to overwrite P0 audit: {root}")
    root.mkdir(parents=True, exist_ok=False)

    off_one = root / "default_off_one_update"
    off_two = root / "default_off_two_updates"
    on_one = root / "telemetry_on_one_update"
    train_ri_gmappo(config(off_one, 1, telemetry=False))
    train_ri_gmappo(config(off_two, 2, telemetry=False))
    train_ri_gmappo(config(on_one, 1, telemetry=True))

    off_state = load_runtime_training_checkpoint(off_one / "actor_critic_runtime_state_latest.pt", torch.device("cpu"))
    on_state = load_runtime_training_checkpoint(on_one / "actor_critic_runtime_state_latest.pt", torch.device("cpu"))
    # The diagnostic metadata differs by design; every trajectory-affecting
    # field must still be exact.
    trajectory_fields = [
        "model_state", "optimizer_state", "update", "best_eval_key", "rng_state",
        "environment_states", "obs", "share_obs", "graph_obs", "episode_counts",
        "drtp_episode_returns", "drtp_selections", "drtp_sampler_state", "normalization_state",
        "s1_rng_state", "failure_telemetry_state",
    ]
    for field in trajectory_fields:
        exact_equal(off_state[field], on_state[field], field)
    telemetry_rows = csv_rows(on_one / "sr_drtp_telemetry" / "training_state.csv")
    if len(telemetry_rows) != 1 or telemetry_rows[0]["training_only"] != "True":
        raise AssertionError("SR-DRTP writer did not emit one training-only row")
    if (off_one / "sr_drtp_telemetry").exists():
        raise AssertionError("default-off SR-DRTP telemetry emitted an artifact")

    frozen_config = dict(config(root / "unused", 2, telemetry=False).__dict__)
    frozen_config["device"] = "cpu"
    frozen_config_path = root / "exact_shadow_config.json"
    frozen_config_path.write_text(json.dumps(frozen_config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    shadow = root / "exact_shadow"
    command = [
        sys.executable, str(ROOT / "scripts" / "run_sr_drtp_shadow_branch.py"),
        "--runtime-checkpoint", str(off_one / "actor_critic_runtime_state_latest.pt"),
        "--config-json", str(frozen_config_path), "--output-dir", str(shadow),
        "--updates", "1", "--execute",
    ]
    subprocess.run(command, cwd=ROOT, check=True)
    continuous_state = load_runtime_training_checkpoint(off_two / "actor_critic_runtime_state_latest.pt", torch.device("cpu"))
    shadow_state = load_runtime_training_checkpoint(shadow / "actor_critic_runtime_state_latest.pt", torch.device("cpu"))
    exact_equal(continuous_state, shadow_state)
    shadow_manifest = json.loads((shadow / "shadow_manifest.json").read_text(encoding="utf-8"))
    if shadow_manifest["algorithm_intervention"] != "none" or shadow_manifest["official_trajectory_modified"]:
        raise AssertionError("P0 exact shadow has an unauthorized intervention")

    results = {
        "protocol": "SR-DRTP-P0-TECHNICAL-AUDIT-V1",
        "status": "P1_READY",
        "long_training_started": False,
        "official_development_trajectory_started": False,
        "formal_or_heldout_evaluation_tape_used": False,
        "algorithm_modification_activated": False,
        "checks": {
            "default_off_trajectory_exact": True,
            "default_off_emits_no_telemetry_artifact": True,
            "telemetry_on_is_write_only": True,
            "telemetry_schema_training_only": True,
            "runtime_snapshot_contains_model_optimizer_env_rng_sampler": True,
            "update_boundary_exact_shadow_matches_uninterrupted": True,
            "shadow_branch_has_no_algorithm_intervention": True,
            "probe_or_evaluation_leakage": False,
        },
        "artifacts": {
            "telemetry_csv_sha256": sha256(on_one / "sr_drtp_telemetry" / "training_state.csv"),
            "source_runtime_checkpoint": str(off_one / "actor_critic_runtime_state_latest.pt"),
            "shadow_manifest": str(shadow / "shadow_manifest.json"),
        },
        "scope_note": (
            "P1_READY means only that default-off telemetry and exact update-boundary shadow replay are "
            "technically ready. It is not evidence for a risk gate, a Selective-KLR mechanism, or training authorization."
        ),
    }
    (root / "SR_DRTP_P0_TECHNICAL_AUDIT.json").write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (root / "SR_DRTP_P0_TECHNICAL_AUDIT.md").write_text(
        "# SR-DRTP P0 technical audit\n\n"
        "**Status:** `P1_READY`.\n\n"
        "All checks are CPU smoke tests only. `P1_READY` is an engineering readiness result, not a mechanism claim "
        "or authorization to start a selector or any official training trajectory.\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "P1_READY", "output": str(root / "SR_DRTP_P0_TECHNICAL_AUDIT.json")}, indent=2))


if __name__ == "__main__":
    main()
