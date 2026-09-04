from __future__ import annotations

from scripts.audit_tatg_mappo_c45_first_update import collect_checks


def test_c45_first_update_same_rollout_passes_all_frozen_guards() -> None:
    checks, details = collect_checks()
    assert all(checks.values())
    assert details["environment_steps"] == 6
    assert details["audit_actor_optimizer_steps"] == 3
    assert details["formal_ppo_updates"] == 0
    assert details["evaluation_episodes"] == 0
