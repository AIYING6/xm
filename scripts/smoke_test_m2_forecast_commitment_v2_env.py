"""Smoke test for the commitment-sensitive M2 environment variant."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.forecast_commitment_escort_env import M2_COMMITMENT_SCENARIOS, ForecastCommitmentEscortV2Env, WAIT


def main() -> None:
    env = ForecastCommitmentEscortV2Env(M2_COMMITMENT_SCENARIOS[0], seed=19)
    obs, shared, graph = env.reset()
    assert obs.shape == (3, 8)
    assert shared.shape == (8,)
    assert graph["action_masks"].shape == (3, 4)
    for _ in range(env.horizon):
        obs, shared, graph, rewards, dones, _ = env.step(np.full(3, WAIT, dtype=np.int64))
    assert bool(dones[0, 0])
    print("M2_FORECAST_COMMITMENT_V2_ENV_SMOKE_PASS")


if __name__ == "__main__":
    main()
