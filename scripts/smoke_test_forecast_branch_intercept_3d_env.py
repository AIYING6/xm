"""Smoke test for the forecast-branch 3DOF information contract."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from envs.forecast_branch_intercept_3d_env import ForecastBranchIntercept3DConfig, ForecastBranchIntercept3DEnv


def main() -> None:
    cfg = ForecastBranchIntercept3DConfig(seed=731, forecast_right_probability=0.5, branch_step=3, max_steps=20)
    env = ForecastBranchIntercept3DEnv(cfg)
    obs, share, graph = env.reset()
    assert obs.shape == (3, 36)
    assert share.shape == (3, 49)
    assert graph["node_feat"].shape[0] == 4
    assert np.allclose(obs[:, -2], 0.5)
    assert np.all(obs[:, -1] == 0.0)
    # Switching the otherwise hidden future branch in the same physical state
    # must not alter the actor observation before physical branching.
    env.branch_right = False
    left_obs = env._get_obs().copy()
    env.branch_right = True
    right_obs = env._get_obs().copy()
    assert np.allclose(left_obs, right_obs)
    initial_y = float(env.red_pos[0, 1])
    for _ in range(3):
        env.step(np.full(3, 13, dtype=np.int64))
    assert float(env.red_pos[0, 1]) < initial_y
    print("FORECAST_BRANCH_INTERCEPT_3D_G0_SMOKE_PASS")


if __name__ == "__main__":
    import math
    main()
