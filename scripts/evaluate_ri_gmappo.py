from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOAgent, stack_graphs
from envs import UAVPursuitConfig, UAVPursuitEnv


def evaluate(
    model_path: Path,
    episodes: int,
    target_policy: str,
    target_speed: float,
    communication_radius: float,
    deterministic: bool,
    detach_intent: bool,
    oracle_intent: bool,
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
    agent = RIGMAPPOAgent(
        obs_dim=env0.obs_dim,
        node_feat_dim=graph_obs["node_feat"].shape[-1],
        edge_feat_dim=graph_obs["edge_feat"].shape[-1],
        share_obs_dim=env0.share_obs_dim,
        action_dim=env0.action_dim,
        num_agents=env0.num_agents,
        hidden_dim=128,
        role_dim=8,
        intent_dim=8,
    )
    state = torch.load(model_path, map_location="cpu", weights_only=True)
    agent.load_state_dict(state, strict=False)
    agent.eval()

    records = []
    intent_correct, intent_total = 0, 0
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
                actions, _, _, _, _, intent_logits = agent.get_action_and_value(
                    torch.as_tensor(obs[None, ...], dtype=torch.float32),
                    torch.as_tensor(graph_batch["node_feat"], dtype=torch.float32),
                    torch.as_tensor(graph_batch["edge_feat"], dtype=torch.float32),
                    torch.as_tensor(graph_batch["role"], dtype=torch.long),
                    torch.as_tensor(graph_batch["adj"], dtype=torch.float32),
                    torch.as_tensor(share_obs[None, ...], dtype=torch.float32),
                    deterministic=deterministic,
                    intent_label=torch.as_tensor(graph_batch["intent_label"], dtype=torch.long),
                    detach_intent=detach_intent,
                    oracle_intent=oracle_intent,
                )
                pred = intent_logits.argmax(dim=-1).numpy()
                intent_correct += int((pred == graph_batch["intent_label"]).sum())
                intent_total += int(np.prod(graph_batch["intent_label"].shape))

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
        "detach_intent": detach_intent,
        "oracle_intent": oracle_intent,
        "success_rate": float(np.mean([r["success"] for r in records])),
        "collision_rate": float(np.mean([r["collision"] for r in records])),
        "timeout_rate": float(np.mean([r["timeout"] for r in records])),
        "avg_steps": float(np.mean([r["step"] for r in records])),
        "avg_mean_distance": float(np.mean([r["mean_distance"] for r in records])),
        "intent_accuracy": float(intent_correct / max(1, intent_total)),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--episodes", type=int, default=30)
    parser.add_argument("--target-policy", type=str, default="mixed")
    parser.add_argument("--target-speed", type=float, default=0.75)
    parser.add_argument("--communication-radius", type=float, default=8.0)
    parser.add_argument("--stochastic", action="store_true")
    parser.add_argument("--detach-intent", action="store_true")
    parser.add_argument("--oracle-intent", action="store_true")
    args = parser.parse_args()
    print(
        evaluate(
            args.model,
            args.episodes,
            args.target_policy,
            args.target_speed,
            args.communication_radius,
            not args.stochastic,
            args.detach_intent,
            args.oracle_intent,
        )
    )


if __name__ == "__main__":
    main()
