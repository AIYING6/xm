"""G0 interface and information-boundary check for dual-asset defense."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.dual_asset_defense_env import DualAssetDefenseConfig, DualAssetDefenseEnv


def main() -> None:
    cfg = DualAssetDefenseConfig(seed=913, branch_step=12, horizon=75)
    env = DualAssetDefenseEnv(cfg)
    obs, critic, graph = env.reset()
    assert obs.shape[0] == 3
    assert graph["action_masks"].shape == (3, 27)
    assert env.exit_choice is None
    for _ in range(cfg.branch_step):
        _, _, _, rewards, dones, info = env.step(np.full(3, 22, dtype=np.int64))
        assert rewards.shape == (3, 1)
        if bool(dones[0, 0]):
            raise AssertionError("terminal event before public route commitment")
    assert info["attack_route_committed"] == 1.0
    assert int(info["attacked_asset"]) in {-1, 1}
    assert not (info["defense_success"] and info["asset_breach"])
    print("DUAL_ASSET_DEFENSE_G0_SMOKE_PASS")


if __name__ == "__main__":
    main()
