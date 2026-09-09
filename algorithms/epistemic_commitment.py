"""Zero-training implementation kernel for epistemic commitment decisions.

The module contains no environment truth input and no communication recovery
mechanism.  It maps a legal local history to an uncertainty interval and makes
a robust task-mode decision over that information set.  Integration with PPO
is intentionally deferred until the implementation audits pass.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import nn


MODE_COMMIT = 0
MODE_DEFER = 1
MODE_FALLBACK = 2
MODE_NAMES = ("commit", "defer", "fallback")


def probability_interval(interval_logits: torch.Tensor) -> torch.Tensor:
    """Convert two unconstrained values into a valid interval in ``[0, 1]``."""

    if interval_logits.shape[-1] != 2:
        raise ValueError("interval_logits must have final dimension 2")
    midpoint = torch.sigmoid(interval_logits[..., 0])
    max_radius = torch.minimum(midpoint, 1.0 - midpoint)
    radius = torch.sigmoid(interval_logits[..., 1]) * max_radius
    return torch.stack((midpoint - radius, midpoint + radius), dim=-1)


def robust_mode_values(endpoint_values: torch.Tensor, interval: torch.Tensor) -> torch.Tensor:
    """Worst-case affine value of each mode over a probability interval.

    ``endpoint_values[..., mode, 0]`` and ``[..., mode, 1]`` are the values
    conditioned on incompatible and compatible teammate commitment states.
    No realized state is consumed.  The minimum of an affine function over an
    interval occurs at one of its endpoints.
    """

    if endpoint_values.shape[-2:] != (3, 2):
        raise ValueError("endpoint_values must end in shape (3, 2)")
    if interval.shape[-1] != 2:
        raise ValueError("interval must end in shape (2,)")
    if torch.any(interval[..., 0] < 0.0) or torch.any(interval[..., 1] > 1.0):
        raise ValueError("probability interval must lie in [0, 1]")
    if torch.any(interval[..., 0] > interval[..., 1]):
        raise ValueError("probability interval lower bound exceeds upper bound")
    low = interval[..., 0].unsqueeze(-1)
    high = interval[..., 1].unsqueeze(-1)
    incompatible = endpoint_values[..., :, 0]
    compatible = endpoint_values[..., :, 1]
    low_value = incompatible + low * (compatible - incompatible)
    high_value = incompatible + high * (compatible - incompatible)
    return torch.minimum(low_value, high_value)


def select_robust_mode(endpoint_values: torch.Tensor, interval: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    values = robust_mode_values(endpoint_values, interval)
    return torch.argmax(values, dim=-1), values


def smooth_robust_mode_values(
    endpoint_values: torch.Tensor,
    interval: torch.Tensor,
    temperature: float,
) -> torch.Tensor:
    """Differentiable conservative value used as policy logits during training."""

    if temperature <= 0.0:
        raise ValueError("soft minimum temperature must be positive")
    low = interval[..., 0].unsqueeze(-1)
    high = interval[..., 1].unsqueeze(-1)
    incompatible = endpoint_values[..., :, 0]
    compatible = endpoint_values[..., :, 1]
    low_value = incompatible + low * (compatible - incompatible)
    high_value = incompatible + high * (compatible - incompatible)
    candidates = torch.stack((low_value, high_value), dim=-1)
    return -temperature * torch.logsumexp(-candidates / temperature, dim=-1)


@dataclass(frozen=True)
class CommitmentActorConfig:
    input_dim: int
    hidden_dim: int = 64
    robust_softmin_temperature: float = 0.10


class _HistoryBackbone(nn.Module):
    def __init__(self, config: CommitmentActorConfig) -> None:
        super().__init__()
        self.config = config
        self.history = nn.GRU(config.input_dim, config.hidden_dim, batch_first=True)

    def encode(self, local_history: torch.Tensor, hidden: torch.Tensor | None = None) -> tuple[torch.Tensor, torch.Tensor]:
        if local_history.ndim != 3 or local_history.shape[-1] != self.config.input_dim:
            raise ValueError("local_history must have shape (batch, time, input_dim)")
        encoded, next_hidden = self.history(local_history, hidden)
        return encoded[:, -1], next_hidden


class InformationSetCommitmentActor(_HistoryBackbone):
    """Candidate actor whose task mode is selected by robust interval value."""

    def __init__(self, config: CommitmentActorConfig) -> None:
        super().__init__(config)
        self.interval_head = nn.Linear(config.hidden_dim, 2)
        self.endpoint_value_head = nn.Linear(config.hidden_dim, 6)

    def forward(self, local_history: torch.Tensor, hidden: torch.Tensor | None = None) -> dict[str, torch.Tensor]:
        encoded, next_hidden = self.encode(local_history, hidden)
        interval_logits = self.interval_head(encoded)
        interval = probability_interval(interval_logits)
        endpoint_values = self.endpoint_value_head(encoded).reshape(-1, 3, 2)
        mode_values = smooth_robust_mode_values(
            endpoint_values,
            interval,
            self.config.robust_softmin_temperature,
        )
        return {
            "interval_logits": interval_logits,
            "interval": interval,
            "endpoint_values": endpoint_values,
            "mode_values": mode_values,
            "mode_logits": mode_values,
            "mode": torch.argmax(mode_values, dim=-1),
            "hidden": next_hidden,
        }


class CapacityMatchedRecurrentActor(_HistoryBackbone):
    """Direct recurrent mode policy with the same active head capacity."""

    def __init__(self, config: CommitmentActorConfig) -> None:
        super().__init__(config)
        self.mode_head = nn.Linear(config.hidden_dim, 8)
        # Fixed dense projection: every output of the matched 8-unit head
        # contributes to at least one direct mode logit and receives gradient.
        self.register_buffer(
            "mode_projection",
            torch.tensor(
                [
                    [1.0, 0.0, 0.0, 0.5, -0.5, 0.25, 0.0, 0.25],
                    [0.0, 1.0, 0.0, -0.25, 0.5, 0.0, 0.25, 0.25],
                    [0.0, 0.0, 1.0, 0.25, 0.0, 0.5, -0.5, 0.25],
                ],
                dtype=torch.float32,
            ),
        )

    def forward(self, local_history: torch.Tensor, hidden: torch.Tensor | None = None) -> dict[str, torch.Tensor]:
        encoded, next_hidden = self.encode(local_history, hidden)
        direct_features = self.mode_head(encoded)
        mode_logits = direct_features @ self.mode_projection.transpose(0, 1)
        interval_logits = direct_features[..., :2]
        return {
            "interval_logits": interval_logits,
            "interval": probability_interval(interval_logits),
            "mode_logits": mode_logits,
            "direct_features": direct_features,
            "mode": torch.argmax(mode_logits, dim=-1),
            "hidden": next_hidden,
        }


def parameter_count(module: nn.Module) -> int:
    return sum(parameter.numel() for parameter in module.parameters())
