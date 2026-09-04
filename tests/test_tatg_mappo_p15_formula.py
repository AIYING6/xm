from __future__ import annotations

import numpy as np

from scripts.audit_tatg_mappo_p15_formula import cetm_update, collect_checks, event_gate, load_freeze


def test_zero_transition_is_an_exact_memory_identity() -> None:
    memory = np.asarray([1.0, -2.0, 3.0])
    proposal = np.asarray([-4.0, 5.0, -6.0])
    assert event_gate(np.zeros(4)) == 0.0
    np.testing.assert_array_equal(cetm_update(memory, proposal, np.zeros(4)), memory)


def test_nonzero_transition_has_a_bounded_positive_gate() -> None:
    gate = event_gate(np.ones(4))
    assert 0.0 < gate < 1.0


def test_frozen_formula_passes_all_static_guards() -> None:
    assert all(collect_checks(load_freeze()).values())
