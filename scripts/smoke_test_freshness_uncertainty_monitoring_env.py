"""Smoke test for M1 monitoring environment before any learner is attached."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.freshness_uncertainty_monitoring_env import M1_SCENARIOS, FreshnessUncertaintyMonitoringEnv


def main() -> None:
    for scenario in M1_SCENARIOS:
        env = FreshnessUncertaintyMonitoringEnv(scenario, seed=11)
        obs, share, graph = env.reset()
        assert obs.shape == (3, 22)
        assert share.shape == (23,)
        assert graph["active_adj"].shape == (3, 3)
        assert graph["action_masks"].shape == (3, 5)
        # Actor observations include beliefs, age and urgency only; the hidden
        # field exists internally for evaluation but is not an observation.
        assert not np.shares_memory(obs, env._truth)
        assert np.all(np.isfinite(obs))

        initial_variance = env.posterior_variance.copy()
        # First move all agents; then sense a region from their locations.
        _, _, _, rewards, dones, info = env.step(np.asarray((1, 2, 3)))
        assert rewards.shape == (3, 1)
        assert dones.shape == (3, 1)
        assert info["truth_exposed_to_actor"] is False
        env.step(np.asarray((1, 2, 3)))
        assert np.any(env.posterior_variance < initial_variance)
        assert np.all(env.age >= 0.0)

        while not env.done:
            env.step(np.asarray((1, 2, 3)))
        summary = env.terminal_summary()
        assert summary["scenario"] == scenario.name
        assert np.isfinite(summary["evaluation_mse"])
    print("M1_FRESHNESS_UNCERTAINTY_ENV_SMOKE_PASS")


if __name__ == "__main__":
    main()
