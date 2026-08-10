"""N2 deterministic checks that the new mission reward cannot pay old proxies."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOConfig, make_env  # noqa: E402
from envs.uav_intercept_3d_env import ACTION3D_TABLE, UAVIntercept3DConfig, UAVIntercept3DEnv  # noqa: E402


def _base_action() -> int:
    return int(np.flatnonzero(np.all(ACTION3D_TABLE == 0.0, axis=1))[0])


def _env(*, shaping: bool = False) -> UAVIntercept3DEnv:
    env = UAVIntercept3DEnv(
        UAVIntercept3DConfig(
            mission_neutralization_enabled=True,
            target_escape_radius=35_000.0,
            target_policy="straight",
            mission_progress_shaping_enabled=shaping,
            seed=31,
        )
    )
    env.reset()
    return env


def test_mission_reward_does_not_read_old_proxy_methods() -> None:
    env = _env()
    env._comm_connectivity = lambda: (_ for _ in ()).throw(AssertionError("communication proxy read"))  # type: ignore[method-assign]
    env._mean_message_age = lambda: (_ for _ in ()).throw(AssertionError("packet-age proxy read"))  # type: ignore[method-assign]
    env._attack_geometry_score = lambda: (_ for _ in ()).throw(AssertionError("geometry proxy read"))  # type: ignore[method-assign]
    rewards = env._compute_rewards(20_000.0, 19_500.0, 0.0, 1.0, 0.0, 1.0)
    assert np.all(np.isfinite(rewards))


def test_chain_and_communication_cannot_change_mission_reward() -> None:
    clean, hacked = _env(), _env()
    hacked.attack_hold = hacked.config.attack_hold_steps
    hacked.comm_adj[:] = 1.0
    hacked.message_age[:] = 0.0
    hacked.detected_by[:] = 1.0
    hacked.attack_window[:] = 1.0
    hacked.local_attack_window[:] = 1.0
    hacked.target_cache_valid[:] = 1.0
    clean_reward = clean._compute_rewards(20_000.0, 19_500.0, 0.0, 0.0, 0.0, 0.0)
    hacked_reward = hacked._compute_rewards(20_000.0, 19_500.0, 1.0, 1.0, 1.0, 1.0)
    assert np.array_equal(clean_reward, hacked_reward)


def test_only_frozen_terminal_outcomes_change_terminal_reward() -> None:
    env = _env()
    baseline = float(env._compute_rewards(10_000.0, 10_000.0, 0.0, 0.0, 0.0, 0.0)[0, 0])
    env.target_neutralized = True
    env.success = True
    neutralized = float(env._compute_rewards(10_000.0, 10_000.0, 0.0, 0.0, 0.0, 0.0)[0, 0])
    env.target_neutralized = False
    env.success = False
    env.target_escaped = True
    escaped = float(env._compute_rewards(10_000.0, 10_000.0, 0.0, 0.0, 0.0, 0.0)[0, 0])
    assert neutralized > baseline > escaped


def test_new_task_parameters_reach_3d_training_factory() -> None:
    cfg = RIGMAPPOConfig(
        env_name="3d_intercept",
        mission_neutralization_enabled=True,
        engage_commit_hold_steps=4,
        target_escape_radius=35_000.0,
        mission_max_steps=360,
        strict_target_sensing=True,
        agent_target_info_bottleneck=True,
    )
    env = make_env(cfg, seed=41, training=True)
    assert env.action_dim == 54
    assert env.config.max_steps == 360
    assert env.config.target_escape_radius == 35_000.0
    assert env.config.strict_target_sensing and env.config.agent_target_info_bottleneck


def test_potential_repair_is_physical_and_does_not_read_proxies() -> None:
    env = _env(shaping=True)
    env._comm_connectivity = lambda: (_ for _ in ()).throw(AssertionError("communication proxy read"))  # type: ignore[method-assign]
    env._mean_message_age = lambda: (_ for _ in ()).throw(AssertionError("age proxy read"))  # type: ignore[method-assign]
    prev_phi = env._mission_progress_potential()
    env.blue_pos[2] += np.asarray([300.0, 0.0, 0.0], dtype=np.float32)
    env.engage_commit_hold = 1
    cur_phi = env._mission_progress_potential()
    shaped = float(env._compute_rewards(20_000.0, 20_000.0, 0.0, 0.0, 0.0, 0.0, prev_phi, cur_phi)[0, 0])
    assert np.isfinite(shaped)
    assert shaped != -0.01


def main() -> None:
    tests = [
        test_mission_reward_does_not_read_old_proxy_methods,
        test_chain_and_communication_cannot_change_mission_reward,
        test_only_frozen_terminal_outcomes_change_terminal_reward,
        test_new_task_parameters_reach_3d_training_factory,
        test_potential_repair_is_physical_and_does_not_read_proxies,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("N2_REWARD_SANITY_TEST_REPORT: PASS (5 tests)")


if __name__ == "__main__":
    main()
