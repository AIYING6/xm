"""Frozen P1F losses for capacity-matched commitment-policy training."""

from __future__ import annotations

import torch
from torch.distributions import Categorical


def target_probability_interval(
    reliability_prior: torch.Tensor,
    radius: float = 0.05,
) -> torch.Tensor:
    if radius <= 0.0 or radius >= 0.5:
        raise ValueError("calibration radius must be in (0, 0.5)")
    prior = reliability_prior.to(dtype=torch.float32)
    if torch.any(prior < 0.0) or torch.any(prior > 1.0):
        raise ValueError("reliability prior must lie in [0, 1]")
    return torch.stack(
        (torch.clamp(prior - radius, 0.0, 1.0), torch.clamp(prior + radius, 0.0, 1.0)),
        dim=-1,
    )


def interval_calibration_loss(
    predicted_interval: torch.Tensor,
    reliability_prior: torch.Tensor,
    radius: float = 0.05,
) -> torch.Tensor:
    """Calibrate against the public reliability context, never delivery truth."""

    target = target_probability_interval(reliability_prior, radius)
    return torch.mean((predicted_interval - target) ** 2)


def ppo_mode_policy_loss(
    mode_logits: torch.Tensor,
    actions: torch.Tensor,
    old_log_prob: torch.Tensor,
    advantages: torch.Tensor,
    clip_epsilon: float = 0.2,
) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
    if clip_epsilon <= 0.0:
        raise ValueError("clip_epsilon must be positive")
    distribution = Categorical(logits=mode_logits)
    new_log_prob = distribution.log_prob(actions)
    ratio = torch.exp(new_log_prob - old_log_prob)
    unclipped = ratio * advantages
    clipped = torch.clamp(ratio, 1.0 - clip_epsilon, 1.0 + clip_epsilon) * advantages
    policy_loss = -torch.mean(torch.minimum(unclipped, clipped))
    return policy_loss, {
        "new_log_prob": new_log_prob,
        "ratio": ratio,
        "entropy": distribution.entropy().mean(),
    }


def commitment_actor_loss(
    output: dict[str, torch.Tensor],
    actions: torch.Tensor,
    old_log_prob: torch.Tensor,
    advantages: torch.Tensor,
    reliability_prior: torch.Tensor,
    calibration_weight: float = 0.10,
    calibration_radius: float = 0.05,
    clip_epsilon: float = 0.2,
) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
    """Identical PPO and calibration contract for candidate and direct baseline."""

    if calibration_weight < 0.0:
        raise ValueError("calibration_weight must be non-negative")
    policy_loss, telemetry = ppo_mode_policy_loss(
        output["mode_logits"], actions, old_log_prob, advantages, clip_epsilon
    )
    calibration = interval_calibration_loss(
        output["interval"], reliability_prior, calibration_radius
    )
    total = policy_loss + calibration_weight * calibration
    telemetry.update(
        {
            "policy_loss": policy_loss,
            "calibration_loss": calibration,
            "total_actor_loss": total,
        }
    )
    return total, telemetry
