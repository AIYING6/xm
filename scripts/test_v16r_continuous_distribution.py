"""Numerical R1 tests for bounded guidance PPO log-probability."""
from __future__ import annotations

import torch

from algorithms.mappo.continuous_guidance_distribution import TanhGaussianGuidance


def main() -> int:
    torch.manual_seed(17064)
    mean = torch.zeros(8, 2, requires_grad=True)
    log_std = torch.full((8, 2), -0.3, requires_grad=True)
    dist = TanhGaussianGuidance(mean, log_std)
    action, old_logp = dist.sample()
    new_logp = dist.log_prob(action)
    loss = -(new_logp.mean())
    loss.backward()
    failures = []
    if not torch.isfinite(action).all() or not torch.isfinite(old_logp).all():
        failures.append("sample/log_prob non-finite")
    if not torch.allclose(old_logp.detach(), new_logp.detach(), atol=2e-5, rtol=2e-5):
        failures.append("sampled action and recomputed log_prob disagree")
    if mean.grad is None or log_std.grad is None or not torch.isfinite(mean.grad).all() or not torch.isfinite(log_std.grad).all():
        failures.append("gradient is missing or non-finite")
    deterministic = dist.deterministic()
    if not torch.all((deterministic > -1.0) & (deterministic < 1.0)):
        failures.append("deterministic action out of bounds")
    print(f"checks=4, failed={len(failures)}")
    for failure in failures:
        print(f"FAIL: {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
