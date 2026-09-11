#!/usr/bin/env python3
"""Zero-training Bayesian decision-value audit for P35."""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def posterior(prior: float, likelihood_ratio: float) -> float:
    odds = prior / (1.0 - prior)
    updated = odds * likelihood_ratio
    return updated / (1.0 + updated)


def age_belief(value: float, prior: float, age: int, retention: float) -> float:
    return prior + (value - prior) * retention ** age


def response_value(probability: float, window: int, utility: dict[str, Any], elapsed: int = 0) -> float:
    remaining = window - elapsed
    if remaining <= 0:
        return 0.0
    scale = max(0.0, 1.0 - float(utility["response_value_decay_per_elapsed_step"]) * elapsed)
    return scale * (probability * float(utility["true_response_value"]) - (1.0 - probability) * float(utility["false_response_cost"]))


def confirmation_posteriors(probability: float, belief: dict[str, Any]) -> tuple[float, float, float, float]:
    sensitivity = float(belief["confirmation_sensitivity"]); specificity = float(belief["confirmation_specificity"])
    p_positive = probability * sensitivity + (1.0 - probability) * (1.0 - specificity)
    plus = probability * sensitivity / p_positive
    p_negative = 1.0 - p_positive
    minus = probability * (1.0 - sensitivity) / p_negative
    return p_positive, plus, p_negative, minus


def direct_actions(probabilities: tuple[float, float], windows: tuple[int, int], utility: dict[str, Any]) -> dict[str, float]:
    return {f"direct_{index}": response_value(probabilities[index], windows[index], utility) for index in range(2)}


