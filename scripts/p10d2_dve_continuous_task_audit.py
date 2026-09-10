#!/usr/bin/env python3
"""Zero-training trajectory audit for the embodied DVE task."""

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
        positions = np.asarray([[rng.uniform(-0.4, 0.4), -y_span], [rng.uniform(-0.4, 0.4), y_span]])
        target = np.asarray([rng.uniform(4.0, 6.0), rng.uniform(-0.6, 0.6)])
        heading = rng.uniform(-np.pi, np.pi)
        speed = rng.uniform(*cfg["target_speed_range"])
        target_velocity = speed * np.asarray([np.cos(heading), np.sin(heading)])
        maneuver = rng.normal(0.0, cfg["target_maneuver_scale"], size=2)
        result = ContinuousInterceptAudit(
            InterceptCase(latency, positions, target, target_velocity, maneuver)
        ).evaluate()
        records.append(
            {
                "case_id": case_id,
                "latency": latency,
                "valid": result["stale_task_valid"],
                "joint_fork": result["individually_safe_jointly_unsafe"],
                "stale_value": result["both_stale"]["value"],
                "fallback_value": result["both_fallback"]["value"],
                "stale_safe": result["both_stale"]["safe"],
            }
        )

    valid_fraction = float(np.mean([r["valid"] for r in records]))
    joint_fraction = float(np.mean([r["joint_fork"] for r in records]))
    failure_fraction = float(np.mean([not r["stale_safe"] for r in records]))
    same_latency_pairs = fork_pairs = 0
    for left_index, left in enumerate(records):
        for right in records[left_index + 1 :]:
            if left["latency"] != right["latency"]:
                continue
            same_latency_pairs += 1
            fork_pairs += int(left["valid"] != right["valid"])
    fork_fraction = fork_pairs / same_latency_pairs

    accept_mean = float(np.mean([r["stale_value"] for r in records]))
    fallback_mean = float(np.mean([r["fallback_value"] for r in records]))
    oracle_mean = float(np.mean([max(r["stale_value"], r["fallback_value"]) for r in records]))
    oracle_gain = oracle_mean - max(accept_mean, fallback_mean)
    gates = cfg["gates"]
    checks = {
        "valid_stale_fraction_nontrivial": gates["valid_stale_fraction"][0] <= valid_fraction <= gates["valid_stale_fraction"][1],
        "same_latency_validity_forks_sufficient": fork_fraction >= gates["same_latency_validity_fork_pair_fraction_min"],
        "joint_compatibility_forks_sufficient": joint_fraction >= gates["individually_safe_jointly_unsafe_fraction_min"],
        "stale_execution_not_global_failure": failure_fraction <= gates["both_stale_global_failure_max"],
        "oracle_gain_over_best_constant_sufficient": oracle_gain >= gates["oracle_gain_over_best_constant_min"],
        "training_started": False,
    }
    scientific = {k: v for k, v in checks.items() if k != "training_started"}
    output = {
        "protocol": cfg["protocol"],
        "verdict": "P10D2_CONTINUOUS_TASK_PASS" if all(scientific.values()) else "P10D2_CONTINUOUS_TASK_STOP",
        "case_count": len(records),
        "valid_stale_fraction": valid_fraction,
        "joint_compatibility_fork_fraction": joint_fraction,
        "stale_safety_failure_fraction": failure_fraction,
        "same_latency_pair_count": same_latency_pairs,
        "same_latency_validity_fork_fraction": fork_fraction,
        "mean_values": {"always_accept": accept_mean, "always_fallback": fallback_mean, "oracle": oracle_mean},
        "oracle_gain_over_best_constant": oracle_gain,
        "checks": checks,
        "training_started": False,
        "environment_steps": 0,
        "ppo_updates": 0
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
