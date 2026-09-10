#!/usr/bin/env python3
"""Zero-training geometric Stage-0 for open-set team tactical response selection."""

from __future__ import annotations

import argparse
import copy
import csv
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class State:
    blue: np.ndarray
    red: np.ndarray
    blue_alive: np.ndarray
    red_alive: np.ndarray
    objectives_alive: np.ndarray
    step: int = 0


OBJECTIVES = np.asarray([[-0.88, 0.34], [-0.88, -0.34]], dtype=float)


def unit(delta: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(delta))
    return np.zeros_like(delta) if norm < 1e-12 else delta / norm


def move(position: np.ndarray, target: np.ndarray, speed: float) -> np.ndarray:
    return position + speed * unit(target - position)


def initial_state(seed: int) -> State:
    rng = np.random.default_rng(seed)
    blue = np.asarray([
        [-0.62, 0.32], [-0.62, -0.32], [-0.52, rng.uniform(-0.05, 0.05)]
    ]) + rng.normal(0.0, 0.015, (3, 2))
    red = np.asarray([
        [0.78, 0.30], [0.78, -0.30], [0.88, 0.0]
    ]) + rng.normal(0.0, 0.02, (3, 2))
    return State(blue, red, np.ones(3, bool), np.ones(3, bool), np.ones(2, bool))


def red_targets(state: State, tactic: str, decision_step: int) -> np.ndarray:
    left, right = OBJECTIVES
    if tactic == "left_mass":
        return np.tile(left, (3, 1))
    if tactic == "right_mass":
        return np.tile(right, (3, 1))
    if tactic == "split_raid":
        return np.asarray([left, right, left if state.step % 24 < 12 else right])
    if tactic == "feint_switch":
        # The switch is not encoded in reward or observations; it is a physical
        # trajectory change after a common early commitment toward the left.
        return np.tile(left if state.step < decision_step else right, (3, 1))
    raise ValueError(tactic)


def blue_targets(state: State, response: str) -> np.ndarray:
    left, right = OBJECTIVES
    alive_red = np.flatnonzero(state.red_alive)
    center = np.mean(state.red[alive_red], axis=0) if len(alive_red) else np.asarray([-0.2, 0.0])
    if response == "left_screen":
        return np.asarray([left + [0.13, 0.08], left + [0.13, -0.08], right + [0.10, 0.0]])
    if response == "right_screen":
        return np.asarray([left + [0.10, 0.0], right + [0.13, 0.08], right + [0.13, -0.08]])
    if response == "split_screen":
        return np.asarray([left + [0.12, 0.0], right + [0.12, 0.0], center])
    if response == "mobile_reserve":
        nearest = sorted(alive_red, key=lambda i: state.red[i, 0])[:2]
        targets = [state.red[i] for i in nearest]
        while len(targets) < 2:
            targets.append(np.asarray([-0.30, 0.0]))
        targets.append(np.asarray([-0.58, 0.0]))
        return np.asarray(targets)
    raise ValueError(response)


def step(state: State, tactic: str, response: str, cfg: dict) -> None:
    for i, target in enumerate(blue_targets(state, response)):
        if state.blue_alive[i]:
            state.blue[i] = move(state.blue[i], target, cfg["shared_rules"]["blue_speed"])
    for i, target in enumerate(red_targets(state, tactic, cfg["decision_step"])):
        if state.red_alive[i]:
            state.red[i] = move(state.red[i], target, cfg["shared_rules"]["red_speed"])

    radius = cfg["shared_rules"]["intercept_radius"]
    pairs = sorted(
        ((float(np.linalg.norm(state.blue[b] - state.red[r])), b, r)
         for b in np.flatnonzero(state.blue_alive) for r in np.flatnonzero(state.red_alive)),
        key=lambda item: item[0],
    )
    used_blue, used_red = set(), set()
    for distance, b, r in pairs:
        if distance > radius or b in used_blue or r in used_red:
            continue
        # Shared symmetric exchange rule for every tactic-response pair.
        state.blue_alive[b] = False
        state.red_alive[r] = False
        used_blue.add(b); used_red.add(r)
    for objective_index, objective in enumerate(OBJECTIVES):
        if state.objectives_alive[objective_index] and any(
            np.linalg.norm(state.red[r] - objective) <= cfg["shared_rules"]["objective_radius"]
            for r in np.flatnonzero(state.red_alive)
        ):
            state.objectives_alive[objective_index] = False
    state.step += 1


