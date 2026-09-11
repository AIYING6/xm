"""Smoke test for the single-window forecast task."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.forecast_commitment_escort_env import M2_COMMITMENT_SCENARIOS, WAIT, ForecastCommitmentEscortV3Env


def main() -> None:
    env = ForecastCommitmentEscortV3Env(M2_COMMITMENT_SCENARIOS[0], seed=23)
    initial, _, _ = env.reset()
    assert np.isclose(initial[0, 0], 0.9)
    env.step(np.full(3, WAIT, dtype=np.int64))
    later = env.actor_observation()
    assert np.isclose(later[0, 0], 0.5)
    print("M2_FORECAST_COMMITMENT_V3_ENV_SMOKE_PASS")


if __name__ == "__main__":
    main()
