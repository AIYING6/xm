#!/usr/bin/env python3
"""Zero-training audit of realistic delayed replanning for DVE."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from envs.dve_continuous_intercept import ContinuousInterceptAudit, InterceptCase


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    rng = np.random.default_rng(cfg["generator_seed"])
    records = []
    for case_id in range(cfg["case_count"]):
        latency = float(rng.choice(cfg["latency_support_seconds"]))
        y_span = rng.uniform(0.55, 1.5)
        positions = np.asarray(
            [[rng.uniform(-0.4, 0.4), -y_span], [rng.uniform(-0.4, 0.4), y_span]]
        )
        target = np.asarray([rng.uniform(4.0, 6.0), rng.uniform(-0.6, 0.6)])
        heading = rng.uniform(-np.pi, np.pi)
        speed = rng.uniform(*cfg["target_speed_range"])
        target_velocity = speed * np.asarray([np.cos(heading), np.sin(heading)])
        maneuver = rng.normal(0.0, cfg["target_maneuver_scale"], size=2)
        audit = ContinuousInterceptAudit(
            InterceptCase(latency, positions, target, target_velocity, maneuver)
        )
        old = audit.evaluate()
        accept = old["both_stale"]
        replan = audit.delayed_replan_rollout()
        records.append(
            {
                "case_id": case_id,
                "latency": latency,
                "accept_value": accept["value"],
                "replan_value": replan["value"],
                "accept_optimal": accept["value"] >= replan["value"],
                "joint_fork": old["individually_safe_jointly_unsafe"],
            }
        )

    accept_fraction = float(np.mean([r["accept_optimal"] for r in records]))
    joint_fraction = float(np.mean([r["joint_fork"] for r in records]))
    same_latency_pairs = fork_pairs = 0
    for left_index, left in enumerate(records):
        for right in records[left_index + 1 :]:
            if left["latency"] != right["latency"]:
                continue
            same_latency_pairs += 1
            fork_pairs += int(left["accept_optimal"] != right["accept_optimal"])
    fork_fraction = fork_pairs / same_latency_pairs

    accept_mean = float(np.mean([r["accept_value"] for r in records]))
    replan_mean = float(np.mean([r["replan_value"] for r in records]))
    oracle_mean = float(
        np.mean([max(r["accept_value"], r["replan_value"]) for r in records])
    )
    scale = max(float(np.mean([
        abs(max(r["accept_value"], r["replan_value"])) for r in records
    ])), 1e-8)
    accept_gap = (oracle_mean - accept_mean) / scale
    replan_gap = (oracle_mean - replan_mean) / scale
    gates = cfg["gates"]
    checks = {
        "oracle_uses_both_actions": gates["accept_optimal_fraction"][0]
        <= accept_fraction
        <= gates["accept_optimal_fraction"][1],
        "same_latency_validity_forks_sufficient": fork_fraction
        >= gates["same_latency_validity_fork_pair_fraction_min"],
        "joint_compatibility_forks_sufficient": joint_fraction
        >= gates["individually_safe_jointly_unsafe_fraction_min"],
        "always_accept_below_oracle": accept_gap
        >= gates["constant_policy_relative_gap_min"],
        "always_replan_below_oracle": replan_gap
        >= gates["constant_policy_relative_gap_min"],
        "future_information_used_by_accept": False,
        "zero_latency_replan_used_as_fair_baseline": False,
        "training_started": False,
    }
    scientific = {
        key: value
        for key, value in checks.items()
        if key not in {"training_started"}
    }
    output = {
        "protocol": cfg["protocol"],
        "verdict": "P10D2R_REALISTIC_FALLBACK_PASS"
        if all(scientific.values())
        else "P10D2R_REALISTIC_FALLBACK_STOP",
        "case_count": len(records),
        "accept_optimal_fraction": accept_fraction,
        "replan_optimal_fraction": 1.0 - accept_fraction,
        "joint_compatibility_fork_fraction": joint_fraction,
        "same_latency_pair_count": same_latency_pairs,
        "same_latency_validity_fork_fraction": fork_fraction,
        "mean_values": {
            "always_accept": accept_mean,
            "always_replan": replan_mean,
            "oracle": oracle_mean,
        },
        "relative_gaps": {
            "always_accept": accept_gap,
            "always_replan": replan_gap,
        },
        "checks": checks,
        "training_started": False,
        "environment_steps": 0,
        "ppo_updates": 0,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(output, handle, indent=2)
        handle.write("\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
