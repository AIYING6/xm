from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.gat_mappo.simple_gat_mappo import GATMAPPOAgent
from algorithms.gat_mappo.simple_gat_mappo import stack_graphs as stack_gat_graphs
from algorithms.mappo.simple_mappo import MAPPOAgent
from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOAgent
from algorithms.ri_gmappo.simple_ri_gmappo import stack_graphs as stack_ri_graphs
from envs import UAVPursuitConfig, UAVPursuitEnv


@dataclass
class PolicySpec:
    name: str
    kind: str
    model: Path


def build_policy(spec: PolicySpec, env: UAVPursuitEnv, graph_obs: dict):
    if spec.kind == "mappo":
        agent = MAPPOAgent(env.obs_dim, env.share_obs_dim, env.action_dim, 128)
        agent.load_state_dict(torch.load(spec.model, map_location="cpu", weights_only=True))
        agent.eval()
        return agent

    if spec.kind == "gat":
        agent = GATMAPPOAgent(
            obs_dim=env.obs_dim,
            node_feat_dim=graph_obs["node_feat"].shape[-1],
            share_obs_dim=env.share_obs_dim,
            action_dim=env.action_dim,
            num_agents=env.num_agents,
            hidden_dim=128,
            role_dim=8,
        )
        agent.load_state_dict(torch.load(spec.model, map_location="cpu", weights_only=True))
        agent.eval()
        return agent

    if spec.kind == "ri":
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
        agent.load_state_dict(torch.load(spec.model, map_location="cpu", weights_only=True), strict=False)
        agent.eval()
        return agent

    raise ValueError(f"Unknown policy kind: {spec.kind}")


