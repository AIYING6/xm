"""Transparent behavior-cloning diagnostic; not a method or paper result."""
from __future__ import annotations

import math
import numpy as np
import torch
from torch import nn

from algorithms.mappo.continuous_guidance_policy import ContinuousGuidanceActor
from envs.uav_intercept_3d_env import ROLE_ATTACKER, angle_diff, UAVIntercept3DConfig
from envs.v16r_env_adapter import V16RIntercept3DEnv


def label(env, obs):
    actions = np.zeros((env.num_agents, 2), dtype=np.float32)
    for i, typ in enumerate(env.config.blue_types):
        if typ.role != ROLE_ATTACKER:
            continue
        evidence = env.legal.target_evidence(i)
        if not evidence.available:
            continue
        rel = evidence.position - env.base.blue_pos[i]
        desired = math.atan2(float(rel[1]), float(rel[0]))
        actions[i, 0] = np.clip(angle_diff(desired, float(env.base.blue_heading[i])) / max(typ.max_turn_rate, 1e-6), -1.0, 1.0)
        desired_gamma = math.atan2(float(rel[2]), float(np.linalg.norm(rel[:2]) + 1e-6))
        actions[i, 1] = np.clip((desired_gamma - float(env.base.blue_gamma[i])) / max(typ.max_gamma, 1e-6), -1.0, 1.0)
    return actions


def main() -> int:
    torch.manual_seed(17073)
    env = V16RIntercept3DEnv(UAVIntercept3DConfig(seed=17073, max_steps=60, v16r_mission_mode=True))
    obs_rows, action_rows = [], []
    for episode in range(16):
        obs, _share, _graph = env.reset()
        for _ in range(60):
            actions = label(env, obs)
            obs_rows.append(obs.copy())
            action_rows.append(actions.copy())
            obs, _share, _graph, _reward, dones, _info = env.step(actions)
            if bool(dones.all()):
                break
    x = torch.as_tensor(np.concatenate(obs_rows), dtype=torch.float32)
    y = torch.as_tensor(np.concatenate(action_rows), dtype=torch.float32)
    actor = ContinuousGuidanceActor(env.obs_dim, hidden_dim=64, role_specific=True)
    optim = torch.optim.Adam(actor.parameters(), lr=1e-3)
    for _ in range(120):
        pred = actor.distribution(x).deterministic()
        loss = (pred - y).square().mean()
        optim.zero_grad(); loss.backward(); optim.step()
    with torch.no_grad():
        fit_error = float((actor.distribution(x).deterministic() - y).abs().mean())
    successes = 0
    for seed in range(17140, 17144):
        test_env = V16RIntercept3DEnv(UAVIntercept3DConfig(seed=seed, max_steps=180, v16r_mission_mode=True))
        obs, _share, _graph = test_env.reset()
        for _ in range(180):
            with torch.no_grad():
                action = actor.distribution(torch.as_tensor(obs, dtype=torch.float32)).deterministic().numpy()
            obs, _share, _graph, _reward, dones, info = test_env.step(action)
            if bool(dones.all()):
                successes += int(float(info.get("success", 0.0)) > 0.5)
                break
    print({"bc_fit_abs_error": fit_error, "bc_eval_neutralized": successes, "bc_eval_episodes": 4})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
