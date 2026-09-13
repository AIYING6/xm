"""G0 invariants for the potential-shaped capacity-defense learning task."""
from __future__ import annotations

import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.multi_threat_capacity_shaped_defense_env import MultiThreatCapacityShapedDefenseEnv


def main() -> None:
    env=MultiThreatCapacityShapedDefenseEnv();obs,share,graph=env.reset()
    assert obs.shape[0]==env.num_agents and share.shape[0]==env.num_agents
    for _ in range(20):
        _,_,_,reward,done,info=env.step(np.full(env.num_agents,13,dtype=np.int64))
        assert reward.shape==(env.num_agents,1)
        assert "risk_potential" in info and "potential_shaping_reward" in info
        if done[0,0]:break
    assert env.action_dim==27 and env.capacity_config.kinetic_engagement_capacity==1
    print("MULTI_THREAT_CAPACITY_SHAPED_DEFENSE_G0_SMOKE_PASS")


if __name__=="__main__":main()
