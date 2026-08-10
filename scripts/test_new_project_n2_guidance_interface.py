"""Deterministic checks for the authorized guidance-level action interface."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np

from envs.uav_intercept_3d_env import GUIDANCE_FLIGHT_ACTION_DIM, FLIGHT_ACTION_DIM
from scripts.run_new_project_n2_guidance_repair import guidance_cfg
from algorithms.ri_gmappo.simple_ri_gmappo import make_env


def test_guidance_has_reduced_flight_action_space():
    cfg = guidance_cfg(8801, Path("results/_guidance_test"))
    env = make_env(cfg, 8801, training=False)
    assert env.action_dim == 2 * GUIDANCE_FLIGHT_ACTION_DIM
    assert env.action_dim < 2 * FLIGHT_ACTION_DIM


def test_guidance_step_is_finite_and_keeps_mission_contract():
    cfg = guidance_cfg(8802, Path("results/_guidance_test"))
    env = make_env(cfg, 8802, training=False)
    _obs, _share, _graph = env.reset()
    _obs, _share, _graph, reward, dones, info = env.step(np.zeros(env.num_agents, dtype=np.int64))
    assert np.isfinite(reward).all()
    assert not bool(np.all(dones))
    assert float(info.get("target_neutralized", 0.0)) == 0.0


if __name__ == "__main__":
    for test in (test_guidance_has_reduced_flight_action_space, test_guidance_step_is_finite_and_keeps_mission_contract):
        test()
        print(f"PASS {test.__name__}")
    print("N2_GUIDANCE_INTERFACE_TEST_REPORT: PASS (2 tests)")
