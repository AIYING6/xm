import torch

from algorithms.acfid_fixed_endpoint_evaluator import EvaluationCase, evaluate_fixed_endpoint
from algorithms.acfid_recovery_policy import ACFIDRecoveryPolicy


def test_evaluator_is_deterministic_and_read_only():
    torch.manual_seed(9); model = ACFIDRecoveryPolicy(7, 5, 3)
    cases = [EvaluationCase(1, 2, frozenset(("sense_0", "relay_1"))), EvaluationCase(3, 4, frozenset(("sense_1", "relay_0", "act_1")))]
    before = [p.detach().clone() for p in model.parameters()]
    first = evaluate_fixed_endpoint(model, cases); second = evaluate_fixed_endpoint(model, cases)
    assert first == second
    assert all(torch.equal(old, new) for old, new in zip(before, model.parameters()))
    assert all(row["action_regret"] >= -1e-10 for row in first)
