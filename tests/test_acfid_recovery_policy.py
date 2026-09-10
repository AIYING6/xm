from __future__ import annotations

import torch

from algorithms.acfid_recovery_policy import ACFIDRecoveryPolicy, AdditiveRecoveryPolicy, DirectFaultAwareRecoveryPolicy, parameter_count


def sample():
    torch.manual_seed(11)
    context = torch.randn(4, 7); faults = torch.randn(4, 6, 5); active = torch.tensor([[1,1,0,0,0,0],[0,1,0,1,0,0],[1,0,1,0,1,0],[1,1,1,0,0,0]], dtype=torch.float32)
    relations = torch.randn(4, 6, 6, 3)
    relations = (relations + relations.transpose(1, 2)) / 2
    return context, faults, active, relations


def test_acfid_is_invariant_to_fault_registry_permutation() -> None:
    model = ACFIDRecoveryPolicy(7, 5, 3); context, faults, active, relations = sample()
    permutation = torch.tensor([3, 0, 5, 1, 4, 2])
    expected = model(context, faults, active, relations)
    actual = model(context, faults[:, permutation], active[:, permutation], relations[:, permutation][:, :, permutation])
    assert torch.allclose(expected, actual, atol=1e-6)


def test_interaction_head_is_inactive_for_zero_or_one_fault() -> None:
    model = ACFIDRecoveryPolicy(7, 5, 3); additive = AdditiveRecoveryPolicy(7, 5)
    additive.load_state_dict({key: value for key, value in model.state_dict().items() if not key.startswith("interaction")})
    context, faults, _, relations = sample(); active = torch.zeros(4, 6); active[:, 2] = 1
    assert torch.allclose(model(context, faults, active, relations), additive(context, faults, active), atol=1e-6)


def test_all_pilot_policies_emit_same_action_shape() -> None:
    context, faults, active, relations = sample()
    models = [DirectFaultAwareRecoveryPolicy(7, 5), AdditiveRecoveryPolicy(7, 5), ACFIDRecoveryPolicy(7, 5, 3)]
    assert all(model(context, faults, active, relations).shape == (4, 5) for model in models)
    assert all(parameter_count(model) > 0 for model in models)


def test_frozen_pilot_capacities_match_within_one_percent() -> None:
    models = [DirectFaultAwareRecoveryPolicy(7, 5, hidden=100), AdditiveRecoveryPolicy(7, 5, hidden=81), ACFIDRecoveryPolicy(7, 5, 3, hidden=64)]
    counts = [parameter_count(model) for model in models]
    assert max(counts) / min(counts) - 1.0 < 0.011
