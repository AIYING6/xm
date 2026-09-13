"""G0 smoke test for PSCR-v3 delayed-choice dual-exit task."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.pscr_v3_dual_exit_interception_env import PSCRV3Config, PSCRV3DualExitInterceptionEnv


def main() -> None:
    cfg = PSCRV3Config(seed=913, branch_step=12, horizon=70)
    env = PSCRV3DualExitInterceptionEnv(cfg)
    obs, critic, graph = env.reset()
    assert obs.shape[0] == 3 and obs.shape[1] == env.base._get_obs().shape[1]
    assert critic.shape == env.base._get_share_obs().shape
    assert graph["action_masks"].shape == (3, 27)
    assert env.exit_choice is None, "future exit must not exist at reset"
    for _ in range(cfg.branch_step):
        obs, critic, graph, rewards, dones, info = env.step(np.full(3, 22, dtype=np.int64))
        assert rewards.shape == (3, 1)
        if bool(dones[0, 0]):
            raise AssertionError("episode terminated before the delayed exit decision")
    assert env.exit_choice in {-1, 1}
    assert info["branch_committed"] == 1.0
    assert info["primitive_action_interface"] == "3dof_27_discrete"
    print("PSCR_V3_DUAL_EXIT_G0_SMOKE_PASS")


if __name__ == "__main__":
    main()
