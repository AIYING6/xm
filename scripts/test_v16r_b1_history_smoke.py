"""No-training B1 legal-history baseline smoke."""
from __future__ import annotations

import numpy as np
import torch

from algorithms.mappo.continuous_guidance_policy import ContinuousGuidanceActor
from algorithms.mappo.v16r_ppo import CentralizedValueCritic, V16RPPOConfig, ppo_update
from algorithms.mappo.v16r_rollout import collect_v16r_rollout
from envs.uav_intercept_3d_env import UAVIntercept3DConfig
from envs.v16r_env_adapter import V16RIntercept3DEnv


def main() -> int:
    torch.manual_seed(17072)
    env = V16RIntercept3DEnv(UAVIntercept3DConfig(seed=17072, max_steps=8, v16r_mission_mode=True))
    history_len = 4
    actor = ContinuousGuidanceActor(env.obs_dim * history_len, hidden_dim=32)
    critic = CentralizedValueCritic(env.share_obs_dim, hidden_dim=32)
    batch = collect_v16r_rollout(env, actor, horizon=4, history_len=history_len)
    metrics = ppo_update(actor, critic, batch, V16RPPOConfig(epochs=1))
    failures = []
    if batch["obs"].shape[-1] != env.obs_dim * history_len:
        failures.append("history width mismatch")
    if not metrics or any(not np.isfinite(v) for v in metrics.values()):
        failures.append("B1 PPO update non-finite")
    print(f"checks=2, failed={len(failures)}")
    for failure in failures:
        print(f"FAIL: {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
