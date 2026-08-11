"""Shape/gradient smoke for the minimal v1.6R vanilla actor."""
from __future__ import annotations

import torch

from algorithms.mappo.continuous_guidance_policy import ContinuousGuidanceActor


def main() -> int:
    torch.manual_seed(17065)
    actor = ContinuousGuidanceActor(obs_dim=34, hidden_dim=32)
    obs = torch.randn(6, 34)
    action, logp = actor(obs)
    deterministic, deterministic_logp = actor(obs, deterministic=True)
    loss = -(logp.mean() + deterministic_logp.mean())
    loss.backward()
    failures = []
    if action.shape != (6, 2) or deterministic.shape != (6, 2):
        failures.append("action shape mismatch")
    if not torch.isfinite(action).all() or not torch.isfinite(logp).all():
        failures.append("stochastic output non-finite")
    if not torch.isfinite(deterministic).all() or not torch.isfinite(deterministic_logp).all():
        failures.append("deterministic output non-finite")
    if any(p.grad is None or not torch.isfinite(p.grad).all() for p in actor.parameters()):
        failures.append("actor gradient missing/non-finite")
    print(f"checks=4, failed={len(failures)}")
    for failure in failures:
        print(f"FAIL: {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
