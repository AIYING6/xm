"""Synthetic one-update PPO regression for v1.6R."""
from __future__ import annotations

import numpy as np
import torch

from algorithms.mappo.continuous_guidance_policy import ContinuousGuidanceActor
from algorithms.mappo.v16r_ppo import CentralizedValueCritic, V16RPPOConfig, ppo_update


def main() -> int:
    torch.manual_seed(17068)
    t, n, obs_dim, share_dim = 6, 3, 34, 38
    actor = ContinuousGuidanceActor(obs_dim, hidden_dim=32)
    critic = CentralizedValueCritic(share_dim, hidden_dim=32)
    with torch.no_grad():
        obs = torch.randn(t, n, obs_dim)
        actions, logp = actor(obs.reshape(t * n, obs_dim))
        actions = actions.reshape(t, n, 2)
        logp = logp.reshape(t, n)
    batch = {
        "obs": obs.numpy(), "share_obs": torch.randn(t, n, share_dim).numpy(),
        "actions": actions.numpy(), "logp": logp.numpy(),
        "rewards": torch.randn(t, n, 1).numpy(), "dones": np.zeros((t, n), dtype=np.float32),
        "next_share_obs": torch.randn(n, share_dim).numpy(),
    }
    metrics = ppo_update(actor, critic, batch, V16RPPOConfig(epochs=1))
    failures = []
    if not metrics or any(not np.isfinite(v) for v in metrics.values()):
        failures.append("PPO metrics non-finite")
    if abs(metrics["ratio_mean"] - 1.0) > 1e-4:
        failures.append("old-policy ratio is not initially one")
    if metrics["actor_grad_norm"] <= 0.0 or metrics["actor_param_delta"] <= 0.0:
        failures.append("actor received no gradient/update")
    print(f"checks=3, failed={len(failures)}")
    for failure in failures:
        print(f"FAIL: {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
