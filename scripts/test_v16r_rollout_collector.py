"""No-update collector and PPO old-log-prob consistency smoke."""
from __future__ import annotations

import numpy as np
import torch

from algorithms.mappo.continuous_guidance_policy import ContinuousGuidanceActor
from algorithms.mappo.v16r_rollout import collect_v16r_rollout
from envs.uav_intercept_3d_env import UAVIntercept3DConfig
from envs.v16r_env_adapter import V16RIntercept3DEnv


def main() -> int:
    torch.manual_seed(17067)
    env = V16RIntercept3DEnv(UAVIntercept3DConfig(seed=17067, max_steps=5, v16r_mission_mode=True))
    actor = ContinuousGuidanceActor(env.obs_dim, hidden_dim=32)
    batch = collect_v16r_rollout(env, actor, horizon=7)
    failures: list[str] = []
    if batch["obs"].shape != (7, env.num_agents, env.obs_dim):
        failures.append("obs batch shape mismatch")
    if batch["node"].shape[1] != env.num_agents:
        failures.append("recipient graph dimension missing")
    if batch["next_obs"].shape != (env.num_agents, env.obs_dim):
        failures.append("next_obs shape mismatch")
    history_batch = collect_v16r_rollout(env, ContinuousGuidanceActor(env.obs_dim * 2, hidden_dim=16), horizon=2, history_len=2)
    if history_batch["obs"].shape[-1] != env.obs_dim * 2:
        failures.append("history-stacked obs shape mismatch")
    if batch["actions"].shape[-1] != 2:
        failures.append("continuous action dimension mismatch")
    if not np.isfinite(batch["logp"]).all() or not np.isfinite(batch["actions"]).all():
        failures.append("action/logp batch non-finite")
    with torch.no_grad():
        dist = actor.distribution(torch.as_tensor(batch["obs"].reshape(-1, env.obs_dim), dtype=torch.float32))
        recomputed = dist.log_prob(torch.as_tensor(batch["actions"].reshape(-1, 2), dtype=torch.float32)).reshape(batch["logp"].shape).numpy()
    if not np.allclose(recomputed, batch["logp"], atol=2e-5, rtol=2e-5):
        failures.append("collector old_logp mismatch")
    if not np.all(np.isin(batch["reset_mask"], [0.0, 1.0])):
        failures.append("reset mask is not binary")
    print(f"checks=7, failed={len(failures)}")
    for failure in failures:
        print(f"FAIL: {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
