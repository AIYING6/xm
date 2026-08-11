"""Small R2 B0/B2 learnability smoke; not formal evidence."""
from __future__ import annotations

import argparse
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


def evaluate(env: V16RIntercept3DEnv, actor, graph_conditioned: bool, episodes: int = 8) -> dict[str, float]:
    successes = 0
    steps = []
    for _ in range(episodes):
        obs, _share, graph = env.reset()
        for step in range(env.config.max_steps):
            with torch.no_grad():
                obs_t = torch.as_tensor(obs, dtype=torch.float32)
                if graph_conditioned:
                    action, _ = actor(obs_t, torch.as_tensor(graph["node"], dtype=torch.float32), torch.as_tensor(graph["relation_adj"], dtype=torch.float32), deterministic=True)
                else:
                    action, _ = actor(obs_t, deterministic=True)
            obs, _share, graph, _rewards, dones, info = env.step(action.numpy())
            if bool(dones.all()):
                successes += int(float(info.get("success", 0.0)) > 0.5)
                steps.append(step + 1)
                break
    return {"success_rate": successes / episodes, "mean_terminal_step": float(np.mean(steps)) if steps else float(env.config.max_steps)}


def run(seed: int, graph_conditioned: bool, updates: int, horizon: int) -> dict[str, object]:
    torch.manual_seed(seed)
    env = V16RIntercept3DEnv(UAVIntercept3DConfig(seed=seed, max_steps=60, strict_target_sensing=True, agent_target_info_bottleneck=True, v16r_mission_mode=True))
    actor = RecipientGraphGuidanceActor(env.obs_dim, hidden_dim=64) if graph_conditioned else ContinuousGuidanceActor(env.obs_dim, hidden_dim=64)
    critic = CentralizedValueCritic(env.share_obs_dim, hidden_dim=64)
    optimizer = torch.optim.Adam(list(actor.parameters()) + list(critic.parameters()), lr=3e-4)
    cfg = V16RPPOConfig(epochs=1)
    losses = []
    for _ in range(updates):
        batch = collect_v16r_rollout(env, actor, horizon=horizon, graph_conditioned=graph_conditioned)
        metrics = ppo_update(actor, critic, batch, cfg, graph_conditioned=graph_conditioned, optimizer=optimizer)
        losses.append(metrics)
    eval_result = evaluate(env, actor, graph_conditioned)
    return {"seed": seed, "method": "B2_unified_graph" if graph_conditioned else "B0_flat", "updates": updates, "horizon": horizon, "evaluation": eval_result, "last_metrics": losses[-1]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results/v1_6r_r2_baseline_smoke.json")
    parser.add_argument("--updates", type=int, default=12)
    parser.add_argument("--horizon", type=int, default=32)
    args = parser.parse_args()
    results = []
    for seed in (17101, 17102):
        results.append(run(seed, False, args.updates, args.horizon))
        results.append(run(seed, True, args.updates, args.horizon))
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"status": "development_only", "results": results}, indent=2), encoding="utf-8")
    print(json.dumps({"status": "development_only", "results": results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