def act(spec: PolicySpec, agent, obs, share_obs, graph_obs):
    if spec.kind == "mappo":
        actions, _, _, _ = agent.get_action_and_value(
            torch.as_tensor(obs, dtype=torch.float32),
            torch.as_tensor(share_obs, dtype=torch.float32),
            deterministic=True,
        )
        return actions.numpy()

    if spec.kind == "gat":
        graph_batch = stack_gat_graphs([graph_obs])
        actions, _, _, _, _ = agent.get_action_and_value(
            torch.as_tensor(obs[None, ...], dtype=torch.float32),
            torch.as_tensor(graph_batch["node_feat"], dtype=torch.float32),
            torch.as_tensor(graph_batch["role"], dtype=torch.long),
            torch.as_tensor(graph_batch["adj"], dtype=torch.float32),
            torch.as_tensor(share_obs[None, ...], dtype=torch.float32),
            deterministic=True,
        )
        return actions.squeeze(0).numpy()

    graph_batch = stack_ri_graphs([graph_obs])
    actions, _, _, _, _, _ = agent.get_action_and_value(
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
    return actions.squeeze(0).numpy()


def run_episode(spec: PolicySpec, seed: int, target_policy: str, target_speed: float, radius: float) -> dict:
    env = UAVPursuitEnv(
        UAVPursuitConfig(
            seed=seed,
            target_policy=target_policy,
            target_speed=target_speed,
            communication_radius=radius,
        )
    )
    obs, share_obs, graph_obs = env.reset()
    agent = build_policy(spec, env, graph_obs)

    pursuer_traj = [env.p_pos.copy()]
    target_traj = [env.t_pos.copy()]
    with torch.no_grad():
        while True:
            actions = act(spec, agent, obs, share_obs, graph_obs)
            obs, share_obs, graph_obs, _, dones, info = env.step(actions)
            pursuer_traj.append(env.p_pos.copy())
            target_traj.append(env.t_pos.copy())
            if np.all(dones):
                break

    return {
        "spec": spec,
        "seed": seed,
        "info": info,
        "pursuer_traj": np.asarray(pursuer_traj),
        "target_traj": np.asarray(target_traj),
    }


def is_ri_advantage(results: list[dict]) -> bool:
    by_name = {r["spec"].name: r["info"] for r in results}
    ri_success = by_name["RI edge staged"]["success"]
    baseline_failed = (
        by_name["MAPPO"]["collision"]
        or by_name["MAPPO"]["timeout"]
        or by_name["GAT-MAPPO"]["collision"]
        or by_name["GAT-MAPPO"]["timeout"]
    )
    return bool(ri_success and baseline_failed)


def plot_case(results: list[dict], out_png: Path, radius: float) -> None:
    colors = ["tab:blue", "tab:orange", "tab:green"]
    fig, axes = plt.subplots(1, len(results), figsize=(5.2 * len(results), 5.0), sharex=True, sharey=True)
    if len(results) == 1:
        axes = [axes]

    for ax, result in zip(axes, results):
        p = result["pursuer_traj"]
        t = result["target_traj"][:, 0, :]
        info = result["info"]
        ax.plot(t[:, 0], t[:, 1], color="black", linewidth=2.0, linestyle="--", label="target")
        ax.scatter(t[0, 0], t[0, 1], color="black", marker="s", s=35)
        ax.scatter(t[-1, 0], t[-1, 1], color="black", marker="*", s=90)
        for i in range(p.shape[1]):
            ax.plot(p[:, i, 0], p[:, i, 1], color=colors[i], linewidth=1.8, label=f"uav{i}")
            ax.scatter(p[0, i, 0], p[0, i, 1], color=colors[i], marker="o", s=28)
            ax.scatter(p[-1, i, 0], p[-1, i, 1], color=colors[i], marker="x", s=45)
        status = "success" if info["success"] else "collision" if info["collision"] else "timeout"
        ax.set_title(f"{result['spec'].name}\n{status}, steps={info['step']}")
        ax.set_xlim(-10, 10)
        ax.set_ylim(-10, 10)
        ax.set_aspect("equal", adjustable="box")
        ax.grid(True, alpha=0.25)
    axes[0].legend(loc="upper right", fontsize=8)
    fig.suptitle(f"Mixed target, speed=0.75, communication radius={radius}")
    fig.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--radius", type=float, default=4.0)
    parser.add_argument("--target-policy", type=str, default="mixed")
    parser.add_argument("--target-speed", type=float, default=0.75)
    parser.add_argument("--start-seed", type=int, default=20_000)
    parser.add_argument("--search-episodes", type=int, default=200)
    parser.add_argument("--out-png", type=Path, default=Path("results/figures/trajectory_ri_advantage_r4.png"))
    parser.add_argument("--mappo-model", type=Path, default=Path("results/mappo_curriculum_slow_seed1_150/actor_critic_latest.pt"))
    parser.add_argument("--gat-model", type=Path, default=Path("results/gat_mappo_hybrid_slow_seed1_60_plus90/actor_critic_latest.pt"))
    parser.add_argument("--ri-model", type=Path, default=Path("results/ri_gmappo_edge_stage2_rand_seed1_20/actor_critic_latest.pt"))
    args = parser.parse_args()

    specs = [
        PolicySpec("MAPPO", "mappo", args.mappo_model),
        PolicySpec("GAT-MAPPO", "gat", args.gat_model),
        PolicySpec("RI edge staged", "ri", args.ri_model),
    ]

    chosen = None
    for offset in range(args.search_episodes):
        seed = args.start_seed + offset
        results = [
            run_episode(spec, seed, args.target_policy, args.target_speed, args.radius)
            for spec in specs
        ]
        if is_ri_advantage(results):
            chosen = results
            break
        if chosen is None:
            chosen = results

    plot_case(chosen, args.out_png, args.radius)
    for result in chosen:
        print(
            {
                "method": result["spec"].name,
                "seed": result["seed"],
                "radius": args.radius,
                **result["info"],
            },
            flush=True,
        )
    print(f"saved: {args.out_png}")


if __name__ == "__main__":
    main()
