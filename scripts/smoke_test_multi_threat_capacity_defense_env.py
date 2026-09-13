"""G0 interface and capacity invariants for multi-threat capacity defense."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.multi_threat_capacity_defense_env import MultiThreatCapacityDefenseConfig, MultiThreatCapacityDefenseEnv


def main() -> None:
    env = MultiThreatCapacityDefenseEnv(MultiThreatCapacityDefenseConfig(seed=73))
    obs, share, graph = env.reset()
    assert obs.shape[0] == env.num_agents and share.shape[0] == env.num_agents
    assert graph["action_masks"].shape == (env.num_agents, env.action_dim)
    for _ in range(12):
        obs, share, graph, reward, done, info = env.step(np.full(env.num_agents, 13, dtype=np.int64))
        assert reward.shape == (env.num_agents, 1) and done.shape == (env.num_agents, 1)
        assert info["kinetic_engagements_remaining"] == 1.0
        if done[0, 0]:
            break
    assert env.capacity_config.kinetic_engagement_capacity == 1
    assert env.capacity_config.suppressed_speed_scale == 1.0
    print("MULTI_THREAT_CAPACITY_DEFENSE_G0_SMOKE_PASS")


if __name__ == "__main__":
    main()
