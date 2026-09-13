from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from envs.multi_threat_communicative_capacity_defense_env import MultiThreatCommunicativeCapacityDefenseEnv
def main():
    env=MultiThreatCommunicativeCapacityDefenseEnv();obs,share,graph=env.reset();assert obs.shape==(3,29);assert graph["active_adj"].shape==(3,3)
    for _ in range(12):
        obs,_,_,_,done,info=env.step(np.full(3,13));assert "track_messages_valid" in info
        if done[0,0]:break
    print("MULTI_THREAT_COMMUNICATIVE_CAPACITY_G0_SMOKE_PASS")
if __name__=="__main__":main()
