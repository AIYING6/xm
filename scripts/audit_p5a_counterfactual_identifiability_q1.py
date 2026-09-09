#!/usr/bin/env python3
"""P5-A-Q1 zero-training counterexamples.

Shows (1) responsibility depends on the chosen default joint action and
(2) interventional transition distributions need not identify individual
counterfactual outcomes.  No policy learning is performed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def joint_cost(action: tuple[int, int]) -> int:
    return int(action == (1, 1))


def coalition_cost(
    actual: tuple[int, int], baseline: tuple[int, int], coalition: tuple[int, ...]
) -> int:
    action = list(baseline)
    for agent in coalition:
        action[agent] = actual[agent]
    return joint_cost(tuple(action))


def shapley(actual: tuple[int, int], baseline: tuple[int, int]) -> tuple[float, float]:
    v_empty = coalition_cost(actual, baseline, ())
    v_full = coalition_cost(actual, baseline, (0, 1))
    rho0 = 0.5 * (
        coalition_cost(actual, baseline, (0,)) - v_empty
        + v_full
        - coalition_cost(actual, baseline, (1,))
    )
    rho1 = 0.5 * (
        coalition_cost(actual, baseline, (1,)) - v_empty
        + v_full
        - coalition_cost(actual, baseline, (0,))
    )
    return rho0, rho1


def scm_outcome(model: str, action: int, noise: int) -> int:
    if model == "action_coupled":
        return action ^ noise
    if model == "action_irrelevant":
        return noise
    raise ValueError(model)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    actual = (1, 1)
    responsibilities = {
        "baseline_00": shapley(actual, (0, 0)),
        "baseline_10": shapley(actual, (1, 0)),
        "baseline_01": shapley(actual, (0, 1)),
    }

    # Both SCMs induce P(Y=1 | do(A=a)) = 0.5 for a in {0,1}; however,
    # under common exogenous noise, changing A flips Y in the first SCM and
    # never changes Y in the second.
    distributions: dict[str, dict[str, float]] = {}
    individual_effects: dict[str, list[int]] = {}
    for model in ("action_coupled", "action_irrelevant"):
        distributions[model] = {}
        individual_effects[model] = []
        for action in (0, 1):
            outcomes = [scm_outcome(model, action, u) for u in (0, 1)]
            distributions[model][f"p_y1_do_a{action}"] = sum(outcomes) / len(outcomes)
        for noise in (0, 1):
            individual_effects[model].append(
                scm_outcome(model, 1, noise) - scm_outcome(model, 0, noise)
            )

    checks = {
        "responsibility_changes_with_legal_baseline": len(set(responsibilities.values())) > 1,
        "interventional_distributions_match": (
            distributions["action_coupled"] == distributions["action_irrelevant"]
        ),
        "individual_counterfactual_effects_differ": (
            individual_effects["action_coupled"]
            != individual_effects["action_irrelevant"]
        ),
    }
    result = {
        "protocol": "P5-A-COUNTERFACTUAL-IDENTIFIABILITY-Q1-V1",
        "verdict": "P5A_IDENTIFIABILITY_AND_BASELINE_RISK_CONFIRMED",
        "training_started": False,
        "responsibilities": responsibilities,
        "interventional_distributions": distributions,
        "individual_counterfactual_effects": individual_effects,
        "checks": checks,
        "interpretation": (
            "A responsibility score is not intrinsic without a justified baseline, and "
            "transition/interventional distributions alone do not identify individual "
            "counterfactual effects without additional SCM assumptions."
        ),
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

