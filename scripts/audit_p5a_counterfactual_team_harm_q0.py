#!/usr/bin/env python3
"""Zero-training audit for P5-A counterfactual team avoidable harm.

The audit enumerates three one-step cooperative games.  It does not train a
policy and does not claim that the counterfactual quantity is identifiable
from observational trajectories.
"""

from __future__ import annotations

import argparse
import csv
import json
from itertools import combinations
from pathlib import Path


AGENTS = (0, 1)
DEFAULT_ACTION = (0, 0)


def cost(game: str, actions: tuple[int, int], exogenous_hazard: int) -> int:
    if exogenous_hazard:
        return 1
    if game == "joint_causation":
        return int(actions == (1, 1))
    if game == "agent0_only":
        return int(actions[0] == 1)
    if game == "no_avoidable_harm":
        return 0
    raise ValueError(game)


def avoidable_harm(game: str, actions: tuple[int, int], hazard: int) -> int:
    actual = cost(game, actions, hazard)
    default = cost(game, DEFAULT_ACTION, hazard)
    return max(actual - default, 0)


def coalition_value(
    game: str, actions: tuple[int, int], hazard: int, coalition: tuple[int, ...]
) -> int:
    mixed = list(DEFAULT_ACTION)
    for agent in coalition:
        mixed[agent] = actions[agent]
    return avoidable_harm(game, tuple(mixed), hazard)


def shapley_responsibility(
    game: str, actions: tuple[int, int], hazard: int
) -> tuple[float, float]:
    # Exact two-player Shapley value, written generically to make the audit
    # extension to more agents unambiguous.
    values: list[float] = []
    for agent in AGENTS:
        other = tuple(i for i in AGENTS if i != agent)
        empty_gain = coalition_value(game, actions, hazard, (agent,)) - coalition_value(
            game, actions, hazard, ()
        )
        full_gain = coalition_value(game, actions, hazard, AGENTS) - coalition_value(
            game, actions, hazard, other
        )
        values.append(0.5 * (empty_gain + full_gain))
    return values[0], values[1]


def enumerate_cases() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for game in ("joint_causation", "agent0_only", "no_avoidable_harm"):
        for hazard in (0, 1):
            for actions in ((0, 0), (0, 1), (1, 0), (1, 1)):
                harm = avoidable_harm(game, actions, hazard)
                rho = shapley_responsibility(game, actions, hazard)
                rows.append(
                    {
                        "game": game,
                        "hazard": hazard,
                        "action_0": actions[0],
                        "action_1": actions[1],
                        "team_cost": cost(game, actions, hazard),
                        "default_cost": cost(game, DEFAULT_ACTION, hazard),
                        "avoidable_harm": harm,
                        "rho_0": rho[0],
                        "rho_1": rho[1],
                        "efficiency_error": abs(sum(rho) - harm),
                    }
                )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    rows = enumerate_cases()
    csv_path = args.output_dir / "P5A_Q0_ANALYTIC_CASES.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    unavoidable = [r for r in rows if r["hazard"] == 1]
    joint = next(
        r
        for r in rows
        if r["game"] == "joint_causation"
        and r["hazard"] == 0
        and r["action_0"] == r["action_1"] == 1
    )
    null_case = next(
        r
        for r in rows
        if r["game"] == "agent0_only"
        and r["hazard"] == 0
        and r["action_0"] == r["action_1"] == 1
    )
    checks = {
        "unavoidable_cost_removed_from_harm": all(
            r["team_cost"] == 1 and r["avoidable_harm"] == 0 for r in unavoidable
        ),
        "joint_causation_shared_equally": joint["rho_0"] == joint["rho_1"] == 0.5,
        "null_agent_receives_zero_responsibility": (
            null_case["rho_0"] == 1.0 and null_case["rho_1"] == 0.0
        ),
        "shapley_efficiency_exact": all(r["efficiency_error"] == 0 for r in rows),
    }
    result = {
        "protocol": "P5-A-COUNTERFACTUAL-TEAM-HARM-Q0-V1",
        "verdict": "P5A_ANALYTIC_NONDEGENERACY_PASS" if all(checks.values()) else "P5A_STOP",
        "training_started": False,
        "cases": len(rows),
        "checks": checks,
        "scope": (
            "The result establishes algebraic non-degeneracy only; it does not establish "
            "novelty, observational identifiability, estimator accuracy, or policy improvement."
        ),
    }
    (args.output_dir / "P5A_Q0_ANALYTIC_RESULT.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

