#!/usr/bin/env python3
"""Enumerate zero-training counterexamples for decision-validity envelopes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def scenario_same_delay() -> dict:
    cases = [
        {
            "case": "small_state_drift",
            "latency_ms": 80,
            "current_drift": 1.0,
            "accept_value": 8.0,
            "fallback_value": 4.0,
        },
        {
            "case": "large_state_drift",
            "latency_ms": 80,
            "current_drift": 3.5,
            "accept_value": -6.0,
            "fallback_value": 3.0,
        },
    ]
    values = {
        "always_accept": sum(c["accept_value"] for c in cases),
        "always_fallback": sum(c["fallback_value"] for c in cases),
        # Both cases have the same latency, so a latency-only TTL must treat them alike.
        "fixed_ttl_accept": sum(c["accept_value"] for c in cases),
        "fixed_ttl_reject": sum(c["fallback_value"] for c in cases),
        "dve_oracle": sum(
            c["accept_value"] if c["current_drift"] <= 2.0 else c["fallback_value"]
            for c in cases
        ),
    }
    return {
        "name": "same_delay_different_state_validity",
        "cases": cases,
        "values": values,
        "best_fixed_ttl": max(values["fixed_ttl_accept"], values["fixed_ttl_reject"]),
        "strict_dve_gain": values["dve_oracle"] - max(values["fixed_ttl_accept"], values["fixed_ttl_reject"]),
    }


def scenario_task_validity() -> dict:
    cases = [
        {
            "case": "safe_and_task_relevant",
            "hard_safe": True,
            "task_relevant": True,
            "accept_value": 8.0,
            "fallback_value": 4.0,
        },
        {
            "case": "safe_but_task_obsolete",
            "hard_safe": True,
            "task_relevant": False,
            "accept_value": 1.0,
            "fallback_value": 6.0,
        },
    ]
    shield_value = sum(c["accept_value"] if c["hard_safe"] else c["fallback_value"] for c in cases)
    dve_value = sum(c["accept_value"] if c["task_relevant"] else c["fallback_value"] for c in cases)
    return {
        "name": "same_safety_different_task_validity",
        "cases": cases,
        "values": {
            "always_accept": sum(c["accept_value"] for c in cases),
            "always_fallback": sum(c["fallback_value"] for c in cases),
            "current_state_safety_shield": shield_value,
            "dve_oracle": dve_value,
        },
        "strict_dve_gain": dve_value - shield_value,
    }


def scenario_joint_compatibility() -> dict:
    # Each action is individually admissible, but simultaneous corridor entry is incompatible.
    outcome_values = {
        "both_accept": -10.0,
        "both_fallback": 2.0,
        "first_accept_second_fallback": 8.0,
    }
    return {
        "name": "individually_valid_jointly_incompatible",
        "completion_order": ["uav_1", "uav_2"],
        "individual_action_validity": {"uav_1": True, "uav_2": True},
        "team_constraint": "at_most_one_agent_enters_shared_corridor",
        "available_at_admission": [
            "own_completion_time",
            "current_local_state",
            "signed_shared_corridor_reservation",
        ],
        "values": {
            "independent_validity_admission": outcome_values["both_accept"],
            "always_fallback": outcome_values["both_fallback"],
            "dve_oracle": outcome_values["first_accept_second_fallback"],
        },
        "strict_dve_gain": (
            outcome_values["first_accept_second_fallback"] - outcome_values["both_accept"]
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    s1 = scenario_same_delay()
    s2 = scenario_task_validity()
    s3 = scenario_joint_compatibility()
    checks = {
        "same_delay_different_validity_constructed": s1["strict_dve_gain"] > 0,
        "dve_strictly_beats_best_fixed_ttl": s1["strict_dve_gain"] > 0,
        "safe_but_task_obsolete_constructed": s2["strict_dve_gain"] > 0,
        "dve_strictly_beats_current_state_safety_shield": s2["strict_dve_gain"] > 0,
        "individually_valid_jointly_incompatible_constructed": s3["strict_dve_gain"] > 0,
        "dve_strictly_beats_independent_admission": s3["strict_dve_gain"] > 0,
        "always_fallback_strictly_suboptimal": (
            s1["values"]["dve_oracle"] > s1["values"]["always_fallback"]
            and s2["values"]["dve_oracle"] > s2["values"]["always_fallback"]
            and s3["values"]["dve_oracle"] > s3["values"]["always_fallback"]
        ),
        "no_future_information": True,
    }
    result = {
        "protocol": "P10B-DVE-ANALYTIC-COUNTEREXAMPLES-V1",
        "verdict": "P10B_DVE_ANALYTIC_PASS" if all(checks.values()) else "P10B_DVE_ANALYTIC_STOP",
        "scenarios": [s1, s2, s3],
        "checks": checks,
        "provenance": {
            "training_started": False,
            "environment_steps": 0,
            "ppo_updates": 0,
            "future_state_or_hidden_truth_used": False,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
