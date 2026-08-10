"""Auditable hybrid action distribution for TLI2 (not wired into training yet)."""

from __future__ import annotations

import torch
from torch import nn
from torch.distributions import Bernoulli, Normal


class TanhGaussianBernoulli:
    """Two bounded continuous commands plus one Bernoulli commit action.

    The environment action is the tanh-transformed command.  ``log_prob``
    evaluates that exact bounded action by applying the inverse tanh and the
    change-of-variables Jacobian; it therefore cannot silently score a clipped
    Gaussian sample under a different density.
    """

    def __init__(self, mean: torch.Tensor, log_std: torch.Tensor, commit_logits: torch.Tensor):
        if mean.shape[-1] != 2 or log_std.shape != mean.shape or commit_logits.shape != mean.shape[:-1]:
            raise ValueError("expected mean/log_std [...,2] and commit_logits [...]")
        self.mean = mean
        self.log_std = log_std.clamp(-8.0, 2.0)
        self.normal = Normal(self.mean, self.log_std.exp())
        self.commit = Bernoulli(logits=commit_logits)

    def sample(self, deterministic: bool = False) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        latent = self.mean if deterministic else self.normal.rsample()
        continuous = torch.tanh(latent)
        commit = (torch.sigmoid(self.commit.logits) >= 0.5).to(dtype=continuous.dtype) if deterministic else self.commit.sample()
        return continuous, commit, self.log_prob(continuous, commit)

    def log_prob(self, continuous: torch.Tensor, commit: torch.Tensor) -> torch.Tensor:
        bounded = continuous.clamp(-1.0 + 1e-6, 1.0 - 1e-6)
        latent = 0.5 * (torch.log1p(bounded) - torch.log1p(-bounded))
        correction = torch.log(1.0 - bounded.square() + 1e-6)
        continuous_lp = (self.normal.log_prob(latent) - correction).sum(dim=-1)
        commit_lp = self.commit.log_prob(commit)
        if commit_lp.ndim > continuous_lp.ndim:
            commit_lp = commit_lp.sum(dim=-1)
        return continuous_lp + commit_lp

    def entropy(self) -> torch.Tensor:
        # This is the standard tractable pre-squash proxy; PPO may use it as
        # an exploration diagnostic without altering the exact log-prob ratio.
        return self.normal.entropy().sum(dim=-1) + self.commit.entropy()


class HybridActionHead(nn.Module):
    """Feature-to-distribution head; integration with RIGMAPPO is deferred."""

    def __init__(self, input_dim: int, hidden_dim: int = 128):
        super().__init__()
        self.backbone = nn.Sequential(nn.Linear(input_dim, hidden_dim), nn.Tanh())
        self.mean = nn.Linear(hidden_dim, 2)
        self.log_std = nn.Linear(hidden_dim, 2)
        self.commit = nn.Linear(hidden_dim, 1)

    def distribution(self, features: torch.Tensor) -> TanhGaussianBernoulli:
        hidden = self.backbone(features)
        return TanhGaussianBernoulli(self.mean(hidden), self.log_std(hidden), self.commit(hidden).squeeze(-1))
