"""No-training smoke: vanilla continuous actor driving the v1.6R facade."""
from __future__ import annotations

import numpy as np
import torch

from algorithms.mappo.continuous_guidance_policy import ContinuousGuidanceActor
from envs.uav_intercept_3d_env import UAVIntercept3DConfig
from envs.v16r_env_adapter import V16RIntercept3DEnv


def main() -> int:
    torch.manual_seed(17066)
    env = V16RIntercept3DEnv(UAVIntercept3DConfig(seed=17066, max_steps=8, v16r_mission_mode=True))
    actor = ContinuousGuidanceActor(env.obs_dim, hidden_dim=32)
    obs, share, graph = env.reset()
    failures: list[str] = []
    for _ in range(3):
        with torch.no_grad():
            actions, _logp = actor(torch.as_tensor(obs, dtype=torch.float32))
        obs, share, graph, rewards, dones, info = env.step(actions.numpy())
        if actions.shape != (env.num_agents, 2):
            failures.append("actor action shape mismatch")
        if not np.isfinite(obs).all() or not np.isfinite(rewards).all():
            failures.append("rollout output non-finite")
        if graph["node"].shape[0] != env.num_agents:
            failures.append("recipient graph dimension lost in rollout")
        if bool(dones.all()):
            break
    print(f"checks=4, failed={len(failures)}")
    for failure in failures:
        print(f"FAIL: {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
