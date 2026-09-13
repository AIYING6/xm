"""Smoke-test the commitment adapter without learning."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from envs.commitment_handoff_intercept_3d_env import CommitmentHandoffIntercept3DEnv
from envs.timed_handoff_intercept_3d_env import TimedHandoffIntercept3DConfig


def main() -> None:
    env = CommitmentHandoffIntercept3DEnv(TimedHandoffIntercept3DConfig(seed=1001))
    obs, share, graph = env.reset()
    assert env.action_dim == 2
    assert obs.shape == (3, 51)
    assert share.shape[-1] >= 3
    _, _, _, _, _, info = env.step(np.asarray((0, 1, 0), dtype=np.int64))
    assert info["commitment_relay_reconstructs_future"] == 1.0
    assert 0 <= int(info["commitment_relay_primitive_action"]) < 27
    try:
        env.step(np.asarray((0, 2, 0), dtype=np.int64))
    except ValueError:
        pass
    else:
        raise AssertionError("invalid commitment action was accepted")
    print("PASS: commitment adapter retains 3DOF plant and exposes only two legal relay commitments")


if __name__ == "__main__":
    main()
