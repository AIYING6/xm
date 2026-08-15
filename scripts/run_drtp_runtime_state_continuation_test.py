"""Technical proof that post-warm-restart runtime checkpoints strictly continue.

This script performs only short CPU smoke trajectories.  For both UTR and
DRTP it compares an uninterrupted two-update run with a one-update run followed
by a runtime-state reload and one further update.  No development/canonical
tape or long training is created.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
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
from algorithms.ri_gmappo.drtp_topology_sampler import (  # noqa: E402
    ALL_GROUPS,
    GROUP_MEMBERS,
    NOMINAL_GROUP,
    DRTPSelection,
    DRTPTopologySampler,
)


OUT = ROOT / "results" / "development" / "drtp_runtime_state_continuation_test_v1"
TECHNICAL_SEEDS = {"utr": 99101, "drtp": 99102}


def config(mode: str, seed: int, out_dir: Path, updates: int, **overrides: Any) -> RIGMAPPOConfig:
    values: dict[str, Any] = {
        "env_name": "3d_intercept", "seed": seed, "num_envs": 4,
        "rollout_steps": 64, "updates": updates, "hidden_dim": 115,
        "role_dim": 8, "intent_dim": 8, "graph_encoder": "single",
        "role_gate_mode": "none", "target_policy": "straight",
        "strict_target_sensing": True, "agent_target_info_bottleneck": True,
        "relay_dependent_task": True, "business_grounded_geometry": True,
        "communication_range_scale": 1.0, "communication_dropout_prob": 0.0,
        "message_delay_steps": 0, "radar_dropout_prob": 0.0,
        "min_success_step": 260, "failed_blue_agent": -1,
        "node_failure_start_step": 0, "node_failure_duration_steps": 0,
        "evaluation_enabled": False, "target_kl": None, "save_interval": 1,
        "save_snapshots": False, "out_dir": str(out_dir), "device": "cpu",
        "topology_curriculum_schedule": "none", "fixed_f0_probability": None,
        "drtp_sampler_mode": mode, "drtp_sampler_seed": seed,
        "drtp_sampler_logging": True, "drtp_sampler_total_updates": 2,
        "runtime_state_checkpointing": True,
        "runtime_state_save_interval": 1,
    }
    values.update(overrides)
    return RIGMAPPOConfig(**values)


def exact_equal(left: Any, right: Any, path: str = "root") -> None:
    """Raise an informative assertion unless two persisted states are exact."""
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


def sampler_state_roundtrip() -> dict:
    """Exercise q/EMA and a non-empty adaptation window independent of PPO."""
    source = DRTPTopologySampler("drtp", 99103, 400)
    for update in (32, 64, 96, 128, 160):
        for index, group in enumerate(ALL_GROUPS):
            condition, onset, duration = GROUP_MEMBERS[group][0]
            source.record_completed_return(DRTPSelection(
                group, condition, onset, duration, -1 if group == NOMINAL_GROUP else 1,
            ), 100.0 - 15.0 * index)
        assert source.maybe_update(update) is not None
    # Preserve partial window contents too; this is the exact field legacy 3M
    # checkpoints cannot reconstruct.
    condition, onset, duration = GROUP_MEMBERS["F0"][0]
    source.record_completed_return(DRTPSelection("F0", condition, onset, duration, 1), -50.0)
    restored = DRTPTopologySampler("drtp", 99103, 400)
    restored.load_state_dict(source.state_dict())
    exact_equal(source.state_dict(), restored.state_dict())
    exact_equal(source.maybe_update(192), restored.maybe_update(192))
    exact_equal(source.state_dict(), restored.state_dict())
    return {
        "q_ema_difficulty_and_active_window_exact": True,
        "adaptation_count": source.adaptation_count,
    }


def run_mode(mode: str, seed: int, root: Path) -> dict:
    uninterrupted = root / f"{mode}_uninterrupted"
    segmented = root / f"{mode}_segmented"
    train_ri_gmappo(config(mode, seed, uninterrupted, updates=2))
    train_ri_gmappo(config(mode, seed, segmented, updates=1))

    boundary = segmented / "actor_critic_runtime_state_latest.pt"
    boundary_payload = load_runtime_training_checkpoint(boundary, torch.device("cpu"))
    assert boundary_payload["update"] == 1
    train_ri_gmappo(config(
        mode, seed, segmented, updates=1, update_offset=1, append_log=True,
        runtime_state_resume=str(boundary),
    ))

    left = load_runtime_training_checkpoint(
        uninterrupted / "actor_critic_runtime_state_latest.pt", torch.device("cpu"),
    )
    right = load_runtime_training_checkpoint(
        segmented / "actor_critic_runtime_state_latest.pt", torch.device("cpu"),
    )
    assert left["update"] == right["update"] == 2
    exact_equal(left, right)
    exact_equal(csv_rows(uninterrupted / "train_log.csv"), csv_rows(segmented / "train_log.csv"))
    exact_equal(
        csv_rows(uninterrupted / "drtp_topology_sampler_log.csv"),
        csv_rows(segmented / "drtp_topology_sampler_log.csv"),
    )
    return {
        "mode": mode,
        "seed": seed,
        "updates": 2,
        "parameter_count": 116728,
        "boundary_runtime_checkpoint": str(boundary),
        "runtime_state_save_reload_next_update_exact": True,
        "model_optimizer_env_rng_sampler_log_exact": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=OUT)
    args = parser.parse_args()
    root = args.output_root.resolve()
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"refusing to overwrite technical output: {root}")
    root.mkdir(parents=True, exist_ok=False)
    results = [run_mode(mode, seed, root) for mode, seed in TECHNICAL_SEEDS.items()]
    payload = {
        "protocol": "DRTP-WARM-RESTART-RUNTIME-CONTINUATION-TEST-V1",
        "status": "PASS",
        "long_training_started": False,
        "development_tape_generated": False,
        "canonical_seeds_used": False,
        "sampler_state_roundtrip": sampler_state_roundtrip(),
        "results": results,
    }
    output = root / "DRTP_RUNTIME_STATE_CONTINUATION_TEST.json"
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()
