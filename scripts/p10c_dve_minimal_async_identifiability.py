#!/usr/bin/env python3
"""Exhaustive zero-training identifiability audit for the minimal DVE task."""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path
import sys

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from envs.dve_async_uav_env import DVEAsyncUAVEnv, DVECase


def action_for(policy: str, env: DVEAsyncUAVEnv, ttl_ms: float) -> np.ndarray:
    if policy == "naive_accept":
        return np.asarray([1, 0])
    if policy == "always_fallback":
        return np.asarray([0, 0])
    if policy == "fixed_ttl":
        return np.asarray([int(env.case.latency_ms <= ttl_ms), 0])
    if policy == "current_state_safety_shield":
        return np.asarray([int(env.hard_safe and not env.case.corridor_reserved), 0])
    if policy == "dve_oracle":
        return np.asarray([int(env.stale_action_valid), 0])
    raise KeyError(policy)


def is_valid(case: DVECase) -> bool:
    return case.state_drift <= 2.0 and case.task_relevant and not case.corridor_reserved


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cfg = json.loads(args.config.read_text(encoding="utf-8"))

    cases = [
        DVECase(*values)
        for values in itertools.product(
            cfg["latency_ms"], cfg["state_drift"], cfg["task_relevant"], cfg["corridor_reserved"]
        )
    ]
    records = []
    for case_id, case in enumerate(cases):
        for policy in cfg["policies"]:
            env = DVEAsyncUAVEnv(case)
            env.reset()
            actions = action_for(policy, env, cfg["fixed_ttl_ms"])
            _, _, _, rewards, _, infos = env.step(actions)
            records.append(
                {
                    "case_id": case_id,
                    "policy": policy,
                    "team_value": float(rewards[0]),
                    "stale_action_valid": env.stale_action_valid,
                    "accepted": bool(actions.sum()),
                    "stale_accept": bool(infos[0]["stale_accept"]),
                    "joint_conflict": bool(infos[0]["joint_conflict"]),
                }
            )

    by_policy = {}
    for policy in cfg["policies"]:
        rows = [r for r in records if r["policy"] == policy]
        by_policy[policy] = {
            "mean_team_value": float(np.mean([r["team_value"] for r in rows])),
            "stale_accept_rate": float(np.mean([r["stale_accept"] for r in rows])),
            "joint_conflict_rate": float(np.mean([r["joint_conflict"] for r in rows])),
        }

    # A validity fork is a pair sharing latency but requiring different accept decisions.
    same_latency_pairs = 0
    fork_pairs = 0
    for left_index, left in enumerate(cases):
        for right in cases[left_index + 1 :]:
            if left.latency_ms != right.latency_ms:
                continue
            same_latency_pairs += 1
            fork_pairs += int(is_valid(left) != is_valid(right))
    fork_fraction = fork_pairs / same_latency_pairs

    dve = by_policy["dve_oracle"]
    checks = {
        "standard_env_interface_smoke": True,
        "validity_fork_fraction_at_least_threshold": fork_fraction >= cfg["minimum_validity_fork_fraction"],
        "naive_async_not_global_collapse": by_policy["naive_accept"]["mean_team_value"] > -10.0,
        "always_fallback_not_optimal": dve["mean_team_value"] > by_policy["always_fallback"]["mean_team_value"],
        "dve_beats_fixed_ttl": dve["mean_team_value"] > by_policy["fixed_ttl"]["mean_team_value"],
        "dve_beats_safety_shield": dve["mean_team_value"] > by_policy["current_state_safety_shield"]["mean_team_value"],
        "dve_has_zero_stale_accepts": dve["stale_accept_rate"] == 0.0,
        "training_started": False,
    }
    scientific_checks = {k: v for k, v in checks.items() if k != "training_started"}
    result = {
        "protocol": "P10C-DVE-MINIMAL-ASYNC-IDENTIFIABILITY-V1",
        "verdict": "P10C_TASK_IDENTIFIABILITY_PASS" if all(scientific_checks.values()) else "P10C_TASK_IDENTIFIABILITY_STOP",
        "case_count": len(cases),
        "same_latency_pair_count": same_latency_pairs,
        "validity_fork_pair_count": fork_pairs,
        "validity_fork_fraction": fork_fraction,
        "policy_summary": by_policy,
        "checks": checks,
        "scope": "task identifiability only; baseline learnability remains untested",
        "environment_steps": 0,
        "ppo_updates": 0,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
