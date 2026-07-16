from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOAgent, stack_graphs
from envs import UAVPursuitConfig, UAVPursuitEnv


FINAL_EA_RG_RUNS = [
    {
        "method": "EA-RG-MAPPO-S",
        "seed": 0,
        "model": Path("results/ri_gmappo_edge_stage2_rand_seed0_20/actor_critic_latest.pt"),
    },
    {
        "method": "EA-RG-MAPPO-S",
        "seed": 1,
        "model": Path("results/ri_gmappo_edge_stage2_rand_seed1_20/actor_critic_latest.pt"),
    },
    {
        "method": "EA-RG-MAPPO-S",
        "seed": 2,
        "model": Path("results/ri_gmappo_edge_stage2_rand_seed2_20/actor_critic_latest.pt"),
    },
]


EDGE_GROUPS = {
    "none": [],
    "zero_rel_pos": [0, 1],
    "zero_distance": [2, 3],
    "zero_bearing": [4, 5],
    "zero_rel_velocity": [6, 7],
    "zero_comm_target_flags": [8, 9],
    "zero_all_edge_features": list(range(10)),
}


EDGE_DIM_NAMES = [
    "rel_x/world",
    "rel_y/world",
    "distance/world",
    "distance/comm_radius",
    "cos(bearing)",
    "sin(bearing)",
    "rel_vx/1.5",
    "rel_vy/1.5",
    "comm_reachable",
    "target_node_flag",
]


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def std(values: list[float]) -> float:
    m = mean(values)
    return math.sqrt(sum((v - m) ** 2 for v in values) / len(values))


def mask_edge_features(edge_feat: np.ndarray, zero_dims: list[int]) -> np.ndarray:
    masked = edge_feat.copy()
    if zero_dims:
        masked[..., zero_dims] = 0.0
    return masked


def make_agent(model_path: Path) -> RIGMAPPOAgent:
    env0 = UAVPursuitEnv(UAVPursuitConfig(seed=0, target_policy="mixed", target_speed=0.75))
    _, _, graph_obs = env0.reset()
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
    return agent


