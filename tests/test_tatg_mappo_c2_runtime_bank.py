from __future__ import annotations

from scripts.audit_tatg_mappo_c2_runtime_bank import collect_checks


def test_c2_runtime_state_bank_passes_all_guards() -> None:
    checks, state_shape = collect_checks()
    assert all(checks.values())
    assert state_shape["batch_size"] == 3
