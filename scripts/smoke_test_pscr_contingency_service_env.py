"""Smoke test for the uncertainty-aware contingency staging interface."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.pscr_adversarial_service_env import PSCRConfig
from envs.pscr_contingency_service_env import CONTINGENCY_STAGE, PSCRContingencyServiceEnv
from envs.pscr_service_reconfiguration_env import FUTURE_SERVICE


def main() -> None:
    env = PSCRContingencyServiceEnv(PSCRConfig(seed=511))
    obs, critic, graph = env.reset()
    assert obs.shape == (3, 27) and critic.shape == (47,)
    assert graph["action_masks"].shape == (3, 5)
    assert graph["action_masks"][:, CONTINGENCY_STAGE].all()
    assert not graph["action_masks"][:, FUTURE_SERVICE].any()
    _, _, _, _, _, info = env.step(np.full(3, CONTINGENCY_STAGE, dtype=np.int64))
    assert info["macro_interface"] == "public_contingency_service_intent_v2"
    print("PSCR_CONTINGENCY_SERVICE_ENV_SMOKE_PASS")


if __name__ == "__main__":
    main()
