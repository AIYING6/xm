"""Deterministic N0 tests for evaluator-defined standoff neutralization.

These tests are intentionally environment-only.  They neither instantiate a
policy nor use graph, cache, or communication inputs as part of the transition.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from envs.uav_intercept_3d_env import (
    ACTION3D_TABLE,
    FLIGHT_ACTION_DIM,
    ROLE_ATTACKER,
    UAVIntercept3DConfig,
    UAVIntercept3DEnv,
)


def _base_action() -> int:
    return int(np.flatnonzero(np.all(ACTION3D_TABLE == 0.0, axis=1))[0])


def _make_env(*, collision_radius: float = 120.0) -> tuple[UAVIntercept3DEnv, int]:
    env = UAVIntercept3DEnv(
        UAVIntercept3DConfig(
            mission_neutralization_enabled=True,
            engage_commit_hold_steps=4,
            collision_radius=collision_radius,
            target_policy="straight",
            seed=17,
        )
    )
    env.reset()
    attacker = next(i for i, typ in enumerate(env.config.blue_types) if typ.role == ROLE_ATTACKER)

    # A pure true-state geometry: target and attacker fly toward each other,
    # remaining inside the 1.4--5.2 km envelope for four transitions.
    env.red_pos[0] = np.asarray([0.0, 0.0, 5_000.0], dtype=np.float32)
    env.red_speed[0] = 210.0
    env.red_heading[0] = math.pi
    env.red_gamma[0] = 0.0
    env.blue_pos[:] = np.asarray(
        [[-12_000.0, -10_000.0, 5_000.0], [-12_000.0, 10_000.0, 5_000.0], [-4_800.0, 0.0, 5_000.0]],
        dtype=np.float32,
    )
    env.blue_speed[:] = np.asarray([175.0, 175.0, 250.0], dtype=np.float32)
    env.blue_heading[:] = np.asarray([0.0, 0.0, 0.0], dtype=np.float32)
    env.blue_gamma[:] = 0.0
    return env, attacker


def _actions(attacker: int, commit: bool) -> np.ndarray:
    actions = np.full(3, _base_action(), dtype=np.int64)
    if commit:
        actions[attacker] += FLIGHT_ACTION_DIM
    return actions


def _step(env: UAVIntercept3DEnv, attacker: int, commit: bool) -> dict[str, float]:
    return env.step(_actions(attacker, commit))[-1]


def test_four_committed_steps_neutralize() -> None:
    env, attacker = _make_env()
    for _ in range(3):
        info = _step(env, attacker, True)
        assert info["target_neutralized"] == 0.0 and not env.done
    info = _step(env, attacker, True)
    assert info["target_neutralized"] == 1.0
    assert info["success"] == 1.0 and env.done
    assert info["engage_commit_hold"] == 4.0


def test_three_committed_steps_do_not_neutralize() -> None:
    env, attacker = _make_env()
    for _ in range(3):
        info = _step(env, attacker, True)
    assert info["target_neutralized"] == 0.0
    assert info["engage_commit_hold"] == 3.0
    assert not env.done


def test_each_geometry_condition_is_necessary() -> None:
    env, attacker = _make_env()
    commits = np.zeros(3, dtype=bool)
    commits[attacker] = True
    assert env._neutralization_eligible(commits)

    env.blue_pos[attacker, 0] = -6_000.0  # range
    assert not env._neutralization_eligible(commits)
    env.blue_pos[attacker, 0] = -4_800.0

    env.blue_heading[attacker] = math.pi  # heading
    assert not env._neutralization_eligible(commits)
    env.blue_heading[attacker] = 0.0

    env.blue_pos[attacker, 2] = 7_000.0  # altitude separation
    assert not env._neutralization_eligible(commits)
    env.blue_pos[attacker, 2] = 5_000.0

    env.red_heading[0] = 0.0  # radial closure
    env.blue_speed[attacker] = 135.0
    assert not env._neutralization_eligible(commits)


def test_commit_is_causally_required_with_fixed_physics() -> None:
    committed, attacker = _make_env()
    uncommitted, other_attacker = _make_env()
    for _ in range(4):
        committed_info = _step(committed, attacker, True)
        uncommitted_info = _step(uncommitted, other_attacker, False)
    assert committed_info["target_neutralized"] == 1.0
    assert uncommitted_info["target_neutralized"] == 0.0


def test_cache_communication_and_graph_cannot_change_transition() -> None:
    clean, attacker = _make_env()
    altered, altered_attacker = _make_env()
    altered.comm_adj[:] = 0.0
    altered.message_age[:] = 999.0
    altered.target_cache_valid[:] = 1.0
    altered.target_cache_pos[:] = 123_456.0
    altered.target_cache_confidence[:] = 0.0
    altered.attack_hold = altered.config.attack_hold_steps
    for _ in range(4):
        clean_info = _step(clean, attacker, True)
        altered_info = _step(altered, altered_attacker, True)
    assert clean_info["target_neutralized"] == altered_info["target_neutralized"] == 1.0
    assert clean_info["engage_commit_hold"] == altered_info["engage_commit_hold"] == 4.0


def test_chain_closed_alone_cannot_neutralize() -> None:
    env, attacker = _make_env()
    env.attack_hold = env.config.attack_hold_steps
    for _ in range(4):
        info = _step(env, attacker, False)
    assert info["target_neutralized"] == 0.0
    assert info["success"] == 0.0
    assert info["engage_commit_hold"] == 0.0


def test_collision_has_precedence_over_neutralization() -> None:
    env, attacker = _make_env(collision_radius=3_000.0)
    env.blue_pos[attacker, 0] = -3_000.0
    env.engage_commit_hold = 3
    info = _step(env, attacker, True)
    assert info["collision"] == 1.0
    assert info["target_neutralized"] == 0.0
    assert info["success"] == 0.0
    assert info["engage_commit_hold"] == 0.0
    assert env.done


def main() -> None:
    tests = [
        test_four_committed_steps_neutralize,
        test_three_committed_steps_do_not_neutralize,
        test_each_geometry_condition_is_necessary,
        test_commit_is_causally_required_with_fixed_physics,
        test_cache_communication_and_graph_cannot_change_transition,
        test_chain_closed_alone_cannot_neutralize,
        test_collision_has_precedence_over_neutralization,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("N0_MISSION_PHYSICS_TEST_REPORT: PASS (7 tests)")


if __name__ == "__main__":
    main()
