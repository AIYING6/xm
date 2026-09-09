from __future__ import annotations

import numpy as np

from algorithms.active_diagnosis.decision_relevant_probe import (
    bayes_task_regret,
    decision_equivalence_classes,
    decision_relevant_probe_value,
    select_probe,
)


BELIEF = np.asarray([0.5, 0.5])
TASK_VALUES = np.asarray([[2.0, 0.8], [0.0, 1.6]])
INFORMATIVE = np.asarray([[0.9, 0.1], [0.1, 0.9]])
UNINFORMATIVE = np.asarray([[0.5, 0.5], [0.5, 0.5]])


def test_decision_irrelevant_label_split_is_invariant() -> None:
    original = decision_relevant_probe_value(BELIEF, TASK_VALUES, INFORMATIVE, cost=0.2)
    split_belief = np.asarray([0.25, 0.25, 0.5])
    split_values = np.asarray([[2.0, 0.8], [2.0, 0.8], [0.0, 1.6]])
    split_kernel = np.asarray([[0.9, 0.1], [0.9, 0.1], [0.1, 0.9]])
    split = decision_relevant_probe_value(split_belief, split_values, split_kernel, cost=0.2)
    assert np.isclose(original.net_value, split.net_value)
    assert decision_equivalence_classes(split_values) == ((0, 1), (2,))


def test_information_cannot_increase_expected_bayes_regret_at_zero_cost() -> None:
    value = decision_relevant_probe_value(BELIEF, TASK_VALUES, INFORMATIVE, cost=0.0)
    assert value.expected_posterior_regret <= value.prior_regret + 1e-12
    assert value.net_value >= 0.0


def test_probe_is_rejected_above_regret_reduction_threshold() -> None:
    value = decision_relevant_probe_value(BELIEF, TASK_VALUES, INFORMATIVE, cost=1.0)
    selected, _ = select_probe(
        BELIEF,
        TASK_VALUES,
        {"handshake": INFORMATIVE},
        {"handshake": 1.0},
        budget_remaining=True,
    )
    assert value.net_value < 0.0
    assert selected is None


def test_oracle_value_upper_bounds_belief_decision_value() -> None:
    oracle = float(np.dot(BELIEF, np.max(TASK_VALUES, axis=1)))
    belief_value = float(np.max(BELIEF @ TASK_VALUES))
    assert oracle >= belief_value
    assert np.isclose(oracle - belief_value, bayes_task_regret(BELIEF, TASK_VALUES))


def test_uninformative_probe_is_rejected_when_costly() -> None:
    value = decision_relevant_probe_value(BELIEF, TASK_VALUES, UNINFORMATIVE, cost=0.01)
    assert np.isclose(value.prior_regret, value.expected_posterior_regret)
    assert np.isclose(value.net_value, -0.01)


def test_budget_prevents_an_otherwise_valuable_probe() -> None:
    selected, values = select_probe(
        BELIEF,
        TASK_VALUES,
        {"handshake": INFORMATIVE},
        {"handshake": 0.05},
        budget_remaining=False,
    )
    assert values["handshake"].net_value > 0.0
    assert selected is None
