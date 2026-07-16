from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from baselines import greedy_intercept_policy
from envs import UAVPursuitConfig, UAVPursuitEnv


def run(seed: int) -> dict:
    env = UAVPursuitEnv(UAVPursuitConfig(seed=seed, target_policy="mixed"))
    obs, share_obs, graph_obs = env.reset()
    assert obs.shape == (env.config.num_pursuers, env.obs_dim), obs.shape
    assert share_obs.shape[0] == env.config.num_pursuers, share_obs.shape
    assert graph_obs["node_feat"].shape[0] == env.config.num_pursuers + env.config.num_targets
    assert graph_obs["adj"].shape[0] == graph_obs["adj"].shape[1]

    done = False
    info = {}
    while not done:
        actions = greedy_intercept_policy(env)
        obs, share_obs, graph_obs, rewards, dones, info = env.step(actions)
        assert rewards.shape == (env.config.num_pursuers, 1), rewards.shape
        assert dones.shape == (env.config.num_pursuers, 1), dones.shape
        assert np.all(np.isfinite(obs))
        assert np.all(np.isfinite(share_obs))
        assert np.all(np.isfinite(graph_obs["node_feat"]))
        done = bool(np.all(dones))
    return info


def main():
    for seed in range(5):
        info = run(seed)
        print(seed, info)


if __name__ == "__main__":
    main()
