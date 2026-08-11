"""Diagnostic: compare joint PPO update with actor-only optimizer after BC."""
from __future__ import annotations

import math
import numpy as np
import torch

from algorithms.mappo.continuous_guidance_policy import ContinuousGuidanceActor
from algorithms.mappo.v16r_ppo import CentralizedValueCritic, V16RPPOConfig, ppo_update
from algorithms.mappo.v16r_rollout import collect_v16r_rollout
from envs.uav_intercept_3d_env import ROLE_ATTACKER, angle_diff, UAVIntercept3DConfig
from envs.v16r_env_adapter import V16RIntercept3DEnv


def eval_success(actor, seeds):
    count = 0
    for seed in seeds:
        env = V16RIntercept3DEnv(UAVIntercept3DConfig(seed=seed, max_steps=180, v16r_mission_mode=True))
        obs, _s, _g = env.reset()
        for _ in range(180):
            with torch.no_grad(): action = actor.distribution(torch.as_tensor(obs, dtype=torch.float32)).deterministic().numpy()
            obs, _s, _g, _r, d, info = env.step(action)
            if bool(d.all()):
                count += int(float(info.get("success", 0.0)) > 0.5); break
    return count


def main() -> int:
    torch.manual_seed(17075)
    env = V16RIntercept3DEnv(UAVIntercept3DConfig(seed=17075, max_steps=60, v16r_mission_mode=True))
    actor = ContinuousGuidanceActor(env.obs_dim, hidden_dim=64, role_specific=True)
    xs, ys = [], []
    for _ in range(8):
        obs, _s, _g = env.reset()
        for _ in range(60):
            y = np.zeros((env.num_agents, 2), dtype=np.float32)
            for i, typ in enumerate(env.config.blue_types):
                if typ.role != ROLE_ATTACKER: continue
                e = env.legal.target_evidence(i)
                if not e.available: continue
                rel = e.position - env.base.blue_pos[i]
                y[i, 0] = np.clip(angle_diff(math.atan2(float(rel[1]), float(rel[0])), float(env.base.blue_heading[i])) / typ.max_turn_rate, -1, 1)
            xs.append(obs.copy()); ys.append(y); obs, _s, _g, _r, d, _i = env.step(y)
            if bool(d.all()): break
    x, y = torch.as_tensor(np.concatenate(xs), dtype=torch.float32), torch.as_tensor(np.concatenate(ys), dtype=torch.float32)
    bc_opt = torch.optim.Adam(actor.parameters(), lr=1e-3)
    for _ in range(80):
        loss = (actor.distribution(x).deterministic() - y).square().mean(); bc_opt.zero_grad(); loss.backward(); bc_opt.step()
    critic_joint, actor_joint = CentralizedValueCritic(env.share_obs_dim, 64), actor
    critic_actor_only = CentralizedValueCritic(env.share_obs_dim, 64)
    # Clone the same BC actor so both branches start identically.
    actor_actor_only = ContinuousGuidanceActor(env.obs_dim, hidden_dim=64, role_specific=True)
    actor_actor_only.load_state_dict(actor.state_dict())
    batch_joint = collect_v16r_rollout(env, actor_joint, 32)
    batch_actor = collect_v16r_rollout(env, actor_actor_only, 32)
    ppo_update(actor_joint, critic_joint, batch_joint, V16RPPOConfig(epochs=1), optimizer=torch.optim.Adam(list(actor_joint.parameters()) + list(critic_joint.parameters()), lr=3e-4))
    ppo_update(actor_actor_only, critic_actor_only, batch_actor, V16RPPOConfig(epochs=1), optimizer=torch.optim.Adam(actor_actor_only.parameters(), lr=3e-4))
    print({"bc_loss": float(loss.detach()), "joint_success": eval_success(actor_joint, range(17160, 17162)), "actor_only_success": eval_success(actor_actor_only, range(17160, 17162))})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
