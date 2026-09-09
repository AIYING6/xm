"""Capacity-controlled recurrent policy components for P3 commitment pilots."""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import nn
from torch.distributions import Categorical, Normal


@dataclass(frozen=True)
class P3PolicyConfig:
    observation_dim: int = 45
    actor_hidden_dim: int = 64
    critic_input_dim: int = 135
    critic_hidden_dim: int = 128
    guidance_log_std_initial: float = -0.7


class P3RecurrentActor(nn.Module):
    """Shared decentralized actor with categorical mode and Gaussian guidance heads."""

    def __init__(self, config: P3PolicyConfig) -> None:
        super().__init__()
        self.config = config
        self.encoder = nn.Sequential(
            nn.Linear(config.observation_dim, config.actor_hidden_dim),
            nn.Tanh(),
        )
        self.gru = nn.GRU(config.actor_hidden_dim, config.actor_hidden_dim, batch_first=True)
        self.mode_head = nn.Linear(config.actor_hidden_dim, 3)
        self.guidance_head = nn.Linear(config.actor_hidden_dim, 2)
        self.guidance_log_std = nn.Parameter(
            torch.full((2,), float(config.guidance_log_std_initial))
        )

    def forward(self, observations: torch.Tensor, hidden: torch.Tensor | None = None):
        if observations.ndim != 3 or observations.shape[-1] != self.config.observation_dim:
            raise ValueError("observations must have shape [batch, time, observation_dim]")
        encoded = self.encoder(observations)
        features, next_hidden = self.gru(encoded, hidden)
        guidance_mean = self.guidance_head(features)
        return {
            "mode_logits": self.mode_head(features),
            "guidance_mean": torch.tanh(guidance_mean),
            "guidance_log_std": self.guidance_log_std.expand_as(guidance_mean),
            "hidden": next_hidden,
        }

    def distributions(self, output: dict[str, torch.Tensor]):
        mode = Categorical(logits=output["mode_logits"])
        guidance = Normal(output["guidance_mean"], output["guidance_log_std"].exp())
        return mode, guidance


class P3CentralCritic(nn.Module):
    """Central value function over the union of legal local observations."""

    def __init__(self, config: P3PolicyConfig) -> None:
        super().__init__()
        self.config = config
        self.network = nn.Sequential(
            nn.Linear(config.critic_input_dim, config.critic_hidden_dim),
            nn.Tanh(),
            nn.Linear(config.critic_hidden_dim, config.critic_hidden_dim),
            nn.Tanh(),
            nn.Linear(config.critic_hidden_dim, 1),
        )

    def forward(self, shared_observations: torch.Tensor) -> torch.Tensor:
        if shared_observations.shape[-1] != self.config.critic_input_dim:
            raise ValueError("critic input dimension mismatch")
        return self.network(shared_observations).squeeze(-1)


def parameter_count(module: nn.Module) -> int:
    return sum(parameter.numel() for parameter in module.parameters())
