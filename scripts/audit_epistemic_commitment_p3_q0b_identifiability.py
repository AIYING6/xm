"""Trajectory-grounded information-gap audit for P3 before pilot training."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from envs.epistemic_commitment_p3_env import (
    MODE_COMMIT,
    MODE_DEFER,
    MODE_FALLBACK,
    EpistemicCommitmentP3Env,
    P3CommunicationSpec,
)


CONTRACT = ROOT / "configs" / "epistemic_commitment_p3_q0b_identifiability_20260909.json"
Q0 = ROOT / "docs" / "strong_q2_clean_sheet_p0_20260909" / "P3_Q0_RESULT.json"


def _action(mode: int) -> np.ndarray:
    value = np.zeros((3, 3), dtype=np.float32)
    value[:, 0] = (mode, MODE_DEFER, mode)
    return value


DEFER = _action(MODE_DEFER)
COMMIT = _action(MODE_COMMIT)
FALLBACK = _action(MODE_FALLBACK)


def _run(spec: P3CommunicationSpec, schedule: list[np.ndarray]):
    env = EpistemicCommitmentP3Env(spec, seed=20260909)
    leader_history = [env.reset()[0][env.leader_id].copy()]
    info = {}
    for action in schedule:
        obs, _, _, _, _, info = env.step(action)
        leader_history.append(obs[env.leader_id].copy())
    return env, np.stack(leader_history), info


def audit() -> dict:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    q0 = json.loads(Q0.read_text(encoding="utf-8"))
    delivered = P3CommunicationSpec("delivered", "delivered", "current")
    lost = P3CommunicationSpec("lost", "not_applicable", "current")
    ack_lost = P3CommunicationSpec("delivered", "lost", "current")

    delivered_prefix, delivered_history, _ = _run(delivered, [DEFER] * 3)
    lost_prefix, lost_history, _ = _run(lost, [DEFER] * 3)
    histories_equal = np.array_equal(delivered_history, lost_history)
    teammate_states_differ = (
        delivered_prefix.follower_plan_version == 1 and lost_prefix.follower_plan_version == -1
    )

    _, _, delivered_commit = _run(delivered, [DEFER] * 3 + [COMMIT] * 5)
    _, _, lost_commit = _run(lost, [DEFER] * 3 + [COMMIT] * 5)
    _, _, delivered_wait = _run(delivered, [DEFER] * 4 + [COMMIT] * 4)
    _, _, lost_wait = _run(lost, [DEFER] * 4 + [FALLBACK] * 4)
    _, _, delivered_fallback = _run(delivered, [DEFER] * 3 + [FALLBACK] * 5)
    _, _, lost_fallback = _run(lost, [DEFER] * 3 + [FALLBACK] * 5)

    probability = float(contract["public_probability_current_plan"])
    commit_values = [float(delivered_commit["task_value"]), float(lost_commit["task_value"])]
    defer_values = [float(delivered_wait["task_value"]), float(lost_wait["task_value"])]
    fallback_values = [float(delivered_fallback["task_value"]), float(lost_fallback["task_value"])]
    expected_commit = probability * commit_values[0] + (1.0 - probability) * commit_values[1]
    expected_defer = probability * defer_values[0] + (1.0 - probability) * defer_values[1]
    expected_fallback = probability * fallback_values[0] + (1.0 - probability) * fallback_values[1]
    bayes_values = {
        "commit_now": expected_commit,
        "defer_for_ack": expected_defer,
        "fallback_now": expected_fallback,
    }
    bayes_choice = max(bayes_values, key=bayes_values.get)
    robust_values = {
        "commit_now": min(commit_values),
        "defer_for_ack": min(defer_values),
        "fallback_now": min(fallback_values),
    }
    robust_choice = max(robust_values, key=robust_values.get)
    certainty_equivalent_choice = "commit_now" if commit_values[0] > fallback_values[0] else "fallback_now"

    delivered_after_ack, delivered_after_ack_history, _ = _run(delivered, [DEFER] * 4)
    ack_lost_after_wait, ack_lost_history, _ = _run(ack_lost, [DEFER] * 4)
    ack_shrinks = (
        delivered_after_ack.leader_ack_version == 1
        and ack_lost_after_wait.leader_ack_version == -1
        and not np.array_equal(delivered_after_ack_history[-1], ack_lost_history[-1])
    )

    constant_values = {}
    for name, action in (("always_commit", COMMIT), ("always_defer", DEFER), ("always_fallback", FALLBACK)):
        _, _, left = _run(delivered, [action] * 8)
        _, _, right = _run(lost, [action] * 8)
        constant_values[name] = probability * float(left["task_value"]) + (1.0 - probability) * float(
            right["task_value"]
        )
    contingent_value = expected_defer

    checks = {
        "leader_histories_observation_equivalent": histories_equal,
        "teammate_information_states_differ": teammate_states_differ,
        "commit_value_changes_across_hidden_states": commit_values == [10.0, -8.0],
        "commit_has_positive_expectation_and_negative_lower_bound": expected_commit > 0.0
        and min(commit_values) < 0.0,
        "defer_preserves_information_value": defer_values == [10.0, 0.0]
        and expected_defer > expected_commit,
        "bayes_information_aware_choice_is_defer": bayes_choice == "defer_for_ack",
        "certainty_equivalent_choice_is_commit": certainty_equivalent_choice == "commit_now",
        "ack_receipt_shrinks_information_set": ack_shrinks,
        "post_ack_choice_switches_to_commit": delivered_wait["endpoint"] == "joint_task_success",
        "constant_policy_does_not_match_contingent_value": contingent_value > max(constant_values.values()),
    }
    exact_registry = list(checks) == contract["required_checks"]
    passed = q0.get("verdict") == "P3_Q0_PASS_TO_TINY_LEARNABILITY_PILOT" and exact_registry and all(
        checks.values()
    )
    return {
        "protocol": "EPISTEMIC-COMMITMENT-P3-Q0B-IDENTIFIABILITY-AUDIT-V1",
        "verdict": "P3_Q0B_INFORMATION_GAP_PASS_WITH_INDUCTIVE_BIAS_SCOPE" if passed else "P3_Q0B_STOP",
        "checks": checks,
        "exact_check_registry": exact_registry,
        "pre_ack_commit_values": {"current_plan": commit_values[0], "no_plan": commit_values[1]},
        "defer_then_contingent_values": {"ack_current": defer_values[0], "no_ack": defer_values[1]},
        "fallback_now_values": {"current_plan": fallback_values[0], "no_plan": fallback_values[1]},
        "public_probability_current_plan": probability,
        "expected_commit_value": expected_commit,
        "expected_defer_then_contingent_value": expected_defer,
        "expected_fallback_now_value": expected_fallback,
        "bayes_action_values": bayes_values,
        "bayes_information_aware_choice": bayes_choice,
        "robust_action_values": robust_values,
        "robust_pre_ack_choice": robust_choice,
        "certainty_equivalent_choice": certainty_equivalent_choice,
        "constant_policy_expected_values": constant_values,
        "representational_impossibility_claim_allowed": False,
        "training_started": False,
        "ppo_updates": 0,
        "next_authorized_action": "retain Q1 learnability pilot; evaluate calibration and sample efficiency rather than representational impossibility",
        "evidence_boundary": (
            "The audit establishes a trajectory-grounded information gap and a Bayes value-of-information action switch "
            "under the frozen public prior. Strict maximin instead selects immediate fallback. "
            "A sufficiently trained GRU can still represent the contingent policy, so future evidence concerns "
            "inductive bias, calibration, reliability, and sample efficiency, not theoretical incapability."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit()
    payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        if args.output.exists():
            raise FileExistsError(args.output)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    if report["verdict"] == "P3_Q0B_STOP":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
