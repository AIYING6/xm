"""Smoke test for the M2 forecast-contingent escort substrate."""
from __future__ import annotations

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


def main() -> None:
    for scenario in M2_COMMITMENT_SCENARIOS:
        env = ForecastCommitmentEscortEnv(scenario, seed=11)
        obs, share, graph = env.reset()
        assert obs.shape == (3, 8)
        assert share.shape == (8,)
        assert graph["active_adj"].shape == (3, 3)
        assert np.isclose(obs[0, 0], scenario.early_right_probability)
        # A branch is hidden before the fork, even to the critic.
        assert env.step_count < env.fork_step
        assert np.isclose(env.critic_observation()[0], scenario.early_right_probability)
        env.step(np.asarray((COMMIT_LEFT, COMMIT_CENTER, COMMIT_RIGHT)))
        assert np.array_equal(
            env._lag_remaining,
            np.asarray((env.reconfiguration_lag, 0, env.reconfiguration_lag)),
        )
        env.step(np.asarray((COMMIT_CENTER, COMMIT_CENTER, COMMIT_CENTER)))
        env.step(np.asarray((COMMIT_CENTER, COMMIT_CENTER, COMMIT_CENTER)))
        assert np.all(env._lag_remaining == 0)
        while not env.done:
            env.step(np.asarray((COMMIT_CENTER, COMMIT_CENTER, COMMIT_CENTER)))
        summary = env.terminal_summary()
        assert summary["scenario"] == scenario.name
        assert summary["branch_support_steps"] >= 0
    print("M2_FORECAST_COMMITMENT_ESCORT_ENV_SMOKE_PASS")


if __name__ == "__main__":
    main()
