#!/usr/bin/env python3
"""Zero-training embodied identifiability audit for the only surviving P11 novelty delta."""

from __future__ import annotations

import argparse
import csv
import itertools
import json
from collections import Counter
from pathlib import Path


def future_value(value: float, distance: float, departure: float, speed: float, deadline: float) -> float:
    arrival = departure + distance / speed
    return value if arrival <= deadline else 0.0


def posterior(prior: float, positive: bool, accuracy: float) -> float:
    likelihood_required = accuracy if positive else 1.0 - accuracy
    likelihood_not = 1.0 - accuracy if positive else accuracy
    evidence = prior * likelihood_required + (1.0 - prior) * likelihood_not
    return prior * likelihood_required / evidence


def choose_after_belief(
    belief: float,
    current_value: float,
    future: float,
    specialist_arrival: float,
    current_deadline: float,
) -> tuple[str, float]:
    # Without specialist commitment, the current task succeeds only when the
    # latent specialist requirement is absent. Committing guarantees it only
    # if the specialist can still reach the site before the deadline.
    commit = current_value if specialist_arrival <= current_deadline else 0.0
    reserve = (1.0 - belief) * current_value + future
    return ("commit", commit) if commit >= reserve else ("reserve", reserve)


def active_value(case: dict[str, float], cfg: dict) -> tuple[float, bool, bool]:
    inspect_time = case["scout_distance"] / cfg["scout_speed"] + cfg["inspection_dwell"]
    specialist_arrival = inspect_time + case["specialist_current_distance"] / cfg["specialist_speed"]
    future = future_value(
        case["future_value"], case["specialist_future_distance"], inspect_time,
        cfg["specialist_speed"], cfg["future_deadline"],
    )
    expected = 0.0
    decisions = []
    for positive in (False, True):
        signal_probability = (
            case["prior"] * (cfg["inspection_accuracy"] if positive else 1.0 - cfg["inspection_accuracy"])
            + (1.0 - case["prior"]) * (1.0 - cfg["inspection_accuracy"] if positive else cfg["inspection_accuracy"])
        )
        post = posterior(case["prior"], positive, cfg["inspection_accuracy"])
        decision, value = choose_after_belief(
            post, case["current_value"], future, specialist_arrival, case["current_deadline"],
        )
        decisions.append(decision)
        expected += signal_probability * value
    return expected - cfg["inspection_energy_cost"], specialist_arrival <= case["current_deadline"], decisions[0] != decisions[1]


