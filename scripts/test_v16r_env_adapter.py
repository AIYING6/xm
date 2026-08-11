"""End-to-end R1 smoke for the v1.6R environment facade."""
from __future__ import annotations

import numpy as np

from envs.uav_intercept_3d_env import UAVIntercept3DConfig
from envs.v16r_env_adapter import V16RIntercept3DEnv


def main() -> int:
    env = V16RIntercept3DEnv(UAVIntercept3DConfig(seed=17063, max_steps=5))
    failures: list[str] = []
    obs, share, graph = env.reset()
    if obs.shape != (env.num_agents, env.obs_dim):
        failures.append("obs shape mismatch")
    if graph["node"].shape[0] != env.num_agents:
        failures.append("recipient dimension missing from graph")
    obs2, share2, graph2, rewards, dones, info = env.step(np.zeros((env.num_agents, 2), dtype=np.float32))
    if graph2["edge"].shape[0] != env.num_agents or rewards.shape[0] != env.num_agents:
        failures.append("step output shape mismatch")
    if not np.isfinite(obs2).all() or not np.isfinite(graph2["node"]).all():
        failures.append("non-finite adapter output")
    print(f"checks=5, failed={len(failures)}")
    for failure in failures:
        print(f"FAIL: {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
