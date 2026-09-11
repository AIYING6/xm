#!/usr/bin/env python3
"""Zero-training identifiability audit for P35B.

This script uses the already frozen P35 Bayesian contract.  It neither edits the
contract nor changes its priors, likelihoods, utilities, windows, or retention.
It measures whether confirmation value is specifically tied to a capacity-limited
responder allocation, rather than being a restatement of posterior entropy.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
from pathlib import Path
from typing import Any


def posterior(prior: float, likelihood_ratio: float) -> float:
    odds = prior / (1.0 - prior)
    updated = odds * likelihood_ratio
    return updated / (1.0 + updated)


def age_belief(value: float, prior: float, age: int, retention: float) -> float:
    return prior + (value - prior) * retention**age


def entropy(probability: float) -> float:
    if probability <= 0.0 or probability >= 1.0:
        return 0.0
    return -probability * math.log(probability) - (1.0 - probability) * math.log(1.0 - probability)


def response_value(probability: float, window: int, utility: dict[str, Any], elapsed: int = 0) -> float:
    if window - elapsed <= 0:
        return 0.0
    scale = max(0.0, 1.0 - float(utility["response_value_decay_per_elapsed_step"]) * elapsed)
    return scale * (
        probability * float(utility["true_response_value"])
        - (1.0 - probability) * float(utility["false_response_cost"])
    )


def confirmation_posteriors(probability: float, belief: dict[str, Any]) -> tuple[float, float, float, float]:
    sensitivity = float(belief["confirmation_sensitivity"])
    specificity = float(belief["confirmation_specificity"])
    positive_probability = probability * sensitivity + (1.0 - probability) * (1.0 - specificity)
    positive = probability * sensitivity / positive_probability
    negative_probability = 1.0 - positive_probability
    negative = probability * (1.0 - sensitivity) / negative_probability
    return positive_probability, positive, negative_probability, negative


def allocation(values: tuple[float, float], capacity: int) -> tuple[int, ...]:
    """Return the positive-value event indices selected by a bounded responder."""
    ranked = sorted(range(len(values)), key=values.__getitem__, reverse=True)
    return tuple(index for index in ranked[:capacity] if values[index] > 0.0)


def allocation_utility(values: tuple[float, float], capacity: int) -> float:
    return sum(values[index] for index in allocation(values, capacity))


def confirmation_value(
    event: int,
    probabilities: tuple[float, float],
    windows: tuple[int, int],
    belief: dict[str, Any],
    utility: dict[str, Any],
    capacity: int,
) -> tuple[float, bool]:
    direct_values = tuple(response_value(probabilities[index], windows[index], utility) for index in range(2))
    direct_allocation = allocation(direct_values, capacity)
    positive_probability, positive, negative_probability, negative = confirmation_posteriors(probabilities[event], belief)
    elapsed = int(utility["confirmation_time_steps"])

    def post_values(updated: float) -> tuple[float, float]:
        return tuple(
            response_value(updated if index == event else probabilities[index], windows[index], utility, elapsed)
            for index in range(2)
        )

    positive_values = post_values(positive)
    negative_values = post_values(negative)
    switches = (
        allocation(positive_values, capacity) != direct_allocation
        or allocation(negative_values, capacity) != direct_allocation
    )
    value = (
        positive_probability * allocation_utility(positive_values, capacity)
        + negative_probability * allocation_utility(negative_values, capacity)
    )
    return value, switches


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
        raise ValueError("unexpected frozen P35 contract")
    belief, utility = contract["belief_model"], contract["task_utility"]
    axes = (
        belief["base_priors"], belief["detector_likelihood_ratios"], belief["evidence_ages"], utility["remaining_windows"],
    )
    rows: list[dict[str, Any]] = []
    capacity_stats = {1: {"positive_dsv": 0, "switch_positive_dsv": 0, "switches": 0}, 2: {"positive_dsv": 0, "switch_positive_dsv": 0, "switches": 0}}
    entropy_bins: dict[tuple[int, int, int], set[str]] = {}

    for event0 in itertools.product(*axes):
        for event1 in itertools.product(*axes):
            prior0, lr0, age0, window0 = event0
            prior1, lr1, age1, window1 = event1
            probabilities = (
                age_belief(posterior(float(prior0), float(lr0)), float(prior0), int(age0), float(belief["age_retention_per_step"])),
                age_belief(posterior(float(prior1), float(lr1)), float(prior1), int(age1), float(belief["age_retention_per_step"])),
            )
            windows = (int(window0), int(window1))
            base_entropy = entropy(probabilities[0]) + entropy(probabilities[1])
            result: dict[str, Any] = {
                "prior_0": prior0, "lr_0": lr0, "age_0": age0, "window_0": window0,
                "prior_1": prior1, "lr_1": lr1, "age_1": age1, "window_1": window1,
                "posterior_0": probabilities[0], "posterior_1": probabilities[1], "joint_entropy": base_entropy,
            }
            for capacity in (1, 2):
                direct_values = tuple(response_value(probabilities[index], windows[index], utility) for index in range(2))
                direct_utility = allocation_utility(direct_values, capacity)
                dsvs: list[float] = []
                switches: list[bool] = []
                for event in range(2):
                    confirmation, switch = confirmation_value(event, probabilities, windows, belief, utility, capacity)
                    dsv = confirmation - direct_utility
                    dsvs.append(dsv); switches.append(switch)
                    result[f"dsv_c{capacity}_event_{event}"] = dsv
                    result[f"switch_c{capacity}_event_{event}"] = int(switch)
                best_dsv = max(dsvs)
                any_switch = any(switches)
                positive = best_dsv > 1e-12
                capacity_stats[capacity]["positive_dsv"] += int(positive)
                capacity_stats[capacity]["switch_positive_dsv"] += int(positive and any_switch)
                capacity_stats[capacity]["switches"] += int(any_switch)
                result[f"best_dsv_c{capacity}"] = best_dsv
                result[f"any_switch_c{capacity}"] = int(any_switch)
                result[f"direct_allocation_c{capacity}"] = "|".join(map(str, allocation(direct_values, capacity)))
            entropy_key = (round(base_entropy, 2), windows[0], windows[1])
            entropy_bins.setdefault(entropy_key, set()).add(result["direct_allocation_c1"])
            rows.append(result)

    total = len(rows)
    entropy_ambiguous = sum(1 for allocations in entropy_bins.values() if len(allocations) > 1)
    report = {
        "protocol": "P35B-DECISION-SWITCHING-IDENTIFIABILITY-AUDIT-V1",
        "source_contract": contract["protocol"],
        "state_count": total,
        "capacity_comparison": {
            str(capacity): {
                "positive_dsv_fraction": stats["positive_dsv"] / total,
                "positive_dsv_with_decision_switch_fraction": stats["switch_positive_dsv"] / total,
                "any_decision_switch_fraction": stats["switches"] / total,
            }
            for capacity, stats in capacity_stats.items()
        },
        "decision_equivalence": {
            "entropy_window_bins": len(entropy_bins),
            "same_entropy_window_bins_with_multiple_capacity1_response_allocations": entropy_ambiguous,
            "fraction": entropy_ambiguous / max(1, len(entropy_bins)),
        },
        "interpretation": (
            "This is a read-only analytical audit under the frozen P35 parameters. "
            "It can show whether DSV is associated with responder-capacity allocation changes; "
            "it cannot establish novelty, learned-policy performance, or causal superiority."
        ),
        "training_started": False,
        "environment_steps": 0,
        "ppo_updates": 0,
    }
    args.output.mkdir(parents=True)
    with (args.output / "P35B_IDENTIFIABILITY_GRID.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    (args.output / "P35B_IDENTIFIABILITY_RESULT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
