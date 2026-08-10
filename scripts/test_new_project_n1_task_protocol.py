"""Deterministic N1 checks for terminal taxonomy and actor-boundary additions."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from envs.uav_intercept_3d_env import (  # noqa: E402
    ACTION3D_TABLE,
    FLIGHT_ACTION_DIM,
    ROLE_ATTACKER,
    UAVIntercept3DConfig,
    UAVIntercept3DEnv,
)


def _base_action() -> int:
    return int(np.flatnonzero(np.all(ACTION3D_TABLE == 0.0, axis=1))[0])


def _configured_env(escape_radius: float) -> tuple[UAVIntercept3DEnv, int]:
    env = UAVIntercept3DEnv(
        UAVIntercept3DConfig(
            mission_neutralization_enabled=True,
            target_escape_radius=escape_radius,
            target_policy="straight",
            seed=23,
        )
    )
    env.reset()
    attacker = next(i for i, typ in enumerate(env.config.blue_types) if typ.role == ROLE_ATTACKER)
    return env, attacker


def _standoff_state(env: UAVIntercept3DEnv, attacker: int, *, origin_x: float = 0.0) -> None:
    env.red_pos[0] = np.asarray([origin_x, 0.0, 5_000.0], dtype=np.float32)
    env.red_speed[0] = 210.0
    env.red_heading[0] = 0.0
    env.red_gamma[0] = 0.0
    env.blue_pos[:] = np.asarray(
        [[origin_x - 12_000.0, -10_000.0, 5_000.0], [origin_x - 12_000.0, 10_000.0, 5_000.0], [origin_x - 3_000.0, 0.0, 5_000.0]],
        dtype=np.float32,
    )
    env.blue_speed[:] = np.asarray([175.0, 175.0, 250.0], dtype=np.float32)
    env.blue_heading[:] = 0.0
    env.blue_gamma[:] = 0.0
    assert env.config.blue_types[attacker].role == ROLE_ATTACKER


def _actions(attacker: int | None = None) -> np.ndarray:
    actions = np.full(3, _base_action(), dtype=np.int64)
    if attacker is not None:
        actions[attacker] += FLIGHT_ACTION_DIM
    return actions


def test_target_escape_is_terminal_outcome() -> None:
    env, _ = _configured_env(escape_radius=100.0)
    env.red_pos[0, :2] = np.asarray([150.0, 0.0], dtype=np.float32)
    env.red_heading[0] = 0.0
    env.red_speed[0] = 210.0
    _obs, _share, _graph, _rewards, dones, info = env.step(_actions())
    assert info["target_escape"] == 1.0
    assert info["success"] == 0.0 and info["timeout"] == 0.0
    assert bool(np.all(dones))


def test_neutralization_beats_same_step_escape() -> None:
    env, attacker = _configured_env(escape_radius=35_000.0)
    _standoff_state(env, attacker, origin_x=34_900.0)
    env.engage_commit_hold = 3
    _obs, _share, _graph, _rewards, dones, info = env.step(_actions(attacker))
    assert info["target_neutralized"] == 1.0
    assert info["target_escape"] == 0.0
    assert info["success"] == 1.0 and bool(np.all(dones))


def test_nonattacker_commit_is_noop() -> None:
    env, attacker = _configured_env(escape_radius=35_000.0)
    _standoff_state(env, attacker)
    for _ in range(4):
        _obs, _share, _graph, _rewards, dones, info = env.step(_actions(0))
        assert not bool(np.all(dones))
    assert info["engage_commit_active"] == 0.0
    assert info["target_neutralized"] == 0.0


def test_evaluator_lifecycle_state_is_not_actor_input() -> None:
    env, _ = _configured_env(escape_radius=35_000.0)
    actor_obs_before = env._get_obs().copy()
    graph_before = env._get_graph_obs()
    env.target_neutralized = True
    env.target_escaped = True
    env.engage_commit_hold = 4
    actor_obs_after = env._get_obs()
    graph_after = env._get_graph_obs()
    assert np.array_equal(actor_obs_before, actor_obs_after)
    for key in graph_before:
        assert np.array_equal(graph_before[key], graph_after[key]), key


def main() -> None:
    tests = [
        test_target_escape_is_terminal_outcome,
        test_neutralization_beats_same_step_escape,
        test_nonattacker_commit_is_noop,
        test_evaluator_lifecycle_state_is_not_actor_input,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("N1_TASK_PROTOCOL_TEST_REPORT: PASS (4 tests)")


if __name__ == "__main__":
    main()
