from __future__ import annotations

import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.multi_threat_dual_capability_defense_env import MultiThreatDualCapabilityDefenseConfig, MultiThreatDualCapabilityDefenseEnv


def main() -> None:
    env = MultiThreatDualCapabilityDefenseEnv(MultiThreatDualCapabilityDefenseConfig(seed=913, branch_step=10, horizon=70))
    obs, critic, graph = env.reset()
    assert obs.shape == (3, 19) and graph["action_masks"].shape == (3, 27)
    for _ in range(10):
        _, _, _, rewards, dones, info = env.step(np.full(3, 22, dtype=np.int64))
        assert rewards.shape == (3, 1)
        if bool(dones[0, 0]):
            raise AssertionError("ended before route commitment")
    assert info["route_committed"] == 1.0
    assert info["suppressed_threats"] <= 1.0
    print("MULTI_THREAT_DUAL_CAPABILITY_G0_SMOKE_PASS")


if __name__ == "__main__":
    main()
