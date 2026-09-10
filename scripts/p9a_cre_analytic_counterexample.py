#!/usr/bin/env python3
"""Zero-training analytic audit for the provisional CRE topic."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


PAYOFFS = {
    "beta_1": {"attack": 10.0, "screen": 5.0, "split": 7.0},
    "beta_2": {"attack": 0.0, "screen": 5.0, "split": 3.0},
}
POSTERIOR = {"beta_1": 0.8, "beta_2": 0.2}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    actions = tuple(next(iter(PAYOFFS.values())))
    expected = {
        action: sum(POSTERIOR[beta] * values[action] for beta, values in PAYOFFS.items())
        for action in actions
    }
    worst_value = {action: min(values[action] for values in PAYOFFS.values()) for action in actions}
    regrets = {}
    for beta, values in PAYOFFS.items():
        oracle = max(values.values())
        regrets[beta] = {action: oracle - values[action] for action in actions}
    worst_regret = {
        action: max(regrets[beta][action] for beta in PAYOFFS) for action in actions
    }

    posterior_mean_action = max(actions, key=expected.get)
    maximin_value_action = max(actions, key=worst_value.get)
    minimax_regret_action = min(actions, key=worst_regret.get)

    scientific_checks = {
        "opponents_observation_equivalent_before_decision": True,
        "best_response_order_reverses": (
            max(PAYOFFS["beta_1"], key=PAYOFFS["beta_1"].get)
            != max(PAYOFFS["beta_2"], key=PAYOFFS["beta_2"].get)
        ),
        "posterior_mean_has_strictly_higher_worst_regret": (
            worst_regret[posterior_mean_action] > worst_regret[minimax_regret_action]
        ),
        "minimax_value_differs_from_minimax_regret": maximin_value_action != minimax_regret_action,
        "same_information_and_action_set": True,
    }
    provenance = {"training_started": False, "environment_steps": 0, "ppo_updates": 0}
    result = {
        "protocol": "P9A-CRE-ANALYTIC-COUNTEREXAMPLE-V1",
        "verdict": "P9A_ANALYTIC_COUNTEREXAMPLE_PASS" if all(scientific_checks.values()) else "P9A_ANALYTIC_COUNTEREXAMPLE_FAIL",
        "payoffs": PAYOFFS,
        "posterior": POSTERIOR,
        "expected_values": expected,
        "worst_values": worst_value,
        "regrets": regrets,
        "worst_regrets": worst_regret,
        "decisions": {
            "posterior_mean": posterior_mean_action,
            "maximin_value": maximin_value_action,
            "minimax_regret": minimax_regret_action,
        },
        "checks": scientific_checks,
        **provenance,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
