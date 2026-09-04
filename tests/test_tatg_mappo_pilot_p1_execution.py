from __future__ import annotations

from scripts.audit_tatg_mappo_pilot_p1_execution import collect_checks


def test_tatg_pilot_execution_interface_is_ready_without_execution() -> None:
    checks, details = collect_checks()
    assert all(checks.values())
    assert details["environment_steps_executed"] == 0
    assert details["ppo_updates_executed"] == 0
    assert details["evaluation_episodes_executed"] == 0
