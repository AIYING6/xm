"""Unified short R2 protocol for B0/B1/B2; development-only."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch

from algorithms.mappo.continuous_guidance_policy import ContinuousGuidanceActor
from algorithms.mappo.recipient_graph_guidance_policy import RecipientGraphGuidanceActor
from algorithms.mappo.v16r_ppo import CentralizedValueCritic, V16RPPOConfig, ppo_update
from algorithms.mappo.v16r_rollout import collect_v16r_rollout
from envs.uav_intercept_3d_env import UAVIntercept3DConfig
from envs.v16r_env_adapter import V16RIntercept3DEnv


def make_actor(method: str, obs_dim: int):
    if method == "B2_unified_graph":
        return RecipientGraphGuidanceActor(obs_dim, hidden_dim=64, role_specific=True)
    width = obs_dim * 4 if method == "B1_history4" else obs_dim
    return ContinuousGuidanceActor(width, hidden_dim=64, role_specific=True)


def evaluate(env, actor, method: str, episodes: int = 8):
    success = 0
    for _ in range(episodes):
        obs, _share, graph = env.reset()
        history = np.repeat(obs[:, None, :], 4, axis=1)
        for _step in range(env.config.max_steps):
            model_obs = history.reshape(env.num_agents, -1) if method == "B1_history4" else obs
            with torch.no_grad():
                obs_t = torch.as_tensor(model_obs, dtype=torch.float32)
                if method == "B2_unified_graph":
                    action, _ = actor(obs_t, torch.as_tensor(graph["node"], dtype=torch.float32), torch.as_tensor(graph["relation_adj"], dtype=torch.float32), deterministic=True)
                else:
                    action, _ = actor(obs_t, deterministic=True)
            obs, _share, graph, _reward, dones, info = env.step(action.numpy())
            history = np.concatenate([history[:, 1:, :], obs[:, None, :]], axis=1)
            if bool(dones.all()):
                success += int(float(info.get("success", 0.0)) > 0.5)
                break
    return success / episodes


def run(seed: int, method: str, updates: int = 12, horizon: int = 32, save_dir: Path | None = None):
    torch.manual_seed(seed)
    env = V16RIntercept3DEnv(UAVIntercept3DConfig(seed=seed, max_steps=60, v16r_mission_mode=True))
    actor = make_actor(method, env.obs_dim)
    critic = CentralizedValueCritic(env.share_obs_dim, hidden_dim=64)
    optimizer = torch.optim.Adam(list(actor.parameters()) + list(critic.parameters()), lr=3e-4)
    cfg = V16RPPOConfig(epochs=1)
    for _ in range(updates):
        batch = collect_v16r_rollout(env, actor, horizon, graph_conditioned=method == "B2_unified_graph", history_len=4 if method == "B1_history4" else 1)
        ppo_update(actor, critic, batch, cfg, graph_conditioned=method == "B2_unified_graph", optimizer=optimizer)
    if save_dir is not None:
        save_dir.mkdir(parents=True, exist_ok=True)
        torch.save({"actor": actor.state_dict(), "critic": critic.state_dict(), "method": method, "seed": seed}, save_dir / f"{method}_{seed}.pt")
    return {"seed": seed, "method": method, "updates": updates, "horizon": horizon, "eval_success_rate": evaluate(env, actor, method)}


def main() -> int:
    updates = 60
    save_dir = Path("results/v1_6r_r2_checkpoints")
    rows = [run(seed, method, updates=updates, save_dir=save_dir) for seed in (17101, 17102) for method in ("B0_flat", "B1_history4", "B2_unified_graph")]
    payload = {"status": "development_only", "protocol": {"seeds": [17101, 17102], "updates": updates, "horizon": 32}, "results": rows}
    path = Path("results/v1_6r_r2_three_baselines.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
