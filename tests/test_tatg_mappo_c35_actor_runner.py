from __future__ import annotations

from scripts.audit_tatg_mappo_c35_actor_runner import collect_checks


def test_c35_actor_runner_passes_all_lifecycle_guards() -> None:
    checks, details = collect_checks()
    assert all(checks.values())
    assert details["environment_steps"] == 0
    assert details["formal_ppo_updates"] == 0