def evaluate_ablation(
    agent: RIGMAPPOAgent,
    run: dict,
    episodes: int,
    target_policy: str,
    target_speed: float,
    communication_radius: float,
    ablation_name: str,
    zero_dims: list[int],
) -> dict:
    records = []
    intent_correct = 0
    intent_total = 0
    with torch.no_grad():
        for ep in range(episodes):
            env = UAVPursuitEnv(
                UAVPursuitConfig(
                    seed=30_000 + int(run["seed"]) * 10_000 + ep,
                    target_policy=target_policy,
                    target_speed=target_speed,
                    communication_radius=communication_radius,
                )
            )
            obs, share_obs, graph_obs = env.reset()
            while True:
                graph_batch = stack_graphs([graph_obs])
                graph_batch["edge_feat"] = mask_edge_features(graph_batch["edge_feat"], zero_dims)
                actions, _, _, _, _, intent_logits = agent.get_action_and_value(
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
                pred = intent_logits.argmax(dim=-1).numpy()
                intent_correct += int((pred == graph_batch["intent_label"]).sum())
                intent_total += int(np.prod(graph_batch["intent_label"].shape))

                obs, share_obs, graph_obs, _, dones, info = env.step(actions.squeeze(0).numpy())
                if np.all(dones):
                    records.append(info)
                    break

    return {
        "method": run["method"],
        "seed": run["seed"],
        "model": str(run["model"]),
        "episodes": episodes,
        "target_policy": target_policy,
        "target_speed": target_speed,
        "radius": communication_radius,
        "ablation": ablation_name,
        "zero_dims": " ".join(str(dim) for dim in zero_dims),
        "zero_dim_names": "; ".join(EDGE_DIM_NAMES[dim] for dim in zero_dims),
        "success_rate": float(np.mean([r["success"] for r in records])),
        "collision_rate": float(np.mean([r["collision"] for r in records])),
        "timeout_rate": float(np.mean([r["timeout"] for r in records])),
        "avg_steps": float(np.mean([r["step"] for r in records])),
        "avg_mean_distance": float(np.mean([r["mean_distance"] for r in records])),
        "intent_accuracy": float(intent_correct / max(1, intent_total)),
    }


def summarize(rows: list[dict]) -> list[dict]:
    summary = []
    radii = sorted({float(row["radius"]) for row in rows})
    ablations = list(dict.fromkeys(row["ablation"] for row in rows))
    for radius in radii:
        for ablation in ablations:
            group = [row for row in rows if float(row["radius"]) == radius and row["ablation"] == ablation]
            summary.append(
                {
                    "radius": radius,
                    "ablation": ablation,
                    "episodes": group[0]["episodes"],
                    "n": len(group),
                    "zero_dims": group[0]["zero_dims"],
                    "zero_dim_names": group[0]["zero_dim_names"],
                    "success_mean": mean([float(row["success_rate"]) for row in group]),
                    "success_std": std([float(row["success_rate"]) for row in group]),
                    "collision_mean": mean([float(row["collision_rate"]) for row in group]),
                    "collision_std": std([float(row["collision_rate"]) for row in group]),
                    "timeout_mean": mean([float(row["timeout_rate"]) for row in group]),
                    "timeout_std": std([float(row["timeout_rate"]) for row in group]),
                    "avg_steps_mean": mean([float(row["avg_steps"]) for row in group]),
                    "avg_steps_std": std([float(row["avg_steps"]) for row in group]),
                }
            )
    return summary


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(summary: list[dict], path: Path) -> None:
    baseline_by_radius = {
        float(row["radius"]): row for row in summary if row["ablation"] == "none"
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Edge Feature Evaluation-Time Ablation",
        "",
        "说明：该实验不重新训练模型，只在评估时将 EA-RG-MAPPO-S 的部分 edge feature 维度置零，用于诊断策略对不同边信息的依赖。结果只能作为机制分析和附录证据，不应替代训练期结构消融。",
        "",
        "| Radius | Ablation | Zeroed dims | Success | Delta success | Collision | Delta collision | Timeout | Avg steps |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary:
        baseline = baseline_by_radius[float(row["radius"])]
        delta_success = float(row["success_mean"]) - float(baseline["success_mean"])
        delta_collision = float(row["collision_mean"]) - float(baseline["collision_mean"])
        lines.append(
            "| {radius:g} | {ablation} | {dims} | {succ:.3f} ± {succ_std:.3f} | {dsucc:+.3f} | {coll:.3f} ± {coll_std:.3f} | {dcoll:+.3f} | {tout:.3f} ± {tout_std:.3f} | {steps:.1f} ± {steps_std:.1f} |".format(
                radius=float(row["radius"]),
                ablation=row["ablation"],
                dims=row["zero_dims"] or "none",
                succ=float(row["success_mean"]),
                succ_std=float(row["success_std"]),
                dsucc=delta_success,
                coll=float(row["collision_mean"]),
                coll_std=float(row["collision_std"]),
                dcoll=delta_collision,
                tout=float(row["timeout_mean"]),
                tout_std=float(row["timeout_std"]),
                steps=float(row["avg_steps_mean"]),
                steps_std=float(row["avg_steps_std"]),
            )
        )
    lines.extend(
        [
            "",
            "边特征维度定义：",
            "",
        ]
    )
    for idx, name in enumerate(EDGE_DIM_NAMES):
        lines.append(f"- `{idx}`: {name}")
    lines.extend(
        [
            "",
            "结果解读：",
            "",
            "```text",
            "1. 该评估时消融整体呈弱敏感性：单独屏蔽位置、距离、方位或速度分量时，30-episode 诊断均值变化很小。",
            "2. 屏蔽 comm_reachable/target_node_flag 时，在 radius=4 和 radius=8 下均出现小幅成功率下降和碰撞率上升，是当前诊断里最一致的退化项。",
            "3. 屏蔽全部 edge feature 后没有出现灾难性退化，说明 actor 仍可从 node feature、adjacency mask 和局部观测中获得冗余信息。",
            "4. 因此，本文主证据仍应使用训练期消融表；本实验只作为评估时机制诊断，说明边特征分量并非唯一信息来源。",
            "```",
            "",
            "论文使用边界：",
            "",
            "```text",
            "可以写：评估时边特征屏蔽显示出弱敏感性，其中通信/目标标记分量的退化最一致；这支持对 edge-aware 表示的机制讨论。",
            "谨慎写：该结果不是独立训练的结构消融，且 node feature/adjacency/local observation 存在冗余，不能单独证明某一类边特征在训练机制上必然最优。",
            "```",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate EA-RG-MAPPO-S with evaluation-time edge feature ablations.")
    parser.add_argument("--episodes", type=int, default=100)
    parser.add_argument("--target-policy", default="mixed")
    parser.add_argument("--target-speed", type=float, default=0.75)
    parser.add_argument("--radii", type=float, nargs="+", default=[4.0, 8.0])
    parser.add_argument("--ablations", nargs="+", default=list(EDGE_GROUPS.keys()), choices=list(EDGE_GROUPS.keys()))
    parser.add_argument("--out-csv", type=Path, default=Path("results/edge_feature_ablation_eval.csv"))
    parser.add_argument("--summary-csv", type=Path, default=Path("results/edge_feature_ablation_summary.csv"))
    parser.add_argument("--notes-md", type=Path, default=Path("results/edge_feature_ablation_notes.md"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = []
    for run in FINAL_EA_RG_RUNS:
        model_path = ROOT / run["model"]
        agent = make_agent(model_path)
        for radius in args.radii:
            for ablation in args.ablations:
                row = evaluate_ablation(
                    agent=agent,
                    run=run,
                    episodes=args.episodes,
                    target_policy=args.target_policy,
                    target_speed=args.target_speed,
                    communication_radius=radius,
                    ablation_name=ablation,
                    zero_dims=EDGE_GROUPS[ablation],
                )
                rows.append(row)
                print(row, flush=True)
                write_csv(rows, args.out_csv)
    summary = summarize(rows)
    write_csv(summary, args.summary_csv)
    write_markdown(summary, args.notes_md)
    print(f"saved: {args.out_csv}")
    print(f"saved: {args.summary_csv}")
    print(f"saved: {args.notes_md}")


if __name__ == "__main__":
    main()
