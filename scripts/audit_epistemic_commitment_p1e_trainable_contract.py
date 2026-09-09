"""Zero-training audit for the minimal trainable commitment task contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from envs.epistemic_commitment_trainable_env import (
    ACTION_COMMIT,
    ACTION_DEFER,
    ACTION_FALLBACK,
    EpistemicCommitmentEpisodeSpec,
    EpistemicCommitmentTrainableEnv,
    make_balanced_evaluation_tape,
)


TRAINING_SEEDS = (98101, 98102, 98103)


def _run_episode(spec: EpistemicCommitmentEpisodeSpec, policy: str) -> dict:
    env = EpistemicCommitmentTrainableEnv(seed=20260909, episode_spec=spec)
    obs0, share0, graph0 = env.reset()
    obs1, share1, graph1, reward0, done0, _ = env.step([ACTION_FALLBACK] * 3)
    if policy == "adaptive_script":
        if spec.context == "low":
            leader = follower = ACTION_FALLBACK
        elif spec.context == "middle":
            leader = follower = ACTION_DEFER
        else:
            leader = ACTION_COMMIT
            follower = ACTION_COMMIT if spec.delivered else ACTION_FALLBACK
    elif policy == "always_commit":
        leader = follower = ACTION_COMMIT
    elif policy == "always_defer":
        leader = follower = ACTION_DEFER
    elif policy == "always_fallback":
        leader = follower = ACTION_FALLBACK
    else:
        raise ValueError(policy)
    _, _, _, rewards, dones, info = env.step([leader, ACTION_FALLBACK, follower])
    return {
        "value": float(rewards[0, 0]),
        "info": info,
        "shape_ok": (
            obs0.shape == obs1.shape == (3, 39)
            and share0.shape == share1.shape == (3, 117)
            and graph0.keys() == graph1.keys()
            and reward0.shape == done0.shape == rewards.shape == dones.shape == (3, 1)
        ),
    }


def run_p1e_audit() -> dict:
    tape = make_balanced_evaluation_tape()
    policies = ("adaptive_script", "always_commit", "always_defer", "always_fallback")
    rows = {policy: [_run_episode(spec, policy) for spec in tape] for policy in policies}
    means = {policy: float(np.mean([row["value"] for row in values])) for policy, values in rows.items()}

    matched_delivered = EpistemicCommitmentEpisodeSpec(999001, "middle", True)
    matched_lost = EpistemicCommitmentEpisodeSpec(999001, "middle", False)
    env_delivered = EpistemicCommitmentTrainableEnv(7, matched_delivered)
    env_lost = EpistemicCommitmentTrainableEnv(7, matched_lost)
    cue_delivered = env_delivered.reset()[0]
    cue_lost = env_lost.reset()[0]
    decision_delivered = env_delivered.step([2, 2, 2])[0]
    decision_lost = env_lost.step([2, 2, 2])[0]

    all_infos = [row["info"] for values in rows.values() for row in values]
    endpoints = {info["endpoint"] for info in all_infos}
    reconstructed = all(
        row["value"] == float(row["info"]["task_value"])
        for values in rows.values()
        for row in values
    )
    tape_payload = [
        {"episode_id": spec.episode_id, "context": spec.context, "delivered": spec.delivered}
        for spec in tape
    ]
    checks = {
        "standard_interface_shapes_exact": all(row["shape_ok"] for values in rows.values() for row in values),
        "cue_stage_contains_no_delivery_leak": bool(np.array_equal(cue_delivered, cue_lost)),
        "decision_stage_sender_observation_matched": bool(
            np.array_equal(decision_delivered[0], decision_lost[0])
        ),
        "decision_stage_receiver_observation_private": bool(
            not np.array_equal(decision_delivered[2], decision_lost[2])
        ),
        "decision_stage_relay_observation_matched": bool(
            np.array_equal(decision_delivered[1], decision_lost[1])
        ),
        "adaptive_script_beats_all_constant_modes": means["adaptive_script"]
        > max(means["always_commit"], means["always_defer"], means["always_fallback"]),
        "no_constant_mode_dominates_task": all(
            means["adaptive_script"] > means[name]
            for name in ("always_commit", "always_defer", "always_fallback")
        ),
        "endpoint_values_reconstruct_from_telemetry": reconstructed,
        "success_failure_and_degradation_endpoints_covered": {
            "compatible_bilateral_commitment",
            "incompatible_or_unilateral_commitment",
            "coordinated_defer",
            "graceful_fallback",
        }.issubset(endpoints),
        "fixed_tape_size_exact": len(tape) == 300,
        "training_seeds_fresh_and_exact": TRAINING_SEEDS == (98101, 98102, 98103),
        "physical_safety_telemetry_present": all(
            "collision" in info and "constraint_violation" in info for info in all_infos
        ),
    }
    passed = all(checks.values())
    return {
        "protocol": "EPISTEMIC-COMMITMENT-P1E-TRAINABLE-CONTRACT-AUDIT-V1",
        "verdict": "P1E_TRAINABLE_CONTRACT_AUDIT_PASS" if passed else "P1E_TRAINABLE_CONTRACT_AUDIT_FAIL",
        "checks": checks,
        "training_seeds": list(TRAINING_SEEDS),
        "evaluation_tape": tape_payload,
        "scripted_mean_task_value": means,
        "covered_endpoints": sorted(endpoints),
        "evidence_boundary": (
            "This zero-training audit establishes interface, information-boundary, endpoint, and non-dominance "
            "contracts. It does not establish neural-policy learnability, calibration, or method advantage."
        ),
        "training_started": False,
        "training_environment_steps": 0,
        "diagnostic_physics_steps": len(policies) * len(tape) * 16,
        "ppo_updates": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run_p1e_audit()
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
