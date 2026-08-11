"""Diagnostic only: legal BC warm-start followed by unchanged PPO."""
from __future__ import annotations

import math
import numpy as np
import torch

from algorithms.mappo.continuous_guidance_policy import ContinuousGuidanceActor
from algorithms.mappo.v16r_ppo import CentralizedValueCritic, V16RPPOConfig, ppo_update
from algorithms.mappo.v16r_rollout import collect_v16r_rollout
from envs.uav_intercept_3d_env import ROLE_ATTACKER, angle_diff, UAVIntercept3DConfig
from envs.v16r_env_adapter import V16RIntercept3DEnv


def legal_label(env):
    a = np.zeros((env.num_agents, 2), dtype=np.float32)
    for i, typ in enumerate(env.config.blue_types):
        if typ.role != ROLE_ATTACKER:
            continue
        e = env.legal.target_evidence(i)
        if not e.available:
            continue
        rel = e.position - env.base.blue_pos[i]
        desired = math.atan2(float(rel[1]), float(rel[0]))
        a[i, 0] = np.clip(angle_diff(desired, float(env.base.blue_heading[i])) / max(typ.max_turn_rate, 1e-6), -1.0, 1.0)
        desired_gamma = math.atan2(float(rel[2]), float(np.linalg.norm(rel[:2]) + 1e-6))
        a[i, 1] = np.clip((desired_gamma - float(env.base.blue_gamma[i])) / max(typ.max_gamma, 1e-6), -1.0, 1.0)
    return a


def main() -> int:
    torch.manual_seed(17074)
    env = V16RIntercept3DEnv(UAVIntercept3DConfig(seed=17074, max_steps=60, v16r_mission_mode=True))
    actor = ContinuousGuidanceActor(env.obs_dim, hidden_dim=64, role_specific=True)
    critic = CentralizedValueCritic(env.share_obs_dim, hidden_dim=64)
    bc_opt = torch.optim.Adam(actor.parameters(), lr=1e-3)
    xs, ys = [], []
    for _ in range(8):
        obs, _s, _g = env.reset()
        for _ in range(60):
            xs.append(obs.copy()); ys.append(legal_label(env)); obs, _s, _g, _r, d, _i = env.step(ys[-1])
            if bool(d.all()): break
    x = torch.as_tensor(np.concatenate(xs), dtype=torch.float32)
    y = torch.as_tensor(np.concatenate(ys), dtype=torch.float32)
    for _ in range(80):
        loss = (actor.distribution(x).deterministic() - y).square().mean()
        bc_opt.zero_grad(); loss.backward(); bc_opt.step()
    ppo_opt = torch.optim.Adam(list(actor.parameters()) + list(critic.parameters()), lr=3e-4)
    for _ in range(20):
        batch = collect_v16r_rollout(env, actor, horizon=32)
        ppo_update(actor, critic, batch, V16RPPOConfig(epochs=1), optimizer=ppo_opt)
    successes = 0
    for seed in range(17150, 17154):
        test = V16RIntercept3DEnv(UAVIntercept3DConfig(seed=seed, max_steps=180, v16r_mission_mode=True))
        obs, _s, _g = test.reset()
        for _ in range(180):
            with torch.no_grad(): action = actor.distribution(torch.as_tensor(obs, dtype=torch.float32)).deterministic().numpy()
            obs, _s, _g, _r, d, info = test.step(action)
            if bool(d.all()):
                successes += int(float(info.get("success", 0.0)) > 0.5); break
    print({"bc_loss": float(loss.detach()), "ppo_warmstart_neutralized": successes, "episodes": 4})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
