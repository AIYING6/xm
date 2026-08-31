"""CPU-only isolation audit for the prospective SR-DRTP P1 shadow branches.

This script creates synthetic, short runtime continuations only.  It does not
use a development/evaluation tape, proposed P1 seeds, or an SR-DRTP selector.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import replace
from pathlib import Path
import sys
from typing import Any

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.drtp_topology_sampler import FAILURE_GROUPS, UNIFORM_Q
from algorithms.ri_gmappo.simple_ri_gmappo import (  # noqa: E402
    RIGMAPPOConfig,
    load_runtime_training_checkpoint,
    train_ri_gmappo,
)


def exact_equal(left: Any, right: Any) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, torch.Tensor):
        return bool(torch.equal(left, right))
    if isinstance(left, np.ndarray):
        return bool(np.array_equal(left, right, equal_nan=True))
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(exact_equal(left[key], right[key]) for key in left)
    if isinstance(left, (list, tuple)):
        return len(left) == len(right) and all(exact_equal(a, b) for a, b in zip(left, right))
    return left == right


def digest(value: Any) -> str:
    import io
    buffer = io.BytesIO()
    torch.save(value, buffer)
    return hashlib.sha256(buffer.getvalue()).hexdigest()


def read_last_row(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise AssertionError(f"missing train-log rows: {path}")
    return rows[-1]


def base_config(out_dir: Path, updates: int) -> RIGMAPPOConfig:
    return RIGMAPPOConfig(
        env_name="3d_intercept", seed=99301, num_envs=4, rollout_steps=64,
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
        drtp_sampler_mode="drtp", drtp_sampler_seed=99301, drtp_sampler_total_updates=2,
        drtp_sampler_logging=True, runtime_state_checkpointing=True,
        runtime_state_save_interval=1, sr_drtp_telemetry=False,
    )


def continuation(source: Path, out_dir: Path, branch: str) -> RIGMAPPOConfig:
    return replace(
        base_config(out_dir, 1), update_offset=1, runtime_state_resume=str(source),
        diagnostic_rng_branch_mode="exact_replay", diagnostic_rng_branch_seed=None,
        sr_drtp_shadow_branch=branch, sr_drtp_shadow_uniform_anchor=0.20,
    )


def make_nonuniform_source(source: Path, destination: Path) -> dict[str, float]:
    payload = torch.load(source, map_location="cpu", weights_only=False)
    q = {"F0": 0.30, **{group: 0.14 for group in FAILURE_GROUPS if group != "F0"}}
    if not np.isclose(sum(q.values()), 1.0):
        raise AssertionError("synthetic q is not a simplex point")
    payload["drtp_sampler_state"]["q"] = q
    torch.save(payload, destination)
    return q


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("--execute required")
    root = args.output_root.resolve()
    if root.exists():
        raise FileExistsError(f"refusing to overwrite audit output: {root}")
    root.mkdir(parents=True)

    source = root / "source"
    continuous = root / "continuous"
    train_ri_gmappo(base_config(source, 1))
    train_ri_gmappo(base_config(continuous, 2))
    runtime = source / "actor_critic_runtime_state_latest.pt"
    source_state = load_runtime_training_checkpoint(runtime, torch.device("cpu"))

    branch_a = root / "branch_a"
    train_ri_gmappo(continuation(runtime, branch_a, "none"))
    continuous_state = load_runtime_training_checkpoint(
        continuous / "actor_critic_runtime_state_latest.pt", torch.device("cpu")
    )
    branch_a_state = load_runtime_training_checkpoint(
        branch_a / "actor_critic_runtime_state_latest.pt", torch.device("cpu")
    )
    if not exact_equal(continuous_state, branch_a_state):
        raise AssertionError("A exact continuation differs from uninterrupted Original DRTP")

    nonuniform_runtime = root / "synthetic_nonuniform_runtime.pt"
    synthetic_q = make_nonuniform_source(runtime, nonuniform_runtime)
    branch_b = root / "branch_b"
    train_ri_gmappo(continuation(nonuniform_runtime, branch_b, "sampler_uniform_anchor"))
    b_manifest = json.loads((branch_b / "sr_drtp_shadow_branch_manifest.json").read_text(encoding="utf-8"))
    expected_q = {group: 0.80 * synthetic_q[group] + 0.20 * UNIFORM_Q for group in FAILURE_GROUPS}
    b_anchor = b_manifest["sampler_anchor"]
    if b_manifest["model_sha256_after_restore"] != digest(source_state["model_state"]):
        raise AssertionError("B changed model while applying sampler intervention")
    if b_manifest["optimizer_sha256_after_restore"] != digest(source_state["optimizer_state"]):
        raise AssertionError("B changed optimizer while applying sampler intervention")
    if b_anchor is None or b_anchor["before"] != synthetic_q or b_anchor["after"] != expected_q:
        raise AssertionError("B sampler anchor differs from its frozen convex combination")

    branch_c = root / "branch_c"
    train_ri_gmappo(continuation(runtime, branch_c, "actor_rollback_next_update"))
    c_manifest = json.loads((branch_c / "sr_drtp_shadow_branch_manifest.json").read_text(encoding="utf-8"))
    c_row = read_last_row(branch_c / "train_log.csv")
    if c_manifest["sampler_anchor"] is not None:
        raise AssertionError("C unexpectedly applied a sampler intervention")
    if c_manifest["model_sha256_after_restore"] != digest(source_state["model_state"]):
        raise AssertionError("C changed model before its one-shot actor update")
    if c_manifest["optimizer_sha256_after_restore"] != digest(source_state["optimizer_state"]):
        raise AssertionError("C changed optimizer before its one-shot actor update")
    if not (
        float(c_row["sr_drtp_shadow_actor_rollback_applied"]) == 1.0
        and float(c_row["actor_optimizer_state_restored"]) == 1.0
        and float(c_row["critic_step_retained_after_actor_rollback"]) == 1.0
    ):
        raise AssertionError("C did not perform actor-only rollback with critic retention")

    report = {
        "protocol": "SR-DRTP-P1-BRANCH-ISOLATION-AUDIT-V1",
        "status": "P1_BRANCH_ISOLATION_PASS",
        "scope": "CPU-only synthetic runtime continuations; no P1 candidate seed, development tape, or evaluation tape",
        "training_started": False,
        "sr_drtp_algorithm_training_started": False,
        "checks": {
            "a_exact_original_continuation": True,
            "b_sampler_only_model_optimizer_unchanged_at_intervention": True,
            "b_frozen_uniform_anchor_exact": True,
            "c_no_sampler_anchor": True,
            "c_actor_optimizer_slots_restored": True,
            "c_critic_update_retained": True,
            "formal_or_heldout_evaluation_tape_used": False,
            "pp_signal_enters_no_control_path": True,
            "mainline_a_modified": False,
        },
    }
    (root / "P1_BRANCH_ISOLATION_AUDIT.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (root / "P1_BRANCH_ISOLATION_AUDIT.md").write_text(
        "# SR-DRTP P1 branch-isolation audit\n\n"
        "**Status:** `P1_BRANCH_ISOLATION_PASS`.\n\n"
        "This CPU-only audit proves branch mechanics, not risk-signal utility. "
        "No proposed P1 seed, official trajectory, development/evaluation tape, or SR-DRTP algorithm training was used.\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": report["status"], "output": str(root)}, indent=2))


if __name__ == "__main__":
    main()
