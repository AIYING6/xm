"""Zero-training qualification audit for P39's opt-in monitoring environment."""

from __future__ import annotations

import argparse
import copy
import csv
import itertools
import json
import sys
from pathlib import Path
from typing import Callable

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from envs.async_role_tracking_env import AsyncRoleTrackingConfig, AsyncRoleTrackingEnv


JOINT_ACTIONS = tuple(np.asarray(values, dtype=np.int64) for values in itertools.product(range(3), repeat=3))


def coverage_after(env: AsyncRoleTrackingEnv, actions: np.ndarray) -> tuple[float, int]:
    trial = copy.deepcopy(env)
    _, _, _, _, _, info = trial.step(actions)
    return float(info["coverage"]), int(np.sum(actions != env.assignments))


def oracle_action(env: AsyncRoleTrackingEnv) -> tuple[np.ndarray, float, int]:
    scored = [(coverage_after(env, action), action) for action in JOINT_ACTIONS]
    best = max(value for (value, _), _action in scored)
    winners = [action for (value, _), action in scored if np.isclose(value, best)]
    action = min(winners, key=lambda item: tuple(int(x) for x in item))
    _, switches = coverage_after(env, action)
    return action, best, switches


def static_split(_env: AsyncRoleTrackingEnv) -> np.ndarray:
    return np.asarray([1, 2, 0], dtype=np.int64)


def greedy_nearest(env: AsyncRoleTrackingEnv) -> np.ndarray:
    action = np.zeros(3, dtype=np.int64)
    for agent in range(3):
        distance = np.linalg.norm(env.event_pos - env.uav_pos[agent], axis=1)
        action[agent] = int(np.argmin(distance)) + 1
    return action


def evaluate(seed: int, policy: Callable[[AsyncRoleTrackingEnv], np.ndarray], blackout: int) -> dict[str, float]:
    env = AsyncRoleTrackingEnv(AsyncRoleTrackingConfig(seed=seed, reassignment_blackout_steps=blackout))
    env.reset()
    coverages: list[float] = []
    switched = 0
    for _ in range(env.config.max_steps):
        action = policy(env)
        switched += int(np.sum(action != env.assignments))
        _, _, _, _, dones, info = env.step(action)
        coverages.append(float(info["coverage"]))
        if np.all(dones):
            break
    return {"coverage": float(np.mean(coverages)), "switch_rate": switched / (len(coverages) * env.num_agents)}


def matched_geometry_counterfactual() -> bool:
    env = AsyncRoleTrackingEnv(AsyncRoleTrackingConfig(seed=39011))
    env.reset()
    fresh = copy.deepcopy(env)
    stale = copy.deepcopy(env)
    fresh.cache_age[:, 0] = 0
    fresh.cache_age[:, 1] = fresh.config.max_steps
    stale.cache_age[:, :] = stale.config.max_steps
    fresh_action, _, _ = oracle_action(fresh)
    stale_action, _, _ = oracle_action(stale)
    same_geometry = np.array_equal(fresh.uav_pos, stale.uav_pos) and np.array_equal(fresh.event_pos, stale.event_pos)
    return bool(same_geometry and not np.array_equal(fresh_action, stale_action))


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
    if contract.get("protocol") != "P39-ASYNC-ROLE-TRACKING-STAGE0-V2":
        raise ValueError("protocol mismatch")
    rows: list[dict[str, float | int | str]] = []
    for seed in contract["seeds"]:
        for name, policy in (("static_split", static_split), ("greedy_nearest", greedy_nearest), ("one_step_oracle", lambda env: oracle_action(env)[0])):
            metrics = evaluate(int(seed), policy, blackout=1)
            rows.append({"seed": int(seed), "policy": name, **metrics})
        rows.append({"seed": int(seed), "policy": "oracle_no_blackout", **evaluate(int(seed), lambda env: oracle_action(env)[0], blackout=0)})
    means = {name: float(np.mean([float(row["coverage"]) for row in rows if row["policy"] == name])) for name in {str(row["policy"]) for row in rows}}
    oracle_switch = float(np.mean([float(row["switch_rate"]) for row in rows if row["policy"] == "one_step_oracle"]))
    non_oracle = max(means["static_split"], means["greedy_nearest"])
    no_blackout_gap = means["oracle_no_blackout"] - means["one_step_oracle"]
    env = AsyncRoleTrackingEnv(AsyncRoleTrackingConfig(seed=39011))
    env.reset()
    env.cache_age[:, :] = 0
    fresh_coverage = float(np.mean(env._coverage()))
    env.cache_age[:, :] = env.config.max_steps
    stale_coverage = float(np.mean(env._coverage()))
    checks = {
        "E1_non_saturated_baseline": 0.10 < means["static_split"] < 0.90,
        "E2_age_changes_oracle_choice": matched_geometry_counterfactual(),
        "E3_switching_has_cost_and_value": 0.05 <= oracle_switch <= 0.80 and no_blackout_gap >= 0.02,
        "E4_native_actor_visible_staleness": fresh_coverage != stale_coverage,
        "E5_distinguishable_reference_ladder": means["one_step_oracle"] - non_oracle >= 0.03 and non_oracle > 0.10,
    }
    result = {
        "protocol": contract["protocol"],
        "verdict": "P39_STAGE0_PASS" if all(checks.values()) else "P39_STAGE0_STOP",
        "mean_coverage": means,
        "oracle_switch_rate": oracle_switch,
        "oracle_blackout_gap": no_blackout_gap,
        "matched_geometry_age_changes_oracle_choice": checks["E2_age_changes_oracle_choice"],
        "fresh_coverage": fresh_coverage,
        "expired_cache_coverage": stale_coverage,
        "checks": checks,
        "training_started": False,
        "environment_steps": len(rows) * int(contract["environment"]["max_steps"]),
        "ppo_updates": 0,
        "interpretation": "Rule/oracle qualification only. It neither trains nor evaluates a learned policy.",
    }
    args.output.mkdir(parents=True)
    with (args.output / "P39_STAGE0_POLICY_LEDGER.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    (args.output / "P39_STAGE0_RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
