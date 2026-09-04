from __future__ import annotations

from scripts.audit_tatg_mappo_c3_sequence_replay import collect_checks


def test_c3_sequence_replay_passes_all_correctness_guards() -> None:
    checks, details = collect_checks()
    assert all(checks.values())
    assert details["sequence_time_steps"] == 4
    assert details["sequence_environments"] == 2
