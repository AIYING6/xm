"""Smoke test for A0's dynamic active-perception environment."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.active_perception_tracking_env import ActivePerceptionTrackingEnv, HOLD


def main() -> None:
    env = ActivePerceptionTrackingEnv(seed=41)
    obs, critic, graph = env.reset()
    assert obs.shape == (3, 10)
    assert critic.shape == (13,)
    assert graph["action_masks"].shape == (3, 5)
    assert not np.shares_memory(obs, env._target_truth)
    initial = float(np.linalg.det(env.belief_covariance))
    for _ in range(env.horizon):
        obs, critic, graph, rewards, dones, info = env.step(np.asarray((HOLD, HOLD, HOLD)))
        assert rewards.shape == (3, 1)
        assert info["target_truth_exposed_to_actor"] is False
    assert bool(dones[0, 0])
    assert np.isfinite(env.terminal_summary()["mean_evaluation_estimation_error"])
    assert np.isfinite(initial)
    print("A0_ACTIVE_PERCEPTION_TRACKING_ENV_SMOKE_PASS")


if __name__ == "__main__":
    main()
