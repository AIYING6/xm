"""Deterministic read-only audit for a physical engagement-readiness outcome."""
from __future__ import annotations

import inspect
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from envs.uav_intercept_3d_env import (  # noqa: E402
    UAVIntercept3DConfig, UAVIntercept3DEnv, physical_engagement_ready,
)
from algorithms.ri_gmappo.simple_ri_gmappo import summarize_validation_event_records  # noqa: E402

STABILITY_STEPS = 4


def first_stable_physical_engagement(ready: list[bool], k: int = STABILITY_STEPS) -> int | None:
    hold = 0
    for step, value in enumerate(ready):
        hold = hold + 1 if value else 0
        if hold >= k:
            return step - k + 1
    return None


def configured_env() -> UAVIntercept3DEnv:
    env = UAVIntercept3DEnv(UAVIntercept3DConfig(
        strict_target_sensing=True, agent_target_info_bottleneck=True,
        communication_dropout_prob=0.3, message_delay_steps=2, radar_dropout_prob=0.1,
        failed_blue_agent=1, node_failure_start_step=40, node_failure_duration_steps=80,
        attack_hold_steps=STABILITY_STEPS, min_success_step=80, seed=71,
    ))
    env.reset()
    env.red_pos[0] = np.asarray((10_000.0, 0.0, 5_000.0), dtype=np.float32)
    env.red_speed[0], env.red_heading[0], env.red_gamma[0] = 255.0, 0.0, 0.0
    env.blue_pos[2] = np.asarray((6_000.0, 0.0, 5_000.0), dtype=np.float32)
    env.blue_speed[2], env.blue_heading[2], env.blue_gamma[2] = 270.0, 0.0, 0.0
    env.detected_by[:] = 0.0
    env.target_cache_valid[:] = 0.0
    env.target_cache_generation_step[:] = -1
    env.target_cache_confidence[:] = 0.0
    env.comm_adj[:] = 0.0
    env.attack_hold = 0
    return env


def test_outcome_uses_only_true_physical_state() -> None:
    source = inspect.getsource(physical_engagement_ready).lower()
    assert not any(token in source for token in ("chain", "comm", "cache", "packet", "graph", "pcrf", "detect", "message"))


def test_true_safe_engagement_can_exist_without_task_chain() -> None:
    env = configured_env()
    assert physical_engagement_ready(env, 2)
    assert not env._comm_has_chain_to_attacker()
    assert env.attack_hold < env.config.attack_hold_steps
    assert not env._has_collision()


def test_each_frozen_physical_constraint_is_necessary() -> None:
    env = configured_env()
    assert physical_engagement_ready(env, 2)
    env.blue_pos[2, 0] = 9_000.0
    assert not physical_engagement_ready(env, 2)
    env = configured_env()
    env.blue_heading[2] = math.pi
    assert not physical_engagement_ready(env, 2)
    env = configured_env()
    env.blue_pos[2, 2] += 2_000.0
    assert not physical_engagement_ready(env, 2)
    env = configured_env()
    env.blue_speed[2], env.red_speed[0] = env.config.blue_types[2].min_speed, env.config.target_type.max_speed
    assert not physical_engagement_ready(env, 2)


def test_stability_is_an_evaluator_counter_not_chain_closed() -> None:
    assert first_stable_physical_engagement([True, True, True, True]) == 0
    assert first_stable_physical_engagement([True, True, False, True, True, True, True]) == 3
    assert first_stable_physical_engagement([True, True, True]) is None


def test_safe_physical_envelope_excludes_collision_radius() -> None:
    env = configured_env()
    assert env.config.blue_types[2].attack_range_min > env.config.collision_radius


def test_rmpe_is_logged_from_the_frozen_physical_event() -> None:
    records = [
        {
            "event_observed": 0, "event_time": -1, "terminal_failure_observed": 0,
            "terminal_failure_time": -1, "physical_event_observed": 1, "physical_event_time": 50,
        },
        {
            "event_observed": 0, "event_time": -1, "terminal_failure_observed": 1,
            "terminal_failure_time": 20, "physical_event_observed": 0, "physical_event_time": -1,
        },
    ]
    summary = summarize_validation_event_records(records)
    assert summary["eval_rmpe80"] == 65.0
    assert summary["eval_physical_engagement_probability80"] == 0.5
    assert summary["eval_rmpe220"] == 135.0


def main() -> None:
    tests = [test_outcome_uses_only_true_physical_state, test_true_safe_engagement_can_exist_without_task_chain,
             test_each_frozen_physical_constraint_is_necessary, test_stability_is_an_evaluator_counter_not_chain_closed,
             test_safe_physical_envelope_excludes_collision_radius, test_rmpe_is_logged_from_the_frozen_physical_event]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"P1_INDEPENDENT_PHYSICAL_ENGAGEMENT_AUDIT_V1_9: PASS ({len(tests)} tests)")


if __name__ == "__main__":
    main()
