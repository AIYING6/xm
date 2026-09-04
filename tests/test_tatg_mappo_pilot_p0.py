from __future__ import annotations

from scripts.audit_tatg_mappo_pilot_p0 import collect_checks


def test_tatg_pilot_p0_preregistration_is_complete_without_execution() -> None:
    checks, details = collect_checks()
    assert all(checks.values())
    assert details["environment_steps_executed"] == 0
    assert details["ppo_updates_executed"] == 0
    assert details["evaluation_episodes_executed"] == 0
    assert details["total_environment_steps_if_authorized"] == 12_002_304
