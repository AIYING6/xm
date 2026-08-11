"""Tiny no-claim B0/B2 one-update development smoke."""
from __future__ import annotations

import numpy as np
import torch

from algorithms.mappo.continuous_guidance_policy import ContinuousGuidanceActor
from algorithms.mappo.recipient_graph_guidance_policy import RecipientGraphGuidanceActor
from algorithms.mappo.v16r_ppo import CentralizedValueCritic, V16RPPOConfig, ppo_update
from algorithms.mappo.v16r_rollout import collect_v16r_rollout
from envs.uav_intercept_3d_env import UAVIntercept3DConfig
from envs.v16r_env_adapter import V16RIntercept3DEnv


def run_one(seed: int, graph_conditioned: bool) -> dict[str, float]:
    env = V16RIntercept3DEnv(UAVIntercept3DConfig(seed=seed, max_steps=8))
    actor = (RecipientGraphGuidanceActor(env.obs_dim, hidden_dim=32) if graph_conditioned else ContinuousGuidanceActor(env.obs_dim, hidden_dim=32))
    critic = CentralizedValueCritic(env.share_obs_dim, hidden_dim=32)
    batch = collect_v16r_rollout(env, actor, horizon=4, graph_conditioned=graph_conditioned)
    return ppo_update(actor, critic, batch, V16RPPOConfig(epochs=1), graph_conditioned=graph_conditioned)


def main() -> int:
    torch.manual_seed(17070)
    failures = []
    for graph_conditioned in (False, True):
        metrics = run_one(17070 + int(graph_conditioned), graph_conditioned)
        if not metrics or any(not np.isfinite(v) for v in metrics.values()):
            failures.append("B2" if graph_conditioned else "B0")
    print(f"checks=2, failed={len(failures)}")
    for failure in failures:
        print(f"FAIL: {failure} update")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
