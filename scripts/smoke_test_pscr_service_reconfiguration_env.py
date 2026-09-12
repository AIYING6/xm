"""Smoke test for PSCR's public high-level service-intent interface."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.pscr_adversarial_service_env import PSCRConfig
from envs.pscr_service_reconfiguration_env import FUTURE_SERVICE, PSCRServiceReconfigurationEnv


def main() -> None:
    env = PSCRServiceReconfigurationEnv(PSCRConfig(seed=401))
    obs, critic, graph = env.reset()
    assert obs.shape == (3, 27) and critic.shape == (47,)
    assert graph["action_masks"].shape == (3, 4)
    assert not graph["action_masks"][:, FUTURE_SERVICE].any()
    # The future-service action is unavailable until the request becomes public.
    for _ in range(env.config.future_arrival_step):
        obs, critic, graph, rewards, dones, info = env.step(np.asarray((0, 1, FUTURE_SERVICE), dtype=np.int64))
        assert rewards.shape == (3, 1)
        if bool(dones[0, 0]):
            raise AssertionError("terminated before the scheduled public request")
    assert graph["action_masks"][:, FUTURE_SERVICE].all()
    assert info["macro_interface"] == "public_role_conditioned_service_intent_v1"
    print("PSCR_SERVICE_RECONFIGURATION_ENV_SMOKE_PASS")


if __name__ == "__main__":
    main()
