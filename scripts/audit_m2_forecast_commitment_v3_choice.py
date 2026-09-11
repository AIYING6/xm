"""Verify that M2 commitment-v3 retains a forecast-contingent decision gap."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.forecast_commitment_escort_env import (
    COMMIT_CENTER,
    COMMIT_LEFT,
    COMMIT_RIGHT,
    M2_COMMITMENT_SCENARIOS,
    WAIT,
    ForecastCommitmentEscortV3Env,
)


def policy_action(policy: str, env: ForecastCommitmentEscortV3Env) -> int:
    if policy == "early_right_commit":
        if env.step_count >= env.reveal_step:
            return COMMIT_RIGHT if env._visible_right_probability() >= 0.5 else COMMIT_LEFT
        return COMMIT_RIGHT
    if policy == "wait_for_reveal":
        return (COMMIT_RIGHT if env._visible_right_probability() >= 0.5 else COMMIT_LEFT) if env.step_count >= env.reveal_step else WAIT
    if policy == "central_fallback":
        return COMMIT_CENTER
    raise ValueError(policy)


def value(scenario, policy: str) -> float:
    returns = []
    for seed in range(400):
        env = ForecastCommitmentEscortV3Env(scenario, seed=20_000 + seed)
        env.reset()
        total = 0.0
        while not env.done:
            action = policy_action(policy, env)
            _, _, _, reward, _, _ = env.step(np.full(env.num_agents, action, dtype=np.int64))
            total += float(reward.mean())
        returns.append(total)
    return float(np.mean(returns))


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
    rows = [{"scenario": scenario.name, "policy": policy, "mean_return": value(scenario, policy)} for scenario in M2_COMMITMENT_SCENARIOS for policy in policies]
    table = {(row["scenario"], row["policy"]): row["mean_return"] for row in rows}
    checks = {
        "reliable_prefers_early": table[("reliable_right_forecast", "early_right_commit")] > table[("reliable_right_forecast", "wait_for_reveal")],
        "ambiguous_prefers_wait": table[("ambiguous_forecast", "wait_for_reveal")] > table[("ambiguous_forecast", "early_right_commit")],
        "central_is_not_optimal": all(max(table[(scenario.name, "early_right_commit")], table[(scenario.name, "wait_for_reveal")]) > table[(scenario.name, "central_fallback")] for scenario in M2_COMMITMENT_SCENARIOS),
    }
    payload = {
        "protocol": "M2-FORECAST-COMMITMENT-V3-CHOICE-AUDIT-V1",
        "task_version": "v3_single_window_forecast",
        "verdict": "M2_V3_CHOICE_AUDIT_PASS" if all(checks.values()) else "M2_V3_CHOICE_AUDIT_FAIL",
        "rows": rows,
        "checks": checks,
        "interpretation": "Template-policy ordering verifies a decision-relevant forecast window only; it neither proves learnability nor validates a proposed method.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
