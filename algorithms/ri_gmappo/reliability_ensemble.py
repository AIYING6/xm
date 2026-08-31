"""Default-off categorical policy pooling for a future Reliable-DRTP study.

The functions here are deliberately interface-only: they load no checkpoint,
create no environment, and do not know about training or evaluation tapes.
They are not wired into any historical or Mainline-A execution path.
"""
from __future__ import annotations

from collections.abc import Sequence

import torch


def uniform_probability_pool(member_logits: Sequence[torch.Tensor]) -> torch.Tensor:
    """Pool same-shaped categorical logits into a valid probability simplex."""
    if not member_logits:
        raise ValueError("at least one ensemble member is required")
    reference_shape = member_logits[0].shape
    if not reference_shape or reference_shape[-1] < 2:
        raise ValueError("member logits must have a categorical action dimension")
    if any(logits.shape != reference_shape for logits in member_logits):
        raise ValueError("all ensemble members must produce the same logits shape")
    if any(not torch.isfinite(logits).all() for logits in member_logits):
        raise ValueError("member logits must be finite")
    probabilities = torch.stack(
        [torch.softmax(logits, dim=-1) for logits in member_logits], dim=0
    ).mean(dim=0)
    if not torch.allclose(
        probabilities.sum(dim=-1), torch.ones_like(probabilities[..., 0]), atol=1e-6
    ):
        raise RuntimeError("pooled probabilities are not normalized")
    return probabilities


def pooled_categorical_action(
    member_logits: Sequence[torch.Tensor],
    *,
    deterministic: bool,
    generator: torch.Generator | None = None,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Return one action source after pooling, never one sample per member."""
    probabilities = uniform_probability_pool(member_logits)
    if deterministic:
        return torch.argmax(probabilities, dim=-1), probabilities
    flattened = probabilities.reshape(-1, probabilities.shape[-1])
    action = torch.multinomial(flattened, num_samples=1, generator=generator)
    return action.reshape(probabilities.shape[:-1]), probabilities