def utility(state: State, cfg: dict) -> float:
    rules = cfg["shared_rules"]
    return float(
        rules["objective_value"] * np.mean(state.objectives_alive)
        + rules["red_removal_value"] * (1.0 - np.mean(state.red_alive))
        + rules["blue_survival_value"] * np.mean(state.blue_alive)
    ) / (rules["objective_value"] + rules["red_removal_value"] + rules["blue_survival_value"])


def run_branch(base: State, tactic: str, pre_response: str, post_response: str, cfg: dict) -> State:
    state = copy.deepcopy(base)
    while state.step < cfg["decision_step"]:
        step(state, tactic, pre_response, cfg)
    while state.step < cfg["horizon_steps"] and np.any(state.objectives_alive) and np.any(state.red_alive):
        step(state, tactic, post_response, cfg)
    return state


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("Refusing to run without --execute")
    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    if cfg["protocol"] != "P12-OPEN-SET-TACTICAL-RESPONSE-STAGE0-V1":
        raise ValueError("protocol mismatch")
    if args.output_dir.exists():
        raise FileExistsError(args.output_dir)

    rows = []
    prefix_nonterminal = 0
    for scenario_id in range(cfg["scenario_count"]):
        base = initial_state(1_200_000 + scenario_id)
        # A neutral split screen is shared before the response decision.
        prefix = copy.deepcopy(base)
        while prefix.step < cfg["decision_step"]:
            step(prefix, "split_raid", "split_screen", cfg)
        prefix_nonterminal += int(np.any(prefix.objectives_alive) and np.any(prefix.red_alive))
        for tactic in cfg["red_tactics"]:
            for response in cfg["blue_responses"]:
                end = run_branch(base, tactic, "split_screen", response, cfg)
                rows.append({
                    "scenario_id": scenario_id, "red_tactic": tactic, "blue_response": response,
                    "utility": utility(end, cfg),
                    "objectives_survived": int(np.sum(end.objectives_alive)),
                    "red_removed": int(3 - np.sum(end.red_alive)),
                    "blue_survived": int(np.sum(end.blue_alive)),
                })

    mean_by_pair = {
        (tactic, response): float(np.mean([r["utility"] for r in rows if r["red_tactic"] == tactic and r["blue_response"] == response]))
        for tactic in cfg["red_tactics"] for response in cfg["blue_responses"]
    }
    best_by_tactic = {}
    for tactic in cfg["red_tactics"]:
        ranking = sorted(((mean_by_pair[(tactic, response)], response) for response in cfg["blue_responses"]), reverse=True)
        best_by_tactic[tactic] = {"response": ranking[0][1], "value": ranking[0][0], "margin": ranking[0][0] - ranking[1][0]}
    best_counts = Counter(item["response"] for item in best_by_tactic.values())
    distinct = len(best_counts)
    dominance = max(best_counts.values()) / len(cfg["red_tactics"])
    static_values = {
        response: float(np.mean([mean_by_pair[(tactic, response)] for tactic in cfg["red_tactics"]]))
        for response in cfg["blue_responses"]
    }
    oracle = float(np.mean([item["value"] for item in best_by_tactic.values()]))
    best_static = max(static_values.values())
    oracle_gain = oracle - best_static
    margin_count = sum(item["margin"] >= cfg["gates"]["minimum_best_response_margin"] for item in best_by_tactic.values())
    nonterminal_fraction = prefix_nonterminal / cfg["scenario_count"]
    checks = {
        "response_library_complementary": distinct >= cfg["gates"]["minimum_distinct_best_responses"],
        "no_universal_response": dominance <= cfg["gates"]["maximum_single_response_dominance"],
        "oracle_headroom_sufficient": oracle_gain >= cfg["gates"]["minimum_oracle_gain_over_best_static"],
        "best_response_margins_sufficient": margin_count >= cfg["gates"]["minimum_tactics_with_margin"],
        "decision_occurs_before_outcome": nonterminal_fraction >= cfg["gates"]["minimum_nonterminal_prefix_fraction"],
    }
    result = {
        "protocol": cfg["protocol"],
        "verdict": "P12_STAGE0_PASS" if all(checks.values()) else "P12_STAGE0_STOP",
        "case_count": len(rows), "best_by_tactic": best_by_tactic,
        "distinct_best_responses": distinct, "single_response_dominance": dominance,
        "oracle_mean": oracle, "best_static_mean": best_static, "oracle_gain": oracle_gain,
        "static_response_values": static_values, "nonterminal_prefix_fraction": nonterminal_fraction,
        "checks": checks, "training_started": False, "environment_steps": 0, "ppo_updates": 0,
    }
    args.output_dir.mkdir(parents=True)
    with (args.output_dir / "P12_STAGE0_CROSSPLAY.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    (args.output_dir / "P12_STAGE0_RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
