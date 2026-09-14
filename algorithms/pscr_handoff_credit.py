"""Task-feasible coalition counterfactual utilities for PSCR experiments.

This module contains only the mathematical helper for the MFHC-MAPPO
candidate. It does not alter an environment, actor interface, reward, or
training runner. Formal use requires an audited state-conditioned feasible
coalition/action set and a critic that evaluates those joint alternatives.
"""
from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import Tensor


@dataclass(frozen=True)
class CoalitionAdvantage:
    """Selected joint-action value and its feasible counterfactual baseline."""

    selected_value: Tensor
    baseline: Tensor
    advantage: Tensor


def minimal_feasible_handoff_coalitions(
    current_actions: Tensor,
    candidate_joint_actions: Tensor,
    destination_feasible: Tensor,
) -> tuple[tuple[int, ...], ...]:
    """Return every smallest set of agents needed for a feasible handoff.

    ``candidate_joint_actions`` must contain complete joint macro-action
    alternatives that the task/environment auditor has already verified
    create one of the publicly available destination service chains. The
    candidate set must be constructed independently of the sampled coalition
    action and must not be filtered by its sampled destination label. An
    agent belongs to a candidate's
    intervention set iff its macro action differs from ``current_actions``.
    All tied minimum-cardinality sets are returned in deterministic lexicographic
    order so callers can sample among them reproducibly.
    """
    if current_actions.ndim != 1:
        raise ValueError("current_actions must have shape [agents]")
    if candidate_joint_actions.ndim != 2 or candidate_joint_actions.shape[1] != current_actions.numel():
        raise ValueError("candidate_joint_actions must have shape [candidates, agents]")
    if destination_feasible.shape != (candidate_joint_actions.shape[0],):
        raise ValueError("destination_feasible must have shape [candidates]")
    if destination_feasible.dtype != torch.bool:
        destination_feasible = destination_feasible.to(torch.bool)
    if not destination_feasible.any():
        return ()

    required_sets = {
        tuple(torch.nonzero(candidate != current_actions, as_tuple=False).flatten().tolist())
        for candidate in candidate_joint_actions[destination_feasible]
    }
    min_size = min(map(len, required_sets))
    minimal = tuple(sorted(required for required in required_sets if len(required) == min_size))
    if not minimal or minimal[0] == ():
        # A destination already feasible with no action change is not a
        # learned handoff decision and should not activate the credit term.
        return ()
    return minimal


def feasible_coalition_advantage(
    q_values: Tensor,
    coalition_probs: Tensor,
    feasible_mask: Tensor,
    selected_index: Tensor,
) -> CoalitionAdvantage:
    """Compute a masked, policy-weighted counterfactual baseline.

    Args:
        q_values: Critic values for coalition alternatives, shape ``[B, K]``.
            Each column must represent a joint alternative for the *same*
            state and fixed non-coalition actions.
        coalition_probs: Product-policy probabilities over those alternatives,
            shape ``[B, K]``. These are detached inside the baseline so this
            helper does not introduce a pathwise actor gradient.
        feasible_mask: Boolean/0-1 mask, shape ``[B, K]``, generated from the
            frozen task constraints without exposing oracle labels to actors.
        selected_index: Selected alternative index, shape ``[B]``.

    The baseline is conditioned on the state, the fixed actions outside the
    coalition, and the feasible alternative set. It must not be constructed
    using a coalition selected as a function of the sampled coalition action;
    such action-dependent routing would invalidate the baseline property.
    """
    if q_values.ndim != 2:
        raise ValueError("q_values must have shape [batch, alternatives]")
    if coalition_probs.shape != q_values.shape or feasible_mask.shape != q_values.shape:
        raise ValueError("probabilities and feasible mask must match q_values")
    if selected_index.shape != (q_values.shape[0],):
        raise ValueError("selected_index must have shape [batch]")
    if not torch.isfinite(q_values).all():
        raise ValueError("q_values must be finite")
    if not torch.isfinite(coalition_probs).all() or (coalition_probs < 0).any():
        raise ValueError("coalition_probs must be finite and non-negative")

    feasible = feasible_mask.to(dtype=torch.bool)
    if not feasible.any(dim=-1).all():
        raise ValueError("each row must contain at least one feasible alternative")
    if (selected_index < 0).any() or (selected_index >= q_values.shape[1]).any():
        raise ValueError("selected alternative index is out of range")
    selected_feasible = feasible.gather(1, selected_index.long().unsqueeze(1)).squeeze(1)
    if not selected_feasible.all():
        raise ValueError("sampled coalition alternative must be feasible")

    weights = coalition_probs.detach() * feasible.to(q_values.dtype)
    weight_sum = weights.sum(dim=-1)
    if (weight_sum <= 0).any():
        raise ValueError("policy assigns zero probability to all feasible alternatives")
    baseline = (weights * q_values).sum(dim=-1) / weight_sum
    selected_value = q_values.gather(1, selected_index.long().unsqueeze(1)).squeeze(1)
    advantage = selected_value - baseline
    return CoalitionAdvantage(selected_value, baseline, advantage)


def coalition_score_function_loss(joint_log_prob: Tensor, advantage: Tensor) -> Tensor:
    """Score-function loss for the product policy of one selected coalition.

    ``joint_log_prob`` is the sum of member log-probabilities for the sampled
    coalition action. The caller must apply this term only on registered
    handoff decision states and use ordinary MAPPO advantages elsewhere.
    """
    if joint_log_prob.shape != advantage.shape:
        raise ValueError("joint_log_prob and advantage must have identical shape")
    if not torch.isfinite(joint_log_prob).all() or not torch.isfinite(advantage).all():
        raise ValueError("joint log-probabilities and advantages must be finite")
    return -(joint_log_prob * advantage.detach()).mean()
