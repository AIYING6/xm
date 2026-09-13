"""Smoke-test the staged-handoff environment interface and information boundary."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from envs.timed_handoff_intercept_3d_env import HANDOFF_CONTEXTS, TimedHandoffIntercept3DConfig, TimedHandoffIntercept3DEnv


def main() -> None:
    for context in HANDOFF_CONTEXTS:
        env = TimedHandoffIntercept3DEnv(TimedHandoffIntercept3DConfig(seed=91, handoff_context=context))
        obs, share, graph = env.reset()
        assert obs.shape == (3, 36), obs.shape
        assert share.shape[0] == 3 and share.shape[1] == env.share_obs_dim + 2, share.shape
        assert graph["node_feat"].shape[0] == 4
        expected = (1.0, 0.0) if context == "current_authorization" else (0.0, 1.0)
        assert tuple(obs[0, -2:]) == expected and np.all(obs[:, -2:] == obs[0, -2:])
        # The branch direction is not appended to any actor observation.
        assert obs.shape[-1] == 36
        _, _, _, _, dones, info = env.step(np.full(3, 13, dtype=np.int64))
        assert dones.shape == (3, 1)
        assert "handoff_success" in info and "authorization_handoff_observed" in info
    print("PASS: timed-handoff environment preserves primitive actions and exposes only public service context")


if __name__ == "__main__":
    main()
