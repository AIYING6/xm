from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.gat_mappo.simple_gat_mappo import GATMAPPOAgent, stack_graphs
from envs import UAVPursuitConfig, UAVPursuitEnv


def evaluate(
    model_path: Path,
    episodes: int,
    target_policy: str,
    target_speed: float,
    communication_radius: float,
    deterministic: bool,
) -> dict:
    env0 = UAVPursuitEnv(
        UAVPursuitConfig(
            seed=0,
            target_policy=target_policy,
            target_speed=target_speed,
            communication_radius=communication_radius,
        )
    )
    _, share_obs, graph_obs = env0.reset()
    agent = GATMAPPOAgent(
        obs_dim=env0.obs_dim,
        node_feat_dim=graph_obs["node_feat"].shape[-1],
        share_obs_dim=env0.share_obs_dim,
        action_dim=env0.action_dim,
        num_agents=env0.num_agents,
        hidden_dim=128,
        role_dim=8,
    )
    agent.load_state_dict(torch.load(model_path, map_location="cpu", weights_only=True))
    agent.eval()

    records = []
    with torch.no_grad():
        for ep in range(episodes):
            env = UAVPursuitEnv(
                UAVPursuitConfig(
                    seed=20_000 + ep,
                    target_policy=target_policy,
                    target_speed=target_speed,
                    communication_radius=communication_radius,
                )
            )
            obs, share_obs, graph_obs = env.reset()
            while True:
                graph_batch = stack_graphs([graph_obs])
                actions, _, _, _, _ = agent.get_action_and_value(
                    torch.as_tensor(obs[None, ...], dtype=torch.float32),
                    torch.as_tensor(graph_batch["node_feat"], dtype=torch.float32),
                    torch.as_tensor(graph_batch["role"], dtype=torch.long),
                    torch.as_tensor(graph_batch["adj"], dtype=torch.float32),
                    torch.as_tensor(share_obs[None, ...], dtype=torch.float32),
                    deterministic=deterministic,
                )
                obs, share_obs, graph_obs, _, dones, info = env.step(actions.squeeze(0).numpy())
                if np.all(dones):
                    records.append(info)
                    break

    return {
        "model": str(model_path),
        "episodes": episodes,
        "target_policy": target_policy,
        "target_speed": target_speed,
        "communication_radius": communication_radius,
        "deterministic": deterministic,
        "success_rate": float(np.mean([r["success"] for r in records])),
        "collision_rate": float(np.mean([r["collision"] for r in records])),
        "timeout_rate": float(np.mean([r["timeout"] for r in records])),
        "avg_steps": float(np.mean([r["step"] for r in records])),
        "avg_mean_distance": float(np.mean([r["mean_distance"] for r in records])),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--episodes", type=int, default=30)
    parser.add_argument("--target-policy", type=str, default="mixed")
    parser.add_argument("--target-speed", type=float, default=0.75)
    parser.add_argument("--communication-radius", type=float, default=8.0)
    parser.add_argument("--stochastic", action="store_true")
    args = parser.parse_args()
    print(
        evaluate(
            args.model,
            args.episodes,
            args.target_policy,
            args.target_speed,
            args.communication_radius,
            not args.stochastic,
        )
    )


if __name__ == "__main__":
    main()
