from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import (
    RIGMAPPOAgent,
    RIGMAPPOConfig,
    load_matching_state_dict,
    make_env,
    stack_graphs,
)


def angle_diff(target: float, source: float) -> float:
    return (target - source + math.pi) % (2 * math.pi) - math.pi


def action_index(turn: int, climb: int, accel: int) -> int:
    return (turn + 1) * 9 + (climb + 1) * 3 + (accel + 1)


def geometric_policy(env) -> np.ndarray:
    actions = []
    target = env.red_pos[0]
    for i in range(env.config.num_blue):
        rel = target - env.blue_pos[i]
        desired_heading = math.atan2(float(rel[1]), float(rel[0]))
        heading_error = angle_diff(desired_heading, float(env.blue_heading[i]))
        turn = -1 if heading_error < -0.05 else 1 if heading_error > 0.05 else 0

        desired_gamma = math.atan2(float(rel[2]), float(np.linalg.norm(rel[:2]) + 1e-6))
        gamma_error = desired_gamma - float(env.blue_gamma[i])
        climb = -1 if gamma_error < -0.02 else 1 if gamma_error > 0.02 else 0

        dist = float(np.linalg.norm(rel))
        accel = 1 if dist > 5_500.0 else -1 if dist < 2_000.0 else 0
        actions.append(action_index(turn, climb, accel))
    return np.asarray(actions, dtype=np.int64)


def build_config(args: argparse.Namespace) -> RIGMAPPOConfig:
    return RIGMAPPOConfig(
        env_name="3d_intercept",
        seed=args.seed,
        target_policy=args.target_policy,
        communication_dropout_prob=args.communication_dropout_prob,
        message_delay_steps=args.message_delay_steps,
        radar_dropout_prob=args.radar_dropout_prob,
        strict_target_sensing=args.strict_target_sensing,
        max_target_message_age_steps=args.max_target_message_age_steps,
        min_target_confidence=args.min_target_confidence,
        graph_encoder=args.graph_encoder,
        graph_relation_ablation=args.graph_relation_ablation,
        graph_message_ablation=args.graph_message_ablation,
        graph_input_ablation=args.graph_input_ablation,
        device=args.device,
    )


def build_agent(cfg: RIGMAPPOConfig, args: argparse.Namespace) -> RIGMAPPOAgent:
    env = make_env(cfg, args.seed, training=False)
    _, share_obs, graph = env.reset()
    return RIGMAPPOAgent(
        obs_dim=env.obs_dim,
        node_feat_dim=graph["node_feat"].shape[-1],
        edge_feat_dim=graph["edge_feat"].shape[-1],
        share_obs_dim=share_obs.shape[-1],
        action_dim=env.action_dim,
        num_agents=env.num_agents,
        num_roles=max(4, int(np.max(graph["role"])) + 1),
        hidden_dim=args.hidden_dim,
        role_dim=args.role_dim,
        intent_dim=args.intent_dim,
        graph_encoder=args.graph_encoder,
        graph_message_ablation=args.graph_message_ablation,
        graph_input_ablation=args.graph_input_ablation,
        use_intent_context=False,
    )


def collect_demonstrations(cfg: RIGMAPPOConfig, args: argparse.Namespace) -> dict[str, np.ndarray]:
    obs_rows, share_rows, node_rows, edge_rows, role_rows, adj_rows, relation_adj_rows, intent_rows, action_rows = [], [], [], [], [], [], [], [], []
    successes = 0
    for ep in range(args.episodes):
        env = make_env(cfg, args.seed + ep, training=False)
        obs, share_obs, graph = env.reset()
        while True:
            actions = geometric_policy(env)
            g = stack_graphs([graph])
            obs_rows.append(obs.copy())
            share_rows.append(share_obs.copy())
            node_rows.append(g["node_feat"][0].copy())
            edge_rows.append(g["edge_feat"][0].copy())
            role_rows.append(g["role"][0].copy())
            adj_rows.append(g["adj"][0].copy())
            relation_adj_rows.append(g["relation_adj"][0].copy())
            intent_rows.append(g["intent_label"][0].copy())
            action_rows.append(actions.copy())
            obs, share_obs, graph, _, dones, info = env.step(actions)
            if np.all(dones):
                successes += int(info["success"] > 0.5)
                break
    return {
        "obs": np.asarray(obs_rows, dtype=np.float32),
        "share_obs": np.asarray(share_rows, dtype=np.float32),
        "node_feat": np.asarray(node_rows, dtype=np.float32),
        "edge_feat": np.asarray(edge_rows, dtype=np.float32),
        "role": np.asarray(role_rows, dtype=np.int64),
        "adj": np.asarray(adj_rows, dtype=np.float32),
        "relation_adj": np.asarray(relation_adj_rows, dtype=np.float32),
        "intent_label": np.asarray(intent_rows, dtype=np.int64),
        "action": np.asarray(action_rows, dtype=np.int64),
        "demo_success_rate": np.asarray([successes / max(1, args.episodes)], dtype=np.float32),
    }


