"""Smoke test for the P41 non-learning task environment."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.recoverable_service_chain_env import P41_SCENARIOS, RecoverableServiceChainEnv


def main() -> None:
    for scenario in P41_SCENARIOS:
        env = RecoverableServiceChainEnv(scenario)
        obs, share, graph = env.reset()
        assert obs.shape == (3, 11)
        assert share.ndim == 1
        assert graph["active_adj"].shape == (3, 3)
        assert obs[0, 3:6].sum() == 0.0, "future site must not enter scout observation at reset"
        done = False
        for _ in range(env.deadline_steps):
            obs, share, graph, rewards, dones, info = env.step(np.asarray((1, 1, 0)))
            assert rewards.shape == (3, 1) and dones.shape == (3, 1)
            done = bool(dones[0, 0])
            if done:
                break
        assert done
        assert "completed_value" in info
    print("P41_ENV_SMOKE_PASS")


if __name__ == "__main__":
    main()
