from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import make_env, set_seed  # noqa: E402
from envs.uav_intercept_3d_env import ROLE_ATTACKER  # noqa: E402
from scripts.pretrain_ri_gmappo_3d_bc import build_config, collect_demonstrations  # noqa: E402
from scripts.train_happo_baseline import HAPPOBaselineAgent  # noqa: E402


def build_happo_agent(args: argparse.Namespace) -> HAPPOBaselineAgent:
    cfg = build_config(args)
    env = make_env(cfg, args.seed, training=False)
    _, share_obs, graph = env.reset()
    return HAPPOBaselineAgent(
        obs_dim=env.obs_dim,
        node_feat_dim=graph["node_feat"].shape[-1],
        edge_feat_dim=graph["edge_feat"].shape[-1],
        share_obs_dim=share_obs.shape[-1],
        action_dim=env.action_dim,
        num_agents=env.num_agents,
        num_roles=max(5, int(np.max(graph["role"])) + 1),
        hidden_dim=args.hidden_dim,
        role_dim=args.role_dim,
        intent_dim=args.intent_dim,
    )


def train_happo_bc(
    agent: HAPPOBaselineAgent,
    data: dict[str, np.ndarray],
    args: argparse.Namespace,
) -> list[dict[str, float | int | str]]:
    device = torch.device(args.device)
    agent.to(device)
    actor_params = [param for policy in agent.policies for param in policy.actor.parameters()]
    optimizer = torch.optim.Adam(actor_params, lr=args.lr)
    n = data["obs"].shape[0]
    indices = np.arange(n)
    action_dim = agent.policies[0].actor.policy_head[-1].out_features
    class_weight = None
    if args.balanced_loss:
        counts = np.bincount(data["action"].reshape(-1), minlength=action_dim).astype(np.float32)
        weights = np.zeros_like(counts)
        nonzero = counts > 0
        weights[nonzero] = counts[nonzero].sum() / (float(np.sum(nonzero)) * counts[nonzero])
        weights = np.clip(weights, 0.0, args.max_class_weight)
        class_weight = torch.as_tensor(weights, dtype=torch.float32, device=device)

    logs: list[dict[str, float | int | str]] = []
    for epoch in range(1, args.epochs + 1):
        np.random.default_rng(args.seed + epoch).shuffle(indices)
        losses: list[float] = []
        correct = total = 0
        attacker_correct = attacker_total = 0
        support_correct = support_total = 0
        for start in range(0, n, args.batch_size):
            batch_idx = indices[start : start + args.batch_size]
            obs = torch.as_tensor(data["obs"][batch_idx], dtype=torch.float32, device=device)
            node = torch.as_tensor(data["node_feat"][batch_idx], dtype=torch.float32, device=device)
            edge = torch.as_tensor(data["edge_feat"][batch_idx], dtype=torch.float32, device=device)
            role = torch.as_tensor(data["role"][batch_idx], dtype=torch.long, device=device)
            adj = torch.as_tensor(data["adj"][batch_idx], dtype=torch.float32, device=device)
            relation_adj = torch.as_tensor(data["relation_adj"][batch_idx], dtype=torch.float32, device=device)
            actions = torch.as_tensor(data["action"][batch_idx], dtype=torch.long, device=device)
            blue_roles = role[:, : agent.num_agents]

            per_agent_losses = []
            all_pred = []
            for agent_id, policy in enumerate(agent.policies):
                logits, _, _ = policy.actor(
                    obs,
                    node,
                    edge,
                    role,
                    adj,
                    agent.num_agents,
                    relation_adj=relation_adj,
                )
                agent_logits = logits[:, agent_id]
                agent_actions = actions[:, agent_id]
                per_sample_loss = F.cross_entropy(
                    agent_logits,
                    agent_actions,
                    weight=class_weight,
                    reduction="none",
                )
                if args.attacker_action_weight != 1.0:
                    weight = torch.where(
                        blue_roles[:, agent_id] == ROLE_ATTACKER,
                        torch.full_like(per_sample_loss, float(args.attacker_action_weight)),
                        torch.ones_like(per_sample_loss),
                    )
                    per_sample_loss = per_sample_loss * weight
                per_agent_losses.append(per_sample_loss.mean())
                all_pred.append(agent_logits.argmax(dim=-1))

            loss = torch.stack(per_agent_losses).mean()
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(actor_params, args.max_grad_norm)
            optimizer.step()
            losses.append(float(loss.item()))

            with torch.no_grad():
                pred = torch.stack(all_pred, dim=1)
                correct_mask = pred == actions
                correct += int(correct_mask.sum().item())
                total += int(actions.numel())
                attacker_mask = blue_roles == ROLE_ATTACKER
                support_mask = ~attacker_mask
                attacker_correct += int(correct_mask[attacker_mask].sum().item())
                attacker_total += int(attacker_mask.sum().item())
                support_correct += int(correct_mask[support_mask].sum().item())
                support_total += int(support_mask.sum().item())

        row = {
            "epoch": epoch,
            "loss": float(np.mean(losses)),
            "action_accuracy": float(correct / max(1, total)),
            "attacker_action_accuracy": float(attacker_correct / max(1, attacker_total)),
            "support_action_accuracy": float(support_correct / max(1, support_total)),
            "samples": int(n),
            "demo_success_rate": float(data["demo_success_rate"][0]),
            "balanced_loss": int(args.balanced_loss),
            "geometric_policy_mode": args.geometric_policy_mode,
            "attacker_action_weight": float(args.attacker_action_weight),
        }
        logs.append(row)
        print(row, flush=True)
    return logs


