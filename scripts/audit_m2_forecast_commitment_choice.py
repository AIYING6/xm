"""Verify that M2 forecast reliability changes the best legal commitment rule."""
from __future__ import annotations

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
    ForecastCommitmentEscortEnv,
)


def action_for(policy: str, env: ForecastCommitmentEscortEnv) -> np.ndarray:
    if policy == "early_right_commit":
        action = COMMIT_RIGHT
    elif policy == "wait_for_reveal":
        if env.step_count < env.reveal_step:
            action = COMMIT_CENTER
        else:
            action = COMMIT_RIGHT if env.actor_observation()[0, 0] >= 0.5 else COMMIT_LEFT
    elif policy == "central_fallback":
        action = COMMIT_CENTER
    else:
        raise ValueError(policy)
    return np.full(env.num_agents, action, dtype=np.int64)


def mean_return(scenario, policy: str, episodes: int = 400) -> float:
    values: list[float] = []
    for seed in range(episodes):
        env = ForecastCommitmentEscortEnv(scenario, seed=seed)
        env.reset()
        total = 0.0
        while not env.done:
            _, _, _, reward, _, _ = env.step(action_for(policy, env))
            total += float(reward[0, 0])
        values.append(total)
    return float(np.mean(values))


def main() -> None:
    policies = ("early_right_commit", "wait_for_reveal", "central_fallback")
    table = {
        scenario.name: {policy: mean_return(scenario, policy) for policy in policies}
        for scenario in M2_COMMITMENT_SCENARIOS
    }
    reliable = table["reliable_right_forecast"]
    ambiguous = table["ambiguous_forecast"]
    assert reliable["early_right_commit"] > reliable["wait_for_reveal"]
    assert ambiguous["wait_for_reveal"] > ambiguous["early_right_commit"]
    assert min(reliable["early_right_commit"], ambiguous["wait_for_reveal"]) > max(
        reliable["central_fallback"], ambiguous["central_fallback"]
    )
    result = {
        "protocol": "M2_FORECAST_COMMITMENT_CHOICE_AUDIT_V1",
        "episodes_per_policy": 400,
        "table": table,
        "checks": {
            "reliable_forecast_favors_early_commit": True,
            "ambiguous_forecast_favors_waiting": True,
            "both_best_rules_beat_central_fallback": True,
        },
        "interpretation": (
            "The task creates a decision-relevant reliability trade-off. This "
            "does not establish learnability or validate a learning method."
        ),
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