def train_bc(agent: RIGMAPPOAgent, data: dict[str, np.ndarray], args: argparse.Namespace) -> list[dict[str, float | int]]:
    device = torch.device(args.device)
    agent.to(device)
    optimizer = torch.optim.Adam(agent.parameters(), lr=args.lr)
    n = data["obs"].shape[0]
    indices = np.arange(n)
    class_weight = None
    if args.balanced_loss:
        counts = np.bincount(data["action"].reshape(-1), minlength=agent.actor.policy_head[-1].out_features).astype(np.float32)
        weights = np.zeros_like(counts)
        nonzero = counts > 0
        weights[nonzero] = counts[nonzero].sum() / (float(np.sum(nonzero)) * counts[nonzero])
        weights = np.clip(weights, 0.0, args.max_class_weight)
        class_weight = torch.as_tensor(weights, dtype=torch.float32, device=device)
    logs: list[dict[str, float | int]] = []
    for epoch in range(1, args.epochs + 1):
        np.random.default_rng(args.seed + epoch).shuffle(indices)
        losses, correct, total = [], 0, 0
        for start in range(0, n, args.batch_size):
            batch_idx = indices[start : start + args.batch_size]
            obs = torch.as_tensor(data["obs"][batch_idx], dtype=torch.float32, device=device)
            node = torch.as_tensor(data["node_feat"][batch_idx], dtype=torch.float32, device=device)
            edge = torch.as_tensor(data["edge_feat"][batch_idx], dtype=torch.float32, device=device)
            role = torch.as_tensor(data["role"][batch_idx], dtype=torch.long, device=device)
            adj = torch.as_tensor(data["adj"][batch_idx], dtype=torch.float32, device=device)
            relation_adj = torch.as_tensor(data["relation_adj"][batch_idx], dtype=torch.float32, device=device)
            actions = torch.as_tensor(data["action"][batch_idx], dtype=torch.long, device=device)
            intent = torch.as_tensor(data["intent_label"][batch_idx], dtype=torch.long, device=device)

            logits, _, _ = agent.actor(
                obs,
                node,
                edge,
                role,
                adj,
                agent.num_agents,
                relation_adj=relation_adj,
                intent_label=intent,
            )
            loss = F.cross_entropy(logits.reshape(-1, logits.shape[-1]), actions.reshape(-1), weight=class_weight)
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(agent.parameters(), args.max_grad_norm)
            optimizer.step()

            with torch.no_grad():
                pred = logits.argmax(dim=-1)
                correct += int((pred == actions).sum().item())
                total += int(actions.numel())
            losses.append(float(loss.item()))
        logs.append(
            {
                "epoch": epoch,
                "loss": float(np.mean(losses)),
                "action_accuracy": float(correct / max(1, total)),
                "samples": int(n),
                "demo_success_rate": float(data["demo_success_rate"][0]),
                "balanced_loss": int(args.balanced_loss),
            }
        )
        print(logs[-1], flush=True)
    return logs


def write_log(rows: list[dict[str, float | int]], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "bc_train_log.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=int, default=50)
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--role-dim", type=int, default=8)
    parser.add_argument("--intent-dim", type=int, default=8)
    parser.add_argument("--graph-encoder", choices=("no_graph", "single", "multi_relation"), default="single")
    parser.add_argument("--graph-relation-ablation", choices=("none", "no_task_support"), default="none")
    parser.add_argument("--graph-message-ablation", choices=("none", "no_role_pair_gate"), default="none")
    parser.add_argument("--graph-input-ablation", choices=("none", "no_edge_features", "no_role_identity"), default="none")
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--max-grad-norm", type=float, default=1.0)
    parser.add_argument("--no-balanced-loss", dest="balanced_loss", action="store_false")
    parser.add_argument("--max-class-weight", type=float, default=10.0)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--target-policy", type=str, default="straight")
    parser.add_argument("--communication-dropout-prob", type=float, default=0.0)
    parser.add_argument("--message-delay-steps", type=int, default=0)
    parser.add_argument("--radar-dropout-prob", type=float, default=0.0)
    parser.add_argument("--strict-target-sensing", action="store_true")
    parser.add_argument("--max-target-message-age-steps", type=int, default=80)
    parser.add_argument("--min-target-confidence", type=float, default=0.2)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--resume", type=Path, default=None)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "results" / "ri_gmappo_3d_bc_straight")
    args = parser.parse_args()

    cfg = build_config(args)
    data = collect_demonstrations(cfg, args)
    agent = build_agent(cfg, args)
    if args.resume is not None:
        load_matching_state_dict(agent, str(args.resume), torch.device(args.device))
    logs = train_bc(agent, data, args)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    torch.save(agent.state_dict(), args.out_dir / "actor_critic_latest.pt")
    torch.save(agent.state_dict(), args.out_dir / "actor_critic_best.pt")
    write_log(logs, args.out_dir)
    print(f"saved: {args.out_dir / 'actor_critic_latest.pt'}")


if __name__ == "__main__":
    main()
