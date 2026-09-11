from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from envs.async_role_tracking_env import AsyncRoleTrackingConfig, AsyncRoleTrackingEnv


def main() -> None:
    env = AsyncRoleTrackingEnv(AsyncRoleTrackingConfig(seed=39))
    obs, share, graph = env.reset()
    assert obs.shape == (3, env.obs_dim)
    assert share.shape == (3, env.share_obs_dim)
    assert graph["node_feat"].shape == (5, 4)
    for step in range(40):
        actions = np.asarray([1, 2, 1 if step % 4 else 2], dtype=np.int64)
        obs, share, graph, rewards, dones, info = env.step(actions)
        assert np.all(np.isfinite(obs)) and np.all(np.isfinite(share))
        assert rewards.shape == (3, 1) and dones.shape == (3, 1)
        if np.all(dones):
            assert info["timeout"] == 1.0
            break
    else:
        raise AssertionError("P39 environment did not terminate")
    print("P39 async-role-tracking smoke PASS")


if __name__ == "__main__":
    main()
