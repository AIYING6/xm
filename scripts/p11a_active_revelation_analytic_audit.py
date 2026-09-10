#!/usr/bin/env python3
"""Analytic, zero-training identifiability audit for P11."""

from __future__ import annotations

import argparse
import itertools
import json
from collections import Counter
from pathlib import Path


def utilities(
    task_value: float,
    belief: float,
    future_value: float,
    inspection_cost: float,
    slack: float,
    inspection_duration: float,
) -> dict[str, float]:
    # Commit the scarce specialist now: current task succeeds, future option is lost.
    commit = task_value
    # Reserve it for the known future opportunity: current uncertain task is declined.
    reserve = future_value
    # Inspection reveals the requirement. With enough slack, the current task is
    # completed and the specialist is preserved exactly when it is not required.
    if slack >= inspection_duration:
        inspect = task_value + (1.0 - belief) * future_value - inspection_cost
    else:
        # Information arrives too late for the current task; the future option remains.
        inspect = future_value - inspection_cost
    return {"commit": commit, "reserve": reserve, "inspect": inspect}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cfg = json.loads(args.config.read_text(encoding="utf-8"))

    records = []
    product = itertools.product(
        cfg["belief_specialist_required"],
        cfg["future_specialist_opportunity_value"],
        cfg["inspection_cost"],
        cfg["deadline_slack"],
    )
    for belief, future_value, cost, slack in product:
        values = utilities(
            cfg["current_task_value"], belief, future_value, cost, slack,
            cfg["inspection_duration"],
        )
        optimal = max(values, key=values.get)
        records.append({
            "belief": belief,
            "future_value": future_value,
            "inspection_cost": cost,
            "deadline_slack": slack,
            "utilities": values,
            "optimal": optimal,
        })

    counts = Counter(record["optimal"] for record in records)
    fractions = {action: counts[action] / len(records) for action in utilities(1, .5, 1, 1, 1, 1)}
    fork_pairs = comparable_pairs = 0
    for left_index, left in enumerate(records):
        for right in records[left_index + 1:]:
            same_geometry = all(
                left[key] == right[key]
                for key in ("future_value", "inspection_cost", "deadline_slack")
            )
            if not same_geometry or left["belief"] == right["belief"]:
                continue
            comparable_pairs += 1
            fork_pairs += int(left["optimal"] != right["optimal"])
    fork_fraction = fork_pairs / comparable_pairs

    means = {
        action: sum(record["utilities"][action] for record in records) / len(records)
        for action in ("commit", "reserve", "inspect")
    }
    oracle_mean = sum(max(record["utilities"].values()) for record in records) / len(records)
    oracle_gain = oracle_mean - max(means.values())
    gates = cfg["gates"]
    checks = {
        "all_three_actions_have_optimal_regions": all(
            fractions[action] >= gates["minimum_fraction_per_optimal_action"]
            for action in fractions
        ),
        "same_geometry_belief_forks_sufficient": fork_fraction
        >= gates["minimum_same_geometry_belief_fork_fraction"],
        "oracle_gain_over_best_constant_sufficient": oracle_gain
        >= gates["minimum_oracle_gain_over_best_constant"],
        "inspection_positive_but_nonuniversal": 0.0 < fractions["inspect"] < 1.0,
        "training_started": False,
    }
    scientific = {key: value for key, value in checks.items() if key != "training_started"}
    result = {
        "protocol": cfg["protocol"],
        "verdict": "P11A_ANALYTIC_PASS" if all(scientific.values()) else "P11A_ANALYTIC_STOP",
        "case_count": len(records),
        "optimal_action_counts": counts,
        "optimal_action_fractions": fractions,
        "same_geometry_belief_pair_count": comparable_pairs,
        "same_geometry_belief_fork_fraction": fork_fraction,
        "mean_constant_policy_values": means,
        "oracle_mean_value": oracle_mean,
        "oracle_gain_over_best_constant": oracle_gain,
        "checks": checks,
        "training_started": False,
        "environment_steps": 0,
        "ppo_updates": 0,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
