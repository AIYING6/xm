#!/usr/bin/env python3
"""Zero-training audit for task-level recoverability.

The finite example shows that task recoverability can differ while immediate
safety and nominal feasibility are equal, but is exactly representable as a
goal-conditioned robust reachability query.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


STATES = {
    "reserve_preserved": (2, 2),
    "reserve_depleted": (2, 1),
}
FAILURES = ("agent0_fails", "agent1_fails")
TASK_ENERGY_REQUIRED = 2


def nominal_feasible(energies: tuple[int, int]) -> bool:
    return max(energies) >= TASK_ENERGY_REQUIRED


def immediate_safe(energies: tuple[int, int]) -> bool:
    return all(energy >= 0 for energy in energies)


def completion_after_failure(energies: tuple[int, int], failure: str) -> bool:
    survivor = energies[1] if failure == "agent0_fails" else energies[0]
    return survivor >= TASK_ENERGY_REQUIRED


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    rows: dict[str, object] = {}
    for name, energies in STATES.items():
        outcomes = {
            failure: completion_after_failure(energies, failure)
            for failure in FAILURES
        }
        recoverability = sum(outcomes.values()) / len(outcomes)
        robust_goal_reachable = all(outcomes.values())
        rows[name] = {
            "energies": energies,
            "communication_complete": True,
            "immediate_safe": immediate_safe(energies),
            "nominal_task_feasible": nominal_feasible(energies),
            "failure_completion": outcomes,
            "recoverability_fraction": recoverability,
            "robust_goal_reachable": robust_goal_reachable,
        }

    preserved = rows["reserve_preserved"]
    depleted = rows["reserve_depleted"]
    checks = {
        "same_connectivity": (
            preserved["communication_complete"] == depleted["communication_complete"]
        ),
        "same_immediate_safety": preserved["immediate_safe"] == depleted["immediate_safe"],
        "same_nominal_feasibility": (
            preserved["nominal_task_feasible"] == depleted["nominal_task_feasible"]
        ),
        "different_task_recoverability": (
            preserved["recoverability_fraction"] != depleted["recoverability_fraction"]
        ),
        "recoverability_equals_failure_conditioned_goal_reachability": all(
            data["robust_goal_reachable"]
            == all(data["failure_completion"].values())
            for data in rows.values()
        ),
    }
    result = {
        "protocol": "P5-B-TASK-RECOVERABILITY-Q0-V1",
        "verdict": "P5B_DISTINCT_FROM_NARROW_SAFETY_BUT_REDUCIBLE_TO_ROBUST_REACHABILITY",
        "training_started": False,
        "states": rows,
        "checks": checks,
        "interpretation": (
            "Task recoverability is not connectivity or immediate safety, but in this "
            "finite construction it is a goal-conditioned robust reachability quantity."
        ),
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