def aura_style_value(case: dict[str, float], cfg: dict) -> float:
    # Strong non-active baseline: while waiting for exogenous perfect revelation,
    # the specialist may stage toward the uncertain task. The staging fraction is
    # selected per case, so this is deliberately favorable to the baseline.
    values = []
    delay = cfg["exogenous_revelation_delay"]
    for fraction in cfg["staging_fractions"]:
        moved = min(delay * cfg["specialist_speed"], fraction * case["specialist_current_distance"])
        remaining_current = max(0.0, case["specialist_current_distance"] - moved)
        current_arrival = delay + remaining_current / cfg["specialist_speed"]
        # Moving toward the current task increases distance to the future task.
        staged_future_distance = case["specialist_future_distance"] + moved
        future = future_value(
            case["future_value"], staged_future_distance, delay,
            cfg["specialist_speed"], cfg["future_deadline"],
        )
        value = case["prior"] * (case["current_value"] if current_arrival <= case["current_deadline"] else 0.0)
        value += (1.0 - case["prior"]) * (case["current_value"] + future)
        values.append(value)
    return max(values)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    keys = (
        "current_task_value", "future_task_value", "specialist_required_prior",
        "scout_to_current_distance", "specialist_to_current_distance",
        "specialist_to_future_distance", "current_deadline",
    )
    rows = []
    for values in itertools.product(*(cfg[key] for key in keys)):
        raw = dict(zip(keys, values))
        case = {
            "current_value": raw["current_task_value"],
            "future_value": raw["future_task_value"],
            "prior": raw["specialist_required_prior"],
            "scout_distance": raw["scout_to_current_distance"],
            "specialist_current_distance": raw["specialist_to_current_distance"],
            "specialist_future_distance": raw["specialist_to_future_distance"],
            "current_deadline": raw["current_deadline"],
        }
        commit = case["current_value"]
        reserve = (1.0 - case["prior"]) * case["current_value"] + future_value(
            case["future_value"], case["specialist_future_distance"], 0.0,
            cfg["specialist_speed"], cfg["future_deadline"],
        )
        active, feasible, signal_flip = active_value(case, cfg)
        aura = aura_style_value(case, cfg)
        policies = {"commit": commit, "reserve": reserve, "active_reveal": active, "aura_style": aura}
        best = max(policies, key=policies.get)
        best_nonactive = max(commit, reserve, aura)
        rows.append({
            **case, **{f"value_{key}": value for key, value in policies.items()},
            "best_policy": best,
            "active_gain_over_best_nonactive": active - best_nonactive,
            "active_feasible": feasible,
            "signal_changes_commitment": signal_flip,
        })

    counts = Counter(row["best_policy"] for row in rows)
    n = len(rows)
    active_fraction = counts["active_reveal"] / n
    mean_gain = sum(row["active_gain_over_best_nonactive"] for row in rows) / n
    positive_fraction = sum(row["active_gain_over_best_nonactive"] > 1e-9 for row in rows) / n
    infeasible_fraction = sum(not row["active_feasible"] for row in rows) / n
    flip_fraction = sum(row["signal_changes_commitment"] for row in rows) / n

    # Same values/prior/deadlines but different scout/specialist geometry should
    # sometimes change the optimal decision if embodiment matters.
    grouped: dict[tuple, set[str]] = {}
    for row in rows:
        key = (row["current_value"], row["future_value"], row["prior"], row["current_deadline"])
        grouped.setdefault(key, set()).add(row["best_policy"])
    geometry_fork_fraction = sum(len(actions) > 1 for actions in grouped.values()) / len(grouped)

    gates = cfg["gates"]
    checks = {
        "active_has_nontrivial_optimal_region": gates["minimum_active_optimal_fraction"] <= active_fraction <= gates["maximum_active_optimal_fraction"],
        "active_mean_gain_over_nonactive": mean_gain >= gates["minimum_mean_gain_over_best_nonactive"],
        "active_beats_nonactive_in_enough_cases": positive_fraction >= gates["minimum_case_fraction_beating_best_nonactive"],
        "geometry_changes_optimal_action": geometry_fork_fraction >= gates["minimum_geometry_induced_action_fork_fraction"],
        "noisy_observation_changes_commitment": flip_fraction >= gates["minimum_noisy_signal_decision_flip_fraction"],
        "active_not_mostly_deadline_infeasible": infeasible_fraction <= gates["maximum_fraction_infeasible_before_deadline"],
    }
    result = {
        "protocol": cfg["protocol"],
        "verdict": "P11C_EMBODIED_IDENTIFIABILITY_PASS" if all(checks.values()) else "P11C_EMBODIED_IDENTIFIABILITY_STOP",
        "case_count": n,
        "best_policy_counts": counts,
        "best_policy_fractions": {key: value / n for key, value in counts.items()},
        "mean_active_gain_over_best_nonactive": mean_gain,
        "active_positive_gain_case_fraction": positive_fraction,
        "geometry_induced_action_fork_fraction": geometry_fork_fraction,
        "noisy_signal_decision_flip_fraction": flip_fraction,
        "active_deadline_infeasible_fraction": infeasible_fraction,
        "checks": checks,
        "training_started": False,
        "environment_steps": 0,
        "ppo_updates": 0,
    }
    args.output_dir.mkdir(parents=True, exist_ok=False)
    with (args.output_dir / "P11C_EMBODIED_IDENTIFIABILITY_CASES.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with (args.output_dir / "P11C_EMBODIED_IDENTIFIABILITY_RESULT.json").open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
