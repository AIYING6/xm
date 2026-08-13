from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOConfig, make_env
from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv
from scripts.run_phase_s3_development_smoke import ENV_STEPS, METHODS, NUM_ENVS, ROLLOUT_STEPS, SEEDS, UPDATES, training_config


def test_business_grounded_geometry_is_opt_in_and_exact() -> None:
    env = UAVIntercept3DEnv(
        UAVIntercept3DConfig(
            seed=1501,
            strict_target_sensing=True,
            agent_target_info_bottleneck=True,
            relay_dependent_task=True,
            business_grounded_geometry=True,
        )
    )
    env.reset()
    np.testing.assert_allclose(
        env.blue_pos,
        np.asarray([[-2000.0, -6000.0, 5000.0], [-2000.0, 0.0, 5000.0], [-2000.0, 6000.0, 5000.0]], dtype=np.float32),
    )
    np.testing.assert_allclose(env.blue_heading, 0.0)
    np.testing.assert_allclose(env.blue_gamma, 0.0)


def test_s3_training_contract_is_fixed_and_failure_on() -> None:
    cfg = training_config(METHODS["full"], SEEDS[0], Path("unused"), UPDATES)
    assert ENV_STEPS == NUM_ENVS * ROLLOUT_STEPS * UPDATES == 200192
    assert cfg.failed_blue_agent == 1
    assert cfg.node_failure_start_step == 44
    assert cfg.node_failure_duration_steps == 80
    assert cfg.relay_dependent_task
    assert cfg.business_grounded_geometry
    assert not cfg.evaluation_enabled
    assert cfg.resume is None and cfg.init_checkpoint is None


def test_core_factory_passes_frozen_s3_flags_to_environment() -> None:
    cfg = RIGMAPPOConfig(
        env_name="3d_intercept",
        seed=1501,
        strict_target_sensing=True,
        agent_target_info_bottleneck=True,
        relay_dependent_task=True,
        business_grounded_geometry=True,
    )
    env = make_env(cfg, 1501, training=True)
    assert env.config.relay_dependent_task
    assert env.config.business_grounded_geometry
