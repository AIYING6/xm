"""Run the zero-training P1C UAV commitment-semantics gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from envs.epistemic_commitment_uav_shadow_env import (
    COMMIT,
    DEFER,
    FALLBACK,
    CommitmentChoice,
    EpistemicCommitmentUAVShadowEnv,
)


def _compact(outcome: dict) -> dict:
    return {
        key: outcome[key]
        for key in (
            "outcome",
            "task_value",
            "elapsed_steps",
            "energy_cost",
            "leader_progress",
            "follower_progress",
            "leader_follower_distance",
            "supported_corridor_entry",
            "unsupported_corridor_entry",
            "joint_commit",
            "unilateral_commit",
            "collision",
            "constraint_violation",
        )
    }


def run_p1c_gate(seed: int = 20260909) -> dict:
    delivered = EpistemicCommitmentUAVShadowEnv(True, seed)
    lost = EpistemicCommitmentUAVShadowEnv(False, seed)
    obs_delivered = delivered.actor_observation()
    obs_lost = lost.actor_observation()

    bilateral = delivered.execute(CommitmentChoice(COMMIT, COMMIT))
    unilateral = lost.execute(CommitmentChoice(COMMIT, FALLBACK))
    fallback = EpistemicCommitmentUAVShadowEnv(False, seed).execute(
        CommitmentChoice(FALLBACK, FALLBACK)
    )
    defer = EpistemicCommitmentUAVShadowEnv(False, seed).execute(
        CommitmentChoice(DEFER, DEFER)
    )

    replay_env = EpistemicCommitmentUAVShadowEnv(True, seed)
    state = replay_env.state_dict()
    first = replay_env.execute(CommitmentChoice(COMMIT, COMMIT))
    replay_env.load_state_dict(state)
    replay = replay_env.execute(CommitmentChoice(COMMIT, COMMIT))

    checks = {
        "leader_history_indistinguishable_across_delivery_states": bool(
            np.array_equal(obs_delivered[0], obs_lost[0])
        ),
        "receiver_privately_observes_delivery": bool(
            not np.array_equal(obs_delivered[2], obs_lost[2])
        ),
        "other_agents_do_not_receive_global_delivery_truth": bool(
            np.array_equal(obs_delivered[1], obs_lost[1])
        ),
        "bilateral_commitment_completes_shadow_task": bilateral["supported_corridor_entry"]
        and bilateral["task_value"] > 0.0,
        "unilateral_commitment_has_strict_cost": unilateral["unsupported_corridor_entry"]
        and unilateral["task_value"] < 0.0,
        "fallback_is_finite_and_below_bilateral_value": 0.0 < fallback["task_value"] < bilateral["task_value"],
        "defer_is_distinct_from_fallback_and_commit": defer["task_value"] not in {
            fallback["task_value"], bilateral["task_value"]
        },
        "all_choices_have_nonzero_physical_cost": all(
            sum(result["energy_cost"]) > 0.0 for result in (bilateral, unilateral, fallback, defer)
        ),
        "fixed_scripts_are_collision_free": not any(
            result["collision"] for result in (bilateral, unilateral, fallback, defer)
        ),
        "fixed_scripts_respect_flight_envelope": not any(
            result["constraint_violation"] for result in (bilateral, unilateral, fallback, defer)
        ),
        "task_is_neither_impossible_nor_saturated": bilateral["task_value"] > 0.0
        and unilateral["task_value"] < 0.0
        and fallback["task_value"] > 0.0,
        "runtime_restore_exact": _compact(first) == _compact(replay),
    }
    passed = all(checks.values())
    return {
        "protocol": "EPISTEMIC-COMMITMENT-P1C-UAV-SHADOW-GATE-V1",
        "verdict": "P1C_UAV_COMMITMENT_SEMANTIC_PASS" if passed else "P1C_UAV_COMMITMENT_SEMANTIC_FAIL",
        "checks": checks,
        "seed": seed,
        "outcomes": {
            "bilateral_commitment": _compact(bilateral),
            "unilateral_commitment": _compact(unilateral),
            "graceful_degradation": _compact(fallback),
            "coordinated_defer": _compact(defer),
        },
        "evidence_boundary": (
            "The gate proves private-delivery semantics and distinct embodied task consequences only. "
            "It does not prove policy learnability, algorithmic novelty, or performance improvement."
        ),
        "training_started": False,
        "environment_steps": 0,
        "ppo_updates": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run_p1c_gate()
    payload = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload + "\n")
    print(payload)
    if report["verdict"].endswith("FAIL"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
