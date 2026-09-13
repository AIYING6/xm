from __future__ import annotations

import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.multi_threat_asset_defense_env import MultiThreatAssetDefenseConfig, MultiThreatAssetDefenseEnv


def main() -> None:
    cfg = MultiThreatAssetDefenseConfig(seed=913, branch_step=10, horizon=70)
    env = MultiThreatAssetDefenseEnv(cfg)
    obs, critic, graph = env.reset()
    assert obs.shape == (3, 19) and graph["action_masks"].shape == (3, 27)
    assert env.route_assignment is None
    for _ in range(cfg.branch_step):
        _, _, _, rewards, dones, info = env.step(np.full(3, 22, dtype=np.int64))
        assert rewards.shape == (3, 1)
        if bool(dones[0, 0]):
            raise AssertionError("ended before route commitment")
    assert env.route_assignment in {(-1, 1), (1, -1)}
    assert info["route_committed"] == 1.0 and info["primitive_action_interface"] == "3dof_27_discrete"
    print("MULTI_THREAT_ASSET_DEFENSE_G0_SMOKE_PASS")


if __name__ == "__main__":
    main()
