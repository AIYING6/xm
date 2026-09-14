from __future__ import annotations

import sys
from pathlib import Path

import pytest
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from algorithms.pscr_handoff_credit import (
    coalition_score_function_loss,
    feasible_coalition_advantage,
    minimal_feasible_handoff_coalitions,
)


def test_feasible_counterfactual_baseline_matches_masked_policy_expectation() -> None:
    q = torch.tensor([[2.0, 10.0, 6.0], [1.0, 3.0, 9.0]])
    probs = torch.tensor([[0.2, 0.5, 0.3], [0.25, 0.25, 0.5]])
    feasible = torch.tensor([[1, 0, 1], [0, 1, 1]], dtype=torch.bool)
    chosen = torch.tensor([2, 1])

    out = feasible_coalition_advantage(q, probs, feasible, chosen)

    expected_baseline = torch.tensor([4.4, 7.0])
    torch.testing.assert_close(out.baseline, expected_baseline)
    torch.testing.assert_close(out.selected_value, torch.tensor([6.0, 3.0]))
    torch.testing.assert_close(out.advantage, torch.tensor([1.6, -4.0]))


def test_infeasible_selected_action_is_rejected() -> None:
    with pytest.raises(ValueError, match="must be feasible"):
        feasible_coalition_advantage(
            torch.tensor([[1.0, 2.0]]),
            torch.tensor([[0.5, 0.5]]),
            torch.tensor([[1, 0]]),
            torch.tensor([1]),
        )


def test_all_zero_feasible_policy_mass_is_rejected() -> None:
    with pytest.raises(ValueError, match="zero probability"):
        feasible_coalition_advantage(
            torch.tensor([[1.0, 2.0]]),
            torch.tensor([[1.0, 0.0]]),
            torch.tensor([[0, 1]]),
            torch.tensor([1]),
        )


def test_coalition_score_function_backpropagates_only_through_log_probability() -> None:
    log_prob = torch.tensor([-0.8, -1.2], requires_grad=True)
    advantage = torch.tensor([2.0, -1.0], requires_grad=True)
    loss = coalition_score_function_loss(log_prob, advantage)
    loss.backward()

    torch.testing.assert_close(log_prob.grad, torch.tensor([-1.0, 0.5]))
    assert advantage.grad is None


def test_minimal_feasible_handoff_coalitions_preserve_ties() -> None:
    current = torch.tensor([0, 0, 0])
    candidates = torch.tensor([
        [1, 1, 0],  # two-agent feasible handoff
        [1, 0, 1],  # tied two-agent feasible handoff
        [1, 1, 1],  # feasible but non-minimal
        [0, 1, 0],  # not a feasible destination chain
    ])
    feasible = torch.tensor([True, True, True, False])

    coalitions = minimal_feasible_handoff_coalitions(current, candidates, feasible)
    assert coalitions == ((0, 1), (0, 2))


def test_minimal_handoff_is_empty_when_no_destination_profile_is_feasible() -> None:
    coalitions = minimal_feasible_handoff_coalitions(
        torch.tensor([0, 0, 0]),
        torch.tensor([[1, 1, 1], [1, 0, 1]]),
        torch.tensor([False, False]),
    )
    assert coalitions == ()


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
