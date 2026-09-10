#!/usr/bin/env python3
"""Build and audit the frozen stratified distribution for P10-C2."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from envs.dve_async_uav_env import DVEAsyncUAVEnv, DVECase


POLICIES = (
    "naive_accept",
    "always_fallback",
    "fixed_ttl",
    "current_state_safety_shield",
    "dve_oracle",
)


def build_cases(cfg: dict) -> list[tuple[str, DVECase]]:
    cases: list[tuple[str, DVECase]] = []
    latency_cycle = cfg["latency_cycle_ms"]
    global_index = 0
    for stratum, spec in cfg["strata"].items():
        drifts = np.linspace(spec["drift_range"][0], spec["drift_range"][1], spec["count"])
        for drift in drifts:
            latency = latency_cycle[global_index % len(latency_cycle)]
            cases.append(
                (
                    stratum,
                    DVECase(
                        float(latency),
                        float(drift),
                        bool(spec["task_relevant"]),
                        bool(spec["corridor_reserved"]),
                    ),
                )
            )
            global_index += 1
    return cases


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    cases = build_cases(cfg)

    rows = []
    for case_id, (stratum, case) in enumerate(cases):
        for policy in POLICIES:
            env = DVEAsyncUAVEnv(case)
            env.reset()
            actions = action_for(policy, env, cfg["fixed_ttl_ms"])
            _, _, _, rewards, _, infos = env.step(actions)
            rows.append(
                {
                    "case_id": case_id,
                    "stratum": stratum,
                    "policy": policy,
                    "value": float(rewards[0]),
                    "accepted": bool(actions.sum()),
                    "valid": env.stale_action_valid,
                    "stale_accept": bool(infos[0]["stale_accept"]),
                }
            )

    summary = {}
    for policy in POLICIES:
        selected = [row for row in rows if row["policy"] == policy]
        summary[policy] = {
            "mean_team_value": float(np.mean([row["value"] for row in selected])),
            "accept_rate": float(np.mean([row["accepted"] for row in selected])),
            "stale_accept_rate": float(np.mean([row["stale_accept"] for row in selected])),
        }

    unique_cases = [row for row in rows if row["policy"] == "dve_oracle"]
    valid_fraction = float(np.mean([row["valid"] for row in unique_cases]))
    same_latency_pairs = 0
    fork_pairs = 0
    for left_index, (_, left) in enumerate(cases):
        for _, right in cases[left_index + 1 :]:
            if left.latency_ms != right.latency_ms:
                continue
            same_latency_pairs += 1
            left_valid = left.state_drift <= 2.0 and left.task_relevant and not left.corridor_reserved
            right_valid = right.state_drift <= 2.0 and right.task_relevant and not right.corridor_reserved
            fork_pairs += int(left_valid != right_valid)
    fork_fraction = fork_pairs / same_latency_pairs

    oracle_value = summary["dve_oracle"]["mean_team_value"]
    relative_gaps = {
        policy: (oracle_value - values["mean_team_value"]) / oracle_value
        for policy, values in summary.items()
        if policy != "dve_oracle"
    }
    lower, upper = cfg["gates"]["valid_action_fraction"]
    minimum_gap = cfg["gates"]["minimum_oracle_relative_gap_for_constant_policies"]
    checks = {
        "case_count_exact": len(cases) == sum(v["count"] for v in cfg["strata"].values()),
        "cases_unique": len({(c.latency_ms, c.state_drift, c.task_relevant, c.corridor_reserved) for _, c in cases}) == len(cases),
        "valid_action_fraction_balanced": lower <= valid_fraction <= upper,
        "always_accept_gap_sufficient": relative_gaps["naive_accept"] >= minimum_gap,
        "always_fallback_gap_sufficient": relative_gaps["always_fallback"] >= minimum_gap,
        "validity_fork_fraction_sufficient": fork_fraction >= cfg["gates"]["minimum_validity_fork_pair_fraction"],
        "naive_async_mean_positive": summary["naive_accept"]["mean_team_value"] > 0.0,
        "dve_beats_fixed_ttl": oracle_value > summary["fixed_ttl"]["mean_team_value"],
        "dve_beats_safety_shield": oracle_value > summary["current_state_safety_shield"]["mean_team_value"],
        "dve_zero_stale_accept": summary["dve_oracle"]["stale_accept_rate"] == 0.0,
    }
    result = {
        "protocol": cfg["protocol"],
        "verdict": "P10C2_DISTRIBUTION_PASS" if all(checks.values()) else "P10C2_DISTRIBUTION_STOP",
        "case_count": len(cases),
        "stratum_counts": {name: spec["count"] for name, spec in cfg["strata"].items()},
        "valid_action_fraction": valid_fraction,
        "same_latency_pair_count": same_latency_pairs,
        "validity_fork_pair_count": fork_pairs,
        "validity_fork_pair_fraction": fork_fraction,
        "policy_summary": summary,
        "oracle_relative_gaps": relative_gaps,
        "checks": checks,
        "scope": "distribution identifiability only; no learned policy evaluated",
        "training_started": False,
        "environment_steps": 0,
        "ppo_updates": 0,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
