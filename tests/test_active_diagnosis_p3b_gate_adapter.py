import numpy as np

from algorithms.active_diagnosis.pilot_gate_adapter import (
    FailureBelief,
    ProbeGate,
    apply_forced_options,
    policy_action_masks,
)


KERNEL = np.asarray([[0.9, 0.1], [0.1, 0.9]])
TASK_VALUES = np.asarray([[2.0, 0.8], [0.0, 1.6]])


def test_forced_option_is_excluded_from_actor_attribution() -> None:
    gate = ProbeGate("decision_relevant", FailureBelief(0.5, KERNEL), 0.12)
    decision = gate.initial_decision(TASK_VALUES)
    actions, control = apply_forced_options(np.asarray([3, 4, 5]), decision, 1, 2, 27, 28)
    assert actions.tolist() == [3, 27, 5]
    assert control.tolist() == [1.0, 0.0, 1.0]


def test_no_ack_updates_shared_belief_and_forces_fallback() -> None:
    gate = ProbeGate("entropy", FailureBelief(0.5, KERNEL), 0.12)
    gate.initial_decision()
    decision = gate.completed_probe_decision(-1.0)
    actions, control = apply_forced_options(np.asarray([3, 4, 5]), decision, 1, 2, 27, 28)
    assert gate.belief.probabilities[1] > gate.belief.probabilities[0]
    assert actions.tolist() == [3, 4, 28]
    assert control.tolist() == [1.0, 1.0, 0.0]


def test_high_confidence_prior_can_separate_entropy_and_task_gates() -> None:
    entropy = ProbeGate("entropy", FailureBelief(0.9, KERNEL), 0.12).initial_decision()
    task = ProbeGate("decision_relevant", FailureBelief(0.9, KERNEL), 0.12).initial_decision(TASK_VALUES)
    assert entropy.force_probe is True
    assert task.force_fallback is True


def test_gate_runtime_state_restores_exactly() -> None:
    first = ProbeGate("decision_relevant", FailureBelief(0.5, KERNEL), 0.12)
    first.initial_decision(TASK_VALUES)
    first.completed_probe_decision(1.0)
    state = first.state_dict()
    second = ProbeGate("decision_relevant", FailureBelief(0.5, KERNEL), 0.12)
    second.load_state_dict(state)
    assert np.array_equal(first.belief.probabilities, second.belief.probabilities)
    assert first.state_dict()["last_ack_state"] == second.state_dict()["last_ack_state"]


def test_gated_policy_mask_contains_flight_actions_only() -> None:
    environment = np.ones((3, 29), dtype=np.float32)
    masks = policy_action_masks(environment, 27, 28)
    assert np.all(masks[:, :27] == 1.0)
    assert np.all(masks[:, 27:] == 0.0)


def test_forced_option_mask_gets_zero_weight_shadow_action() -> None:
    environment = np.ones((3, 29), dtype=np.float32)
    environment[1, :] = 0.0
    environment[1, 27] = 1.0
    masks = policy_action_masks(environment, 27, 28, neutral_action=13)
    assert masks[1, 13] == 1.0
    assert masks[1].sum() == 1.0
    assert masks[1, 27] == 0.0
