"""Interface and information-boundary smoke test for PSCR-v2."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.pscr_adversarial_service_env import PSCRConfig, PredictiveServiceChainReconfigurationEnv


def main() -> None:
    env = PredictiveServiceChainReconfigurationEnv(PSCRConfig(seed=37))
    obs, share, graph = env.reset()
    assert obs.shape == (3, 27) and share.shape == (47,)
    assert graph["active_adj"].shape == (3, 3)
    # Exact future geometry remains absent until the request arrives.
    future_rel_slice = slice(-3, None)
    assert np.allclose(obs[:, future_rel_slice], 0.0)
    for _ in range(env.config.future_arrival_step):
        obs, share, graph, reward, dones, info = env.step(np.full(3, 13, dtype=np.int64))
        assert reward.shape == (3, 1) and dones.shape == (3, 1)
        if env.done:
            raise AssertionError("environment terminated before the scheduled future request")
    assert info["future_request_active"] == 1.0
    assert not np.allclose(obs[:, future_rel_slice], 0.0)
    assert info["future_request_truth_exposed_to_actor"] is False
    print("PSCR_ADVERSARIAL_SERVICE_ENV_SMOKE_PASS")


if __name__ == "__main__":
    main()
