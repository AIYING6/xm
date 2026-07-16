from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOAgent, stack_graphs
from envs import UAVPursuitConfig, UAVPursuitEnv


NODE_NAMES = ["uav0", "uav1", "uav2", "target"]


def load_agent(model: Path, env: UAVPursuitEnv, graph_obs: dict) -> RIGMAPPOAgent:
    agent = RIGMAPPOAgent(
        obs_dim=env.obs_dim,
        node_feat_dim=graph_obs["node_feat"].shape[-1],
        edge_feat_dim=graph_obs["edge_feat"].shape[-1],
        share_obs_dim=env.share_obs_dim,
        action_dim=env.action_dim,
        num_agents=env.num_agents,
        hidden_dim=128,
        role_dim=8,
        intent_dim=8,
    )
    agent.load_state_dict(torch.load(model, map_location="cpu", weights_only=True), strict=False)
    agent.eval()
    return agent


def run_episode(model: Path, seed: int, radius: float, target_policy: str, target_speed: float) -> tuple[dict, np.ndarray]:
    env = UAVPursuitEnv(
        UAVPursuitConfig(
            seed=seed,
            target_policy=target_policy,
            target_speed=target_speed,
            communication_radius=radius,
        )
    )
    obs, share_obs, graph_obs = env.reset()
    agent = load_agent(model, env, graph_obs)
    attn_records = []
    with torch.no_grad():
        while True:
            graph_batch = stack_graphs([graph_obs])
            actions, _, _, _, attn, _ = agent.get_action_and_value(
                torch.as_tensor(obs[None, ...], dtype=torch.float32),
                torch.as_tensor(graph_batch["node_feat"], dtype=torch.float32),
                torch.as_tensor(graph_batch["edge_feat"], dtype=torch.float32),
                torch.as_tensor(graph_batch["role"], dtype=torch.long),
                torch.as_tensor(graph_batch["adj"], dtype=torch.float32),
                torch.as_tensor(share_obs[None, ...], dtype=torch.float32),
                deterministic=True,
                intent_label=torch.as_tensor(graph_batch["intent_label"], dtype=torch.long),
                detach_intent=True,
                oracle_intent=False,
            )
            attn_records.append(attn.squeeze(0).numpy())
            obs, share_obs, graph_obs, _, dones, info = env.step(actions.squeeze(0).numpy())
            if np.all(dones):
                break
    return info, np.asarray(attn_records).mean(axis=0)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, default=Path("results/ri_gmappo_edge_stage2_rand_seed1_20/actor_critic_latest.pt"))
    parser.add_argument("--radius", type=float, default=4.0)
    parser.add_argument("--target-policy", type=str, default="mixed")
    parser.add_argument("--target-speed", type=float, default=0.75)
    parser.add_argument("--start-seed", type=int, default=20_000)
    parser.add_argument("--search-episodes", type=int, default=100)
    parser.add_argument("--out-png", type=Path, default=Path("results/figures/ri_attention_heatmap_r4.png"))
    parser.add_argument("--out-csv", type=Path, default=Path("results/ri_attention_heatmap_r4.csv"))
    args = parser.parse_args()

    chosen_info = None
    chosen_attn = None
    chosen_seed = None
    for offset in range(args.search_episodes):
        seed = args.start_seed + offset
        info, attn = run_episode(args.model, seed, args.radius, args.target_policy, args.target_speed)
        if chosen_info is None:
            chosen_info, chosen_attn, chosen_seed = info, attn, seed
        if info["success"]:
            chosen_info, chosen_attn, chosen_seed = info, attn, seed
            break

    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["source", "target", "attention"])
        for i, src in enumerate(NODE_NAMES):
            for j, dst in enumerate(NODE_NAMES):
                writer.writerow([src, dst, float(chosen_attn[i, j])])

    fig, ax = plt.subplots(figsize=(5.2, 4.8))
    im = ax.imshow(chosen_attn, cmap="viridis", vmin=0.0, vmax=max(0.5, float(chosen_attn.max())))
    ax.set_xticks(range(len(NODE_NAMES)), NODE_NAMES)
    ax.set_yticks(range(len(NODE_NAMES)), NODE_NAMES)
    ax.set_xlabel("Attended node")
    ax.set_ylabel("Query node")
    status = "success" if chosen_info["success"] else "collision" if chosen_info["collision"] else "timeout"
    ax.set_title(f"RI attention, r={args.radius}, seed={chosen_seed}, {status}")
    for i in range(len(NODE_NAMES)):
        for j in range(len(NODE_NAMES)):
            ax.text(j, i, f"{chosen_attn[i, j]:.2f}", ha="center", va="center", color="white", fontsize=8)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    args.out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out_png, dpi=180)
    plt.close(fig)

    print({"seed": chosen_seed, "radius": args.radius, **chosen_info})
    print(f"saved: {args.out_png}")
    print(f"saved: {args.out_csv}")


if __name__ == "__main__":
    main()
