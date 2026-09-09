#!/usr/bin/env python3
"""Zero-training identifiability audit for the CIRU escort-interception task.

This is deliberately a compact deterministic task model, not a learning
environment.  Every intent and response uses the same kinematics, interception
rules and utility.  The audit forks identical runtime states at the frozen
decision step to obtain paired counterfactual outcomes.
"""
from __future__ import annotations

import argparse
import copy
import csv
import json
import math
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np


INTENTS = ("direct_strike", "split_saturation", "decoy_flank", "defender_attrition")
RESPONSES = ("close_escort", "forward_intercept", "split_screen", "reserve_counter")
PRE_POLICIES = ("close_escort", "forward_intercept")


@dataclass
class State:
    blue: np.ndarray
    red: np.ndarray
    blue_alive: np.ndarray
    red_alive: np.ndarray
    step: int = 0
    asset_failed: bool = False
    asset_exited: bool = False


def unit(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    return np.zeros_like(v) if n < 1e-12 else v / n


def move_toward(position: np.ndarray, target: np.ndarray, speed: float) -> np.ndarray:
    return position + speed * unit(target - position)


def initial_state(rng: np.random.Generator) -> State:
    asset = np.array([-0.82, rng.uniform(-0.04, 0.04)])
    defenders = np.array([
        asset + [-0.02, 0.16 + rng.uniform(-0.025, 0.025)],
        asset + [-0.02, -0.16 + rng.uniform(-0.025, 0.025)],
    ])
    red = np.array([
        [0.70 + rng.uniform(-0.025, 0.025), 0.15 + rng.uniform(-0.04, 0.04)],
        [0.70 + rng.uniform(-0.025, 0.025), -0.15 + rng.uniform(-0.04, 0.04)],
        [0.78 + rng.uniform(-0.025, 0.025), rng.uniform(-0.06, 0.06)],
    ])
    return State(np.vstack([asset, defenders]), red, np.ones(3, bool), np.ones(3, bool))


def blue_targets(state: State, response: str) -> np.ndarray:
    asset = state.blue[0]
    live_red = np.flatnonzero(state.red_alive)
    fallback = asset + np.array([0.12, 0.0])
    targets = np.tile(fallback, (2, 1))
    if response == "close_escort":
        targets[0] = asset + [0.10, 0.13]
        targets[1] = asset + [0.10, -0.13]
    elif response == "forward_intercept":
        if len(live_red):
            lead = live_red[np.argmin(state.red[live_red, 0])]
            targets[:] = state.red[lead]
    elif response == "split_screen":
        upper = [i for i in live_red if state.red[i, 1] >= asset[1]]
        lower = [i for i in live_red if state.red[i, 1] < asset[1]]
        targets[0] = state.red[min(upper, key=lambda i: state.red[i, 0])] if upper else asset + [0.10, 0.18]
        targets[1] = state.red[min(lower, key=lambda i: state.red[i, 0])] if lower else asset + [0.10, -0.18]
    elif response == "reserve_counter":
        if len(live_red):
            lead = live_red[np.argmin(state.red[live_red, 0])]
            targets[0] = state.red[lead]
        targets[1] = asset + [0.04, 0.0]
    else:
        raise ValueError(response)
    return targets


def red_targets(state: State, intent: str) -> np.ndarray:
    asset = state.blue[0]
    defenders = [i for i in (1, 2) if state.blue_alive[i]]
    # A common ingress makes intent inference non-trivial without hiding state.
    if state.step < 34:
        return np.array([[-0.05, 0.12], [-0.05, -0.12], [0.02, 0.0]])
    if intent == "direct_strike":
        return np.tile(asset, (3, 1))
    if intent == "split_saturation":
        return np.array([asset + [0.0, 0.11], asset + [0.0, -0.11], asset])
    if intent == "decoy_flank":
        upper_defender = state.blue[1] if state.blue_alive[1] else asset
        return np.array([asset, asset + [0.0, -0.18], upper_defender + [0.0, 0.25]])
    if intent == "defender_attrition":
        if defenders:
            target = state.blue[min(defenders, key=lambda i: np.linalg.norm(state.blue[i] - np.mean(state.red, axis=0)))]
            return np.tile(target, (3, 1))
        return np.tile(asset, (3, 1))
    raise ValueError(intent)


def step_state(state: State, intent: str, response: str) -> None:
    if state.asset_failed or state.asset_exited:
        return
    # Protected asset follows a fixed mission corridor; only defenders are controlled.
    state.blue[0, 0] += 0.0075
    state.blue[0, 1] *= 0.985
    btargets = blue_targets(state, response)
    for j, i in enumerate((1, 2)):
        if state.blue_alive[i]:
            state.blue[i] = move_toward(state.blue[i], btargets[j], 0.016)
    rtargets = red_targets(state, intent)
    red_speed = {"direct_strike": 0.0135, "split_saturation": 0.013,
                 "decoy_flank": 0.0135, "defender_attrition": 0.014}[intent]
    for i in np.flatnonzero(state.red_alive):
        state.red[i] = move_toward(state.red[i], rtargets[i], red_speed)

    # Uniform geometric interaction rules; no intent/response-specific reward or hit table.
    for bi in (1, 2):
        if not state.blue_alive[bi]:
            continue
        for ri in np.flatnonzero(state.red_alive):
            d = float(np.linalg.norm(state.blue[bi] - state.red[ri]))
            if d <= 0.035:
                # Symmetric close-range exchange for every intent and response.
                state.red_alive[ri] = False
                state.blue_alive[bi] = False
                break
            if d <= 0.040:
                state.red_alive[ri] = False
                break
    for ri in np.flatnonzero(state.red_alive):
        if np.linalg.norm(state.red[ri] - state.blue[0]) <= 0.047:
            state.asset_failed = True
    if state.blue[0, 0] >= 0.86 and not state.asset_failed:
        state.asset_exited = True
    state.step += 1


def behavior_vector(state: State) -> np.ndarray:
    asset = state.blue[0]
    rel = state.red - asset
    live = state.red_alive.astype(float)
    nearest_asset = float(np.min(np.linalg.norm(rel[state.red_alive], axis=1))) if np.any(state.red_alive) else 0.0
    live_def = state.blue_alive[1:]
    if np.any(live_def) and np.any(state.red_alive):
        d = [np.linalg.norm(state.red[r] - state.blue[b]) for r in np.flatnonzero(state.red_alive) for b in (1, 2) if state.blue_alive[b]]
        nearest_def = float(min(d))
    else:
        nearest_def = 0.0
    return np.asarray([
        float(np.mean(rel[:, 0])), float(np.mean(rel[:, 1])),
        float(np.std(rel[:, 1])), nearest_asset, nearest_def,
        float(np.mean(live)), float(np.mean(live_def)),
    ])


def trace_prefix(state: State, intent: str, pre_policy: str, decision_step: int) -> tuple[State, np.ndarray]:
    values = []
    while state.step < decision_step and not (state.asset_failed or state.asset_exited):
        step_state(state, intent, pre_policy)
        values.append(behavior_vector(state))
    arr = np.stack(values)
    return state, np.concatenate([np.mean(arr, axis=0), arr[-1], arr[-1] - arr[0]])


def finish(state: State, intent: str, response: str, horizon: int) -> dict[str, float]:
    while state.step < horizon and not (state.asset_failed or state.asset_exited):
        step_state(state, intent, response)
    progress = float(np.clip((state.blue[0, 0] + 0.82) / 1.68, 0.0, 1.0))
    defenders_alive = float(np.mean(state.blue_alive[1:]))
    red_removed = 1.0 - float(np.mean(state.red_alive))
    success = float(state.asset_exited and not state.asset_failed)
    # One common mission utility, normalized to [0, 1].
    utility = float(np.clip(0.55 * success + 0.20 * progress + 0.15 * defenders_alive + 0.10 * red_removed, 0.0, 1.0))
    return {"utility": utility, "success": success, "progress": progress,
            "defenders_alive": defenders_alive, "red_removed": red_removed,
            "asset_failed": float(state.asset_failed), "steps": float(state.step)}


def distance(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.sqrt(np.mean((a - b) ** 2)))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--contract", type=Path, required=True)
    ap.add_argument("--output-root", type=Path, required=True)
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args()
    if not args.execute:
        raise SystemExit("Refusing to run without --execute")
    c = json.loads(args.contract.read_text(encoding="utf-8"))
    if c.get("protocol") != "P6-CIRU-ESCORT-INTERCEPTION-STAGE0-FREEZE-V1":
        raise ValueError("contract mismatch")
    if args.output_root.exists():
        raise FileExistsError(args.output_root)
    n, decision, horizon = c["stage0"]["scenario_count"], c["decision_step"], c["horizon_steps"]
    outcomes: list[dict[str, Any]] = []
    prefix: dict[tuple[int, str, str], np.ndarray] = {}
    for sid in range(n):
        base = initial_state(np.random.default_rng(970_000 + sid))
        for intent in INTENTS:
            for pre in PRE_POLICIES:
                branch, vec = trace_prefix(copy.deepcopy(base), intent, pre, decision)
                prefix[(sid, intent, pre)] = vec
                for response in RESPONSES:
                    result = finish(copy.deepcopy(branch), intent, response, horizon)
                    outcomes.append({"scenario_id": sid, "intent": intent, "pre_policy": pre,
                                     "response": response, **result})

    z1_values = []
    for sid in range(n):
        for intent in INTENTS:
            z1_values.append(distance(prefix[(sid, intent, PRE_POLICIES[0])], prefix[(sid, intent, PRE_POLICIES[1])]))
    z1c = c["stage0"]["z1"]
    z1_fraction = float(np.mean(np.asarray(z1_values) >= z1c["minimum_median_standardized_distance"]))
    z1_median = float(np.median(z1_values))
    z1_pass = z1_fraction >= z1c["minimum_shifted_case_fraction"] and z1_median >= z1c["minimum_median_standardized_distance"]

    # Z2 uses the same pre-policy and compares intent-level prefix distributions.
    ref_pre = PRE_POLICIES[0]
    mean_prefix = {i: np.mean([prefix[(sid, i, ref_pre)] for sid in range(n)], axis=0) for i in INTENTS}
    mean_u = {(i, r): float(np.mean([o["utility"] for o in outcomes if o["intent"] == i and o["pre_policy"] == ref_pre and o["response"] == r])) for i in INTENTS for r in RESPONSES}
    best = {}
    for i in INTENTS:
        order = sorted(((mean_u[(i, r)], r) for r in RESPONSES), reverse=True)
        best[i] = (order[0][1], order[0][0] - order[1][0])
    z2_rows = []
    for a, b in combinations(INTENTS, 2):
        d = distance(mean_prefix[a], mean_prefix[b])
        qualifies = d <= c["stage0"]["z2"]["maximum_alias_distance"] and best[a][0] != best[b][0] and min(best[a][1], best[b][1]) >= c["stage0"]["z2"]["minimum_best_response_margin_normalized"]
        z2_rows.append({"intent_a": a, "intent_b": b, "prefix_distance": d,
                        "best_a": best[a][0], "margin_a": best[a][1],
                        "best_b": best[b][0], "margin_b": best[b][1], "qualifies": int(qualifies)})
    z2_count = sum(r["qualifies"] for r in z2_rows)
    z2_pass = z2_count >= c["stage0"]["z2"]["minimum_qualifying_intent_pairs"]

    distinct = len({v[0] for v in best.values()})
    dominance = max(sum(v[0] == r for v in best.values()) for r in RESPONSES) / len(INTENTS)
    scenario_oracle, static = [], []
    for sid in range(n):
        vals = {(i, r): next(o["utility"] for o in outcomes if o["scenario_id"] == sid and o["intent"] == i and o["pre_policy"] == ref_pre and o["response"] == r) for i in INTENTS for r in RESPONSES}
        scenario_oracle.extend(max(vals[(i, r)] for r in RESPONSES) for i in INTENTS)
        static.append({r: np.mean([vals[(i, r)] for i in INTENTS]) for r in RESPONSES})
    oracle_mean = float(np.mean(scenario_oracle))
    static_best = max(float(np.mean([x[r] for x in static])) for r in RESPONSES)
    oracle_gain = oracle_mean - static_best
    z3c = c["stage0"]["z3"]
    z3_pass = distinct >= z3c["minimum_distinct_best_responses"] and dominance <= z3c["maximum_universal_dominance_fraction"] and oracle_gain >= z3c["minimum_oracle_gain_over_best_static_normalized"]
    verdict = "CIRU_ESCORT_STAGE0_PASS" if z1_pass and z2_pass and z3_pass else "CIRU_ESCORT_STAGE0_STOP"
    report = {"protocol": c["protocol"], "verdict": verdict, "training_started": False,
              "z1": {"pass": z1_pass, "shifted_fraction": z1_fraction, "median_distance": z1_median},
              "z2": {"pass": z2_pass, "qualifying_pairs": int(z2_count), "pairs": len(z2_rows)},
              "z3": {"pass": z3_pass, "distinct_best_responses": distinct,
                     "universal_dominance_fraction": dominance, "oracle_mean": oracle_mean,
                     "best_static_mean": static_best, "oracle_gain": oracle_gain,
                     "best_by_intent": {i: {"response": best[i][0], "margin": best[i][1]} for i in INTENTS}},
              "boundary": "A Stage-0 pass establishes task identifiability only; it does not establish learnability, CIRU performance, or publication-level evidence."}
    args.output_root.mkdir(parents=True)
    write_csv(args.output_root / "paired_counterfactual_outcomes.csv", outcomes)
    write_csv(args.output_root / "z2_alias_pairs.csv", z2_rows)
    (args.output_root / "P6_CIRU_ESCORT_STAGE0_REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (args.output_root / "P6_CIRU_ESCORT_STAGE0_REPORT.md").write_text(
        f"# CIRU escort-interception Stage-0\n\n**`{verdict}`**\n\n"
        f"- Z1: {'PASS' if z1_pass else 'FAIL'}; shifted={z1_fraction:.3f}, median distance={z1_median:.4f}.\n"
        f"- Z2: {'PASS' if z2_pass else 'FAIL'}; qualifying pairs={z2_count}/{len(z2_rows)}.\n"
        f"- Z3: {'PASS' if z3_pass else 'FAIL'}; distinct best={distinct}, dominance={dominance:.3f}, oracle gain={oracle_gain:.4f}.\n",
        encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
