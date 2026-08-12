"""P0 semantic tests for the frozen Phase2IB relay-dependent task.

These tests deliberately inspect information semantics only.  They do not
train, evaluate a checkpoint, calculate recovery statistics, or write results.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv


def _cfg(**overrides: object) -> UAVIntercept3DConfig:
    values: dict[str, object] = {
        "seed": 21801,
        "target_policy": "straight",
        "strict_target_sensing": True,
        "agent_target_info_bottleneck": True,
        "relay_dependent_task": True,
        "communication_dropout_prob": 0.0,
        "message_delay_steps": 0,
        "radar_dropout_prob": 0.0,
    }
    values.update(overrides)
    return UAVIntercept3DConfig(**values)


def _cache(env: UAVIntercept3DEnv, agent_id: int, path: list[int]) -> None:
    env._write_target_cache(
        agent_id,
        pos=env.red_pos[0],
        vel=np.zeros(3, dtype=np.float32),
        source=0,
        generation_step=env.step_count,
        delivery_step=env.step_count,
        hop_count=len(path) - 1,
        confidence=1.0,
        path=path,
    )


def test_invalid_configuration_is_rejected() -> None:
    try:
        UAVIntercept3DEnv(UAVIntercept3DConfig(relay_dependent_task=True))
    except ValueError as exc:
        assert "strict_target_sensing" in str(exc)
    else:
        raise AssertionError("relay-dependent mode without strict prerequisites was accepted")


def test_attacker_direct_sensor_is_disabled_but_scout_sensor_is_not() -> None:
    env = UAVIntercept3DEnv(_cfg())
    env.reset()
    attacker = 2
    scout = 0
    # Put both platforms at the same valid radar pose. The difference must be
    # policy, not geometry.
    env.blue_pos[attacker] = env.red_pos[0] - np.asarray([1_000.0, 0.0, 0.0], dtype=np.float32)
    env.blue_pos[scout] = env.red_pos[0] - np.asarray([1_000.0, 0.0, 0.0], dtype=np.float32)
    env.blue_heading[attacker] = 0.0
    env.blue_heading[scout] = 0.0
    env.blue_gamma[attacker] = 0.0
    env.blue_gamma[scout] = 0.0
    assert not env._radar_visible(attacker, env.config.blue_types[attacker])
    assert env._radar_visible(scout, env.config.blue_types[scout])


def test_bypass_cache_is_rejected_and_relay_cache_is_accepted() -> None:
    env = UAVIntercept3DEnv(_cfg())
    env.reset()
    _cache(env, 2, [0, 2])
    assert env.target_cache_valid[2] == 0.0
    assert not env._has_target_information(2)
    _cache(env, 2, [0, 1, 2])
    assert env.target_cache_valid[2] == 1.0
    assert env.target_cache_path[2] == [0, 1, 2]
    assert env._has_target_information(2)


def test_relay_failure_makes_relay_cache_unavailable_until_rebuilt() -> None:
    env = UAVIntercept3DEnv(_cfg(failed_blue_agent=1, node_failure_start_step=5, node_failure_duration_steps=10))
    env.reset()
    _cache(env, 2, [0, 1, 2])
    assert env._has_target_information(2)
    env.step_count = 5
    assert not env._has_target_information(2)
    env.step_count = 15
    assert env._has_target_information(2)


def test_legacy_mode_accepts_direct_attacker_sensing_and_cache() -> None:
    env = UAVIntercept3DEnv(
        UAVIntercept3DConfig(
            seed=21802,
            strict_target_sensing=True,
            agent_target_info_bottleneck=True,
            relay_dependent_task=False,
        )
    )
    env.reset()
    env.blue_pos[2] = env.red_pos[0] - np.asarray([1_000.0, 0.0, 0.0], dtype=np.float32)
    env.blue_heading[2] = 0.0
    env.blue_gamma[2] = 0.0
    assert env._radar_visible(2, env.config.blue_types[2])
    _cache(env, 2, [0, 2])
    assert env._has_target_information(2)


def main() -> None:
    for test in (
        test_invalid_configuration_is_rejected,
        test_attacker_direct_sensor_is_disabled_but_scout_sensor_is_not,
        test_bypass_cache_is_rejected_and_relay_cache_is_accepted,
        test_relay_failure_makes_relay_cache_unavailable_until_rebuilt,
        test_legacy_mode_accepts_direct_attacker_sensing_and_cache,
    ):
        test()
        print(f"PASS {test.__name__}")
    print("PHASE2IB P0 semantic tests: PASS")


if __name__ == "__main__":
    main()
