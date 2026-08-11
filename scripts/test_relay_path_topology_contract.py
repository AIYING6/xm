"""Deterministic guard for the opt-in physical Relay-path formation."""
from __future__ import annotations

from dataclasses import replace
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from envs.uav_intercept_3d_env import (ROLE_ATTACKER, ROLE_RELAY, ROLE_SCOUT, UAVIntercept3DConfig, UAVIntercept3DEnv)


def configured() -> UAVIntercept3DEnv:
    return UAVIntercept3DEnv(UAVIntercept3DConfig(
        seed=77, communication_range_scale=0.5, communication_dropout_prob=0.0,
        message_delay_steps=0, strict_target_sensing=True,
        agent_target_info_bottleneck=True, relay_identifiable_initial_formation=True,
    ))


def ids(env):
    return {typ.role: i for i, typ in enumerate(env.config.blue_types)}


def target_setup(env):
    # Scout can sense an ahead target; Relay and Attacker cannot locally sense it.
    env.red_pos[0] = np.asarray((-2_000.0, -4_200.0, 5_000.0), dtype=np.float32)
    env.red_speed[0] = 210.0; env.red_heading[0] = np.pi; env.red_gamma[0] = 0.0
    env._update_sensing_and_comm()


def relay_delivery(env):
    target_setup(env)
    env._update_sensing_and_comm()


def test_physical_two_hop_and_no_direct_link():
    env = configured(); r = ids(env); scale = env.config.communication_range_scale
    def linked(a, b):
        distance = float(np.linalg.norm(env.blue_pos[a] - env.blue_pos[b]))
        limit = scale * min(env.config.blue_types[a].comm_range, env.config.blue_types[b].comm_range)
        return distance <= limit
    assert linked(r[ROLE_SCOUT], r[ROLE_RELAY])
    assert linked(r[ROLE_RELAY], r[ROLE_ATTACKER])
    assert not linked(r[ROLE_SCOUT], r[ROLE_ATTACKER])


def test_relay_forwards_fresh_target_to_attacker():
    env = configured(); r = ids(env); relay_delivery(env)
    attacker = r[ROLE_ATTACKER]
    assert env.detected_by[attacker] == 0.0
    assert env._has_fresh_target_cache(attacker)
    assert env.target_cache_path[attacker] == [r[ROLE_SCOUT], r[ROLE_RELAY], attacker]


def test_relay_removal_changes_actor_information_not_physics():
    active = configured(); blocked = configured(); r = ids(active); target_setup(active); target_setup(blocked)
    relay = r[ROLE_RELAY]
    original = blocked._is_comm_failed
    blocked._is_comm_failed = lambda agent: bool(original(agent) or agent == relay)  # type: ignore[method-assign]
    active._update_sensing_and_comm(); blocked._update_sensing_and_comm()
    active_obs = active._get_obs()[r[ROLE_ATTACKER]]
    blocked_obs = blocked._get_obs()[r[ROLE_ATTACKER]]
    assert active._has_fresh_target_cache(r[ROLE_ATTACKER])
    assert not blocked._has_fresh_target_cache(r[ROLE_ATTACKER])
    assert not np.array_equal(active_obs, blocked_obs)
    assert np.array_equal(active.blue_pos, blocked.blue_pos)
    assert np.array_equal(active.red_pos, blocked.red_pos)


def main():
    tests = [test_physical_two_hop_and_no_direct_link, test_relay_forwards_fresh_target_to_attacker, test_relay_removal_changes_actor_information_not_physics]
    for test in tests:
        test(); print(f"PASS {test.__name__}")
    print("RELAY_PATH_TOPOLOGY_CONTRACT_TEST_REPORT: PASS (3 tests)")


if __name__ == "__main__":
    main()