def write_log(rows: list[dict[str, float | int | str]], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "bc_train_log.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Behavior-clone the no-graph HAPPO external baseline.")
    parser.add_argument("--episodes", type=int, default=50)
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--role-dim", type=int, default=8)
    parser.add_argument("--intent-dim", type=int, default=8)
    parser.add_argument("--graph-encoder", choices=("no_graph",), default="no_graph")
    parser.add_argument("--graph-relation-ablation", choices=("none",), default="none")
    parser.add_argument("--graph-message-ablation", choices=("none",), default="none")
    parser.add_argument("--graph-input-ablation", choices=("none",), default="none")
    parser.add_argument("--multi-relation-global-residual-weight", type=float, default=1.0)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--max-grad-norm", type=float, default=1.0)
    parser.add_argument("--no-balanced-loss", dest="balanced_loss", action="store_false")
    parser.add_argument("--max-class-weight", type=float, default=10.0)
    parser.add_argument("--attacker-action-weight", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--target-policy", type=str, default="straight")
    parser.add_argument("--geometric-policy-mode", choices=("direct", "lead", "offset"), default="direct")
    parser.add_argument("--communication-dropout-prob", type=float, default=0.0)
    parser.add_argument("--message-delay-steps", type=int, default=0)
    parser.add_argument("--radar-dropout-prob", type=float, default=0.0)
    parser.add_argument("--strict-target-sensing", action="store_true")
    parser.add_argument("--agent-target-info-bottleneck", action="store_true")
    parser.add_argument("--max-target-message-age-steps", type=int, default=80)
    parser.add_argument("--min-target-confidence", type=float, default=0.2)
    parser.add_argument("--failed-blue-agent", type=int, default=-1)
    parser.add_argument("--node-failure-start-step", type=int, default=0)
    parser.add_argument("--node-failure-start-random-min", type=int, default=None)
    parser.add_argument("--node-failure-start-random-max", type=int, default=None)
    parser.add_argument("--node-failure-duration-steps", type=int, default=0)
    parser.add_argument("--node-failure-duration-random-min", type=int, default=None)
    parser.add_argument("--node-failure-duration-random-max", type=int, default=None)
    parser.add_argument("--min-success-step", type=int, default=0)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "results" / "happo_3d_bc")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    set_seed(args.seed)
    cfg = build_config(args)
    data = collect_demonstrations(cfg, args)
    agent = build_happo_agent(args)
    logs = train_happo_bc(agent, data, args)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    torch.save(agent.state_dict(), args.out_dir / "happo_bc_latest.pt")
    torch.save(agent.state_dict(), args.out_dir / "happo_bc_best.pt")
    write_log(logs, args.out_dir)
    print(f"saved: {args.out_dir / 'happo_bc_latest.pt'}")


if __name__ == "__main__":
    main()
