"""Enumerate transparent policy templates for the M2 commitment-v2 task.

This is a task-identifiability audit.  It does not train a policy and does not
claim that any learning algorithm will recover the preferred decision rule.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.forecast_commitment_escort_env import (
    CENTER,
    COMMIT_CENTER,
    COMMIT_LEFT,
    COMMIT_RIGHT,
    M2_COMMITMENT_SCENARIOS,
    WAIT,
    ForecastCommitmentEscortV2Env,
)


def _cue_action(env: ForecastCommitmentEscortV2Env) -> int:
    return COMMIT_RIGHT if env._visible_right_probability() >= 0.5 else COMMIT_LEFT


def _policy_action(name: str, env: ForecastCommitmentEscortV2Env) -> int:
    if name == "early_right_commit":
        if env.step_count == env.reveal_step:
            return _cue_action(env)
        return COMMIT_RIGHT
    if name == "wait_for_reveal":
        return _cue_action(env) if env.step_count >= env.reveal_step else WAIT
    if name == "central_fallback":
        return COMMIT_CENTER
    raise ValueError(name)


def rollout(scenario_name: str, policy: str, *, repeats: int) -> float:
    scenario = next(item for item in M2_COMMITMENT_SCENARIOS if item.name == scenario_name)
    values = []
    for seed in range(repeats):
        env = ForecastCommitmentEscortV2Env(scenario, seed=10_000 + seed)
        env.reset()
        total = 0.0
        while not env.done:
            action = _policy_action(policy, env)
            _, _, _, reward, _, _ = env.step(np.full(env.num_agents, action, dtype=np.int64))
            total += float(reward.mean())
        values.append(total)
    return float(np.mean(values))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("refusing to run without --execute")
    if args.output.exists():
        raise FileExistsError(args.output)

    policies = ("early_right_commit", "wait_for_reveal", "central_fallback")
    rows = []
    for scenario in M2_COMMITMENT_SCENARIOS:
        for policy in policies:
            rows.append({"scenario": scenario.name, "policy": policy, "mean_return": rollout(scenario.name, policy, repeats=400)})

    table = {(row["scenario"], row["policy"]): row["mean_return"] for row in rows}
    checks = {
        "reliable_forecast_prefers_early_commit": table[("reliable_right_forecast", "early_right_commit")] > table[("reliable_right_forecast", "wait_for_reveal")],
        "ambiguous_forecast_prefers_waiting": table[("ambiguous_forecast", "wait_for_reveal")] > table[("ambiguous_forecast", "early_right_commit")],
        "both_regimes_beat_central_fallback": all(
            max(table[(scenario.name, "early_right_commit")], table[(scenario.name, "wait_for_reveal")]) > table[(scenario.name, "central_fallback")]
            for scenario in M2_COMMITMENT_SCENARIOS
        ),
    }
    output = {
        "protocol": "M2-FORECAST-COMMITMENT-V2-CHOICE-AUDIT-V1",
        "task_version": "v2_redeployment_cost",
        "verdict": "M2_V2_CHOICE_AUDIT_PASS" if all(checks.values()) else "M2_V2_CHOICE_AUDIT_FAIL",
        "rows": rows,
        "checks": checks,
        "interpretation": "The audit establishes only that explicit policy templates have different expected values across forecast regimes. It does not establish learnability or validate a proposed method.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
