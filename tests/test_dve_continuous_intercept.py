import numpy as np

from envs.dve_continuous_intercept import ContinuousInterceptAudit, InterceptCase


def make_case(latency: float = 0.2) -> InterceptCase:
    return InterceptCase(
        latency=latency,
        agent_positions=np.asarray([[0.0, -1.0], [0.0, 1.0]], dtype=float),
        target_position=np.asarray([5.0, 0.0], dtype=float),
        target_velocity=np.asarray([0.4, 0.2], dtype=float),
        target_maneuver=np.asarray([0.1, -0.15], dtype=float),
    )


def test_latency_advances_agents_and_target_before_admission() -> None:
    audit = ContinuousInterceptAudit(make_case())

    assert not np.allclose(audit.completion_agents, audit.case.agent_positions)
    assert not np.allclose(audit.completion_target, audit.case.target_position)


def test_evaluation_is_finite_and_reports_validity_fields() -> None:
    result = ContinuousInterceptAudit(make_case()).evaluate()

    assert set(result) == {
        "both_stale",
        "both_fallback",
        "first_stale",
        "second_stale",
        "stale_task_valid",
        "individually_safe_jointly_unsafe",
    }
    for rollout_name in ("both_stale", "both_fallback", "first_stale", "second_stale"):
        rollout = result[rollout_name]
        assert np.isfinite(rollout["value"])
        assert np.isfinite(rollout["mean_distance"])
        assert np.isfinite(rollout["min_separation"])
        assert isinstance(rollout["safe"], (bool, np.bool_))


def test_delayed_replan_holds_before_executing_fresh_action() -> None:
    audit = ContinuousInterceptAudit(make_case(latency=0.2))
    result = audit.delayed_replan_rollout()

    assert result["hold_duration"] == 0.2
    assert np.isclose(result["execution_duration"], audit.horizon - 0.2)
    assert np.isfinite(result["value"])
