from __future__ import annotations

from scripts.audit_tatg_mappo_c4_outer_rollout import collect_checks


def test_c4_outer_rollout_and_strict_continuation_pass_all_guards() -> None:
    checks, details = collect_checks()
    assert all(checks.values())
    assert details["environment_steps"] == 12
    assert details["ppo_updates"] == 0
    assert details["evaluation_episodes"] == 0
