"""Smoke test for P41 v2 before any learner can be attached."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.recoverable_service_chain_v2_env import P41_V2_SCENARIOS, RecoverableServiceChainV2Env


def main() -> None:
    for scenario in P41_V2_SCENARIOS:
        env = RecoverableServiceChainV2Env(scenario)
        obs, share, graph = env.reset()
        assert obs.shape == (3, 12)
        assert share.shape == (6,)
        assert graph["active_adj"].shape == (3, 3)
        # The public forecast is present, but future realization is absent.
        assert obs[0, 3] == 0.0
        assert np.isclose(obs[0, 6], scenario.forecast.probability)
        for _ in range(env.horizon):
            _, _, _, rewards, dones, _ = env.step(np.asarray((1, 1, 0)))
            assert rewards.shape == (3, 1)
            if bool(dones[0, 0]):
                break
    print("P41_V2_ENV_SMOKE_PASS")


if __name__ == "__main__":
    main()