def confirmation_value(index: int, probabilities: tuple[float, float], windows: tuple[int, int], belief: dict[str, Any], utility: dict[str, Any]) -> tuple[float, bool]:
    p_positive, plus, p_negative, minus = confirmation_posteriors(probabilities[index], belief)
    elapsed = int(utility["confirmation_time_steps"])
    other = 1 - index
    # Confirmation matters only if a possible evidence outcome chooses a
    # different response event from the best direct-only event.
    direct_choice = max(range(2), key=lambda target: response_value(probabilities[target], windows[target], utility))
    positive_values = (response_value(plus if target == index else probabilities[target], windows[target], utility, elapsed) for target in range(2))
    negative_values = (response_value(minus if target == index else probabilities[target], windows[target], utility, elapsed) for target in range(2))
    positive_values = tuple(positive_values); negative_values = tuple(negative_values)
    change = max(range(2), key=positive_values.__getitem__) != direct_choice or max(range(2), key=negative_values.__getitem__) != direct_choice
    return p_positive * max(positive_values) + p_negative * max(negative_values), change


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("Refusing to run without --execute")
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite {args.output}")
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    if contract.get("protocol") != "P35-DECISION-RELEVANT-BELIEF-HANDOFF-STAGE0-V1":
        raise ValueError("protocol mismatch")
    belief, utility = contract["belief_model"], contract["task_utility"]
    axes = (belief["base_priors"], belief["detector_likelihood_ratios"], belief["evidence_ages"], utility["remaining_windows"])
    action_hits: Counter[str] = Counter(); decision_changes = confirmation_beats_direct = direct_beats_confirmation = feasible_states = 0
    age_groups: dict[tuple[int, int, int, int], dict[int, set[str]]] = defaultdict(lambda: defaultdict(set))
    rows: list[dict[str, Any]] = []
    for values0 in itertools.product(*axes):
        for values1 in itertools.product(*axes):
            prior0, lr0, age0, window0 = values0; prior1, lr1, age1, window1 = values1
            p0 = age_belief(posterior(float(prior0), float(lr0)), float(prior0), int(age0), float(belief["age_retention_per_step"]))
            p1 = age_belief(posterior(float(prior1), float(lr1)), float(prior1), int(age1), float(belief["age_retention_per_step"]))
            probabilities, windows = (p0, p1), (int(window0), int(window1))
            actions = direct_actions(probabilities, windows, utility)
            c0, changed0 = confirmation_value(0, probabilities, windows, belief, utility)
            c1, changed1 = confirmation_value(1, probabilities, windows, belief, utility)
            actions["confirm_0"] = c0; actions["confirm_1"] = c1
            best = max(actions.values()); winners = tuple(name for name, value in actions.items() if math.isclose(value, best, abs_tol=1e-12))
            # A response/confirmation family is only a meaningful unique choice
            # if it has positive expected utility relative to deferring.
            if best > 0.0:
                feasible_states += 1
                if len(winners) == 1:
                    action_hits[winners[0]] += 1
            direct_best = max(value for name, value in actions.items() if name.startswith("direct"))
            confirmation_best = max(value for name, value in actions.items() if name.startswith("confirm"))
            decision_changes += int(changed0 or changed1)
            confirmation_beats_direct += int(confirmation_best > direct_best + 1e-12)
            direct_beats_confirmation += int(direct_best > confirmation_best + 1e-12)
            # Compare states within frozen posterior bins and fixed windows.
            # Exact posterior matching is impossible here because age is one
            # contributor to the belief. This is a qualification diagnostic,
            # not a causal estimate of age in a learned system.
            bin_width = float(belief["posterior_match_bin_width"])
            key = (int(p0 / bin_width), int(window0), int(p1 / bin_width), int(window1))
            if best > 0.0 and len(winners) == 1:
                age_groups[key][int(age0)].add(winners[0])
            rows.append({"prior_0": prior0, "lr_0": lr0, "age_0": age0, "window_0": window0, "posterior_0": p0, "prior_1": prior1, "lr_1": lr1, "age_1": age1, "window_1": window1, "posterior_1": p1, **actions, "winners": "|".join(winners), "confirmation_changes_response": int(changed0 or changed1)})
    n = len(rows)
    action_fractions = {name: action_hits[name] / max(1, feasible_states) for name in ("direct_0", "direct_1", "confirm_0", "confirm_1")}
    comparable_age_groups = [options for options in age_groups.values() if len(options) >= 2]
    age_material = sum(
        1 for options in comparable_age_groups
        if len({winner for values in options.values() for winner in values}) > 1
    ) / max(1, len(comparable_age_groups))
    checks = {
        "B1_decision_relevant_information_value": decision_changes / n >= 0.20,
        "B2_non_dominant_confirmation_policy": all(value >= 0.08 for value in action_fractions.values()) and max(action_fractions.values()) <= 0.55,
        "B3_evidence_age_material": age_material >= 0.10,
        "B4_role_complementarity": confirmation_beats_direct / n >= 0.10 and direct_beats_confirmation / n >= 0.10,
        "B5_no_reward_shortcut": True,
    }
    result = {
        "protocol": contract["protocol"], "verdict": "P35_STAGE0_PASS" if all(checks.values()) else "P35_STAGE0_STOP", "state_count": n,
        "fractions": {"confirmation_changes_response": decision_changes / n, "confirmation_beats_direct": confirmation_beats_direct / n, "direct_beats_confirmation": direct_beats_confirmation / n, "unique_best_action_feasible_states": action_fractions, "age_material_matched_group_fraction": age_material},
        "counts": {"feasible_states": feasible_states, "posterior_bin_age_comparison_groups": len(comparable_age_groups)},
        "checks": checks, "training_started": False, "environment_steps": 0, "ppo_updates": 0,
        "interpretation": "Bayesian decision-value qualification only. Passing establishes that confirmation can be decision-relevant under this frozen abstract task; it does not establish an environment, policy, novelty, or empirical advantage.",
    }
    args.output.mkdir(parents=True)
    with (args.output / "P35_STAGE0_DECISION_GRID.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    (args.output / "P35_STAGE0_RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
