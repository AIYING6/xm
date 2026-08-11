"""Bounded continuous guidance distribution for v1.6R PPO."""
from __future__ import annotations

import torch
from torch import Tensor


class TanhGaussianGuidance:
    """Tanh-squashed diagonal Gaussian with the exact Jacobian correction."""

    def __init__(self, mean: Tensor, log_std: Tensor, eps: float = 1e-6):
        if mean.shape != log_std.shape or mean.shape[-1] != 2:
            raise ValueError("mean/log_std must have matching [..., 2] shape")
        self.mean = mean
        self.log_std = log_std
        self.eps = eps
        self.normal = torch.distributions.Normal(mean, log_std.exp())

    def sample(self) -> tuple[Tensor, Tensor]:
        pre_tanh = self.normal.rsample()
        action = torch.tanh(pre_tanh)
        return action, self.log_prob(action, pre_tanh=pre_tanh)

    def deterministic(self) -> Tensor:
        return torch.tanh(self.mean)

    def log_prob(self, action: Tensor, pre_tanh: Tensor | None = None) -> Tensor:
        action = action.clamp(-1.0 + self.eps, 1.0 - self.eps)
        if pre_tanh is None:
            pre_tanh = torch.atanh(action)
        correction = torch.log(1.0 - action.square() + self.eps)
        return (self.normal.log_prob(pre_tanh) - correction).sum(dim=-1)

    def entropy_proxy(self) -> Tensor:
        return self.normal.entropy().sum(dim=-1)

