from __future__ import annotations

import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.multi_threat_target_lock_defense_env import MultiThreatTargetLockDefenseConfig, MultiThreatTargetLockDefenseEnv


def main() -> None:
    env=MultiThreatTargetLockDefenseEnv(MultiThreatTargetLockDefenseConfig(seed=913, branch_step=10, horizon=70))
    obs, _, graph=env.reset()
    assert obs.shape==(3,19) and graph["action_masks"].shape==(3,27)
    for _ in range(10):
        _,_,_,reward,done,info=env.step(np.full(3,22,dtype=np.int64))
        assert reward.shape==(3,1)
        if bool(done[0,0]): raise AssertionError("ended before route commitment")
    assert info["route_committed"]==1.0
    assert np.all(env.red_target_lock_hold >= 0)
    print("MULTI_THREAT_TARGET_LOCK_DEFENSE_G0_SMOKE_PASS")
if __name__=="__main__": main()
