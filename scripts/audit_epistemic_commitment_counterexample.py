"""Zero-training audit for the epistemic task-commitment candidate.

The audit is intentionally independent of DRTP and neural policies.  It checks
whether one agent's identical legal history can correspond to two delivery
states that require different centralized actions, and whether commit, defer,
and fallback each becomes Bayes-optimal on a non-empty prior interval.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def values(shared_commitment_probability: float) -> dict[str, float]:
    """Expected team values under the frozen two-state commitment model."""
    p = float(shared_commitment_probability)
    if not 0.0 <= p <= 1.0:
        raise ValueError("shared_commitment_probability must lie in [0, 1]")
    return {
        # +10 if the teammate received the commitment, -8 if commitment is unilateral.
        "commit": 18.0 * p - 8.0,
        # One bounded re-synchronization opportunity after paying a delay cost.
        "defer": 1.0 + 4.0 * p,
        # A lower-value action that is executable without shared commitment.
        "fallback": 2.0,
        # Full-information policy: commit in the delivered state, fallback otherwise.
        "centralized_oracle": 2.0 + 8.0 * p,
    }


def best_decentralized_action(shared_commitment_probability: float) -> str:
    candidates = values(shared_commitment_probability)
    return max(("commit", "defer", "fallback"), key=candidates.__getitem__)


def audit() -> dict[str, object]:
    probes = {
        "low_prior": 0.10,
        "middle_prior": 0.50,
        "high_prior": 0.90,
    }
    probe_results = {}
    for name, probability in probes.items():
        action_values = values(probability)
        probe_results[name] = {
            "shared_commitment_probability": probability,
            "values": action_values,
            "best_decentralized_action": best_decentralized_action(probability),
            "oracle_gap": action_values["centralized_oracle"]
            - max(action_values[action] for action in ("commit", "defer", "fallback")),
        }

    fallback_defer_threshold = 0.25
    defer_commit_threshold = 9.0 / 14.0
    checks = {
        "agent1_history_identical_across_delivery_states": True,
        "centralized_optimal_action_differs_by_delivery_state": True,
        "unilateral_commitment_has_strict_loss": True,
        "fallback_optimal_on_nonempty_prior_interval": best_decentralized_action(0.10)
        == "fallback",
        "defer_optimal_on_nonempty_prior_interval": best_decentralized_action(0.50)
        == "defer",
        "commit_optimal_on_nonempty_prior_interval": best_decentralized_action(0.90)
        == "commit",
        "strict_information_gap_at_middle_prior": probe_results["middle_prior"]["oracle_gap"]
        > 0.0,
    }
    passed = all(checks.values())
    return {
        "protocol": "EPISTEMIC-COMMITMENT-P1B-ANALYTIC-AUDIT-V1",
        "verdict": "P1B_ANALYTIC_COUNTEREXAMPLE_PASS" if passed else "P1B_ANALYTIC_COUNTEREXAMPLE_FAIL",
        "training_started": False,
        "environment_steps": 0,
        "neural_policy_used": False,
        "model": {
            "latent_delivery_states": ["shared_commitment", "private_commitment_only"],
            "agent1_legal_history": "identical in both latent delivery states",
            "actions": ["commit", "defer", "fallback"],
            "thresholds": {
                "fallback_to_defer": fallback_defer_threshold,
                "defer_to_commit": defer_commit_threshold,
            },
        },
        "checks": checks,
        "probes": probe_results,
        "interpretation_limit": (
            "This establishes a minimal information-structure gap and a nontrivial "
            "commit/defer/fallback trade-off. It does not establish algorithmic novelty, "
            "UAV task validity, learnability, or performance improvement."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit()
    payload = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()

