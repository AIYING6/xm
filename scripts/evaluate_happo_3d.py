from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import torch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOConfig, make_env, stack_graphs  # noqa: E402
from scripts.evaluate_ri_gmappo_3d import (  # noqa: E402
    CSV_COLUMNS,
    build_episode_row,
    display_path,
    mean_metric,
)
from scripts.train_happo_baseline import HAPPOBaselineAgent  # noqa: E402


def infer_happo_dims(checkpoint: dict[str, torch.Tensor] | None, args: argparse.Namespace) -> tuple[int, int, int, int | None]:
    if checkpoint is None:
        return args.hidden_dim, args.role_dim, args.intent_dim, None
    hidden_tensor = checkpoint.get("policies.0.critic.net.0.weight")
    role_tensor = checkpoint.get("policies.0.actor.role_emb.weight")
    intent_tensor = checkpoint.get("policies.0.actor.intent_emb.weight")
    hidden_dim = int(hidden_tensor.shape[0]) if hidden_tensor is not None else args.hidden_dim
    role_dim = int(role_tensor.shape[1]) if role_tensor is not None else args.role_dim
    intent_dim = int(intent_tensor.shape[1]) if intent_tensor is not None else args.intent_dim
    num_roles = int(role_tensor.shape[0]) if role_tensor is not None else None
    return hidden_dim, role_dim, intent_dim, num_roles


def build_config(args: argparse.Namespace) -> RIGMAPPOConfig:
    return RIGMAPPOConfig(
        env_name="3d_intercept",
        seed=args.seed,
        eval_episodes=args.episodes,
        target_policy=args.target_policy,
        communication_range_scale=args.communication_range_scale,
        communication_dropout_prob=args.communication_dropout_prob,
        message_delay_steps=args.message_delay_steps,
        radar_dropout_prob=args.radar_dropout_prob,
        strict_target_sensing=args.strict_target_sensing,
        agent_target_info_bottleneck=args.agent_target_info_bottleneck,
        target_prior_position=tuple(args.target_prior_position),
        max_target_message_age_steps=args.max_target_message_age_steps,
        min_target_confidence=args.min_target_confidence,
        failed_blue_agent=args.failed_blue_agent,
        node_failure_start_step=args.node_failure_start_step,
        node_failure_duration_steps=args.node_failure_duration_steps,
        graph_encoder="no_graph",
        graph_relation_ablation="none",
        graph_message_ablation="none",
        graph_input_ablation="none",
        device=args.device,
    )


def build_agent(args: argparse.Namespace, cfg: RIGMAPPOConfig) -> tuple[HAPPOBaselineAgent, str]:
    checkpoint = None
    policy_source = "random_untrained"
    if args.checkpoint.exists():
        checkpoint = torch.load(args.checkpoint, map_location=args.device, weights_only=True)
        policy_source = "checkpoint"
    elif not args.allow_random_policy:
        raise FileNotFoundError(
            f"checkpoint not found: {args.checkpoint}. Use --allow-random-policy only for smoke tests."
        )

    env = make_env(cfg, args.seed, training=False)
    _, share_obs, graph = env.reset()
    hidden_dim, role_dim, intent_dim, checkpoint_roles = infer_happo_dims(checkpoint, args)
    env_roles = int(np.max(graph["role"])) + 1
    num_roles = max(env_roles, checkpoint_roles or env_roles)
    agent = HAPPOBaselineAgent(
        obs_dim=env.obs_dim,
        node_feat_dim=graph["node_feat"].shape[-1],
        edge_feat_dim=graph["edge_feat"].shape[-1],
        share_obs_dim=share_obs.shape[-1],
        action_dim=env.action_dim,
        num_agents=env.num_agents,
        num_roles=num_roles,
        hidden_dim=hidden_dim,
        role_dim=role_dim,
        intent_dim=intent_dim,
    )
    if checkpoint is not None:
        agent.load_state_dict(checkpoint)
    agent.to(torch.device(args.device))
    agent.eval()
    return agent, policy_source


def evaluate(args: argparse.Namespace) -> list[dict[str, float | int | str | bool]]:
    cfg = build_config(args)
    agent, policy_source = build_agent(args, cfg)
    device = torch.device(args.device)
    rows: list[dict[str, float | int | str | bool]] = []
    eval_batch_size = max(1, int(getattr(args, "eval_batch_size", 1)))

    with torch.no_grad():
        for batch_start in range(0, args.episodes, eval_batch_size):
            batch_episodes = list(range(batch_start, min(args.episodes, batch_start + eval_batch_size)))
            envs, obs_list, share_obs_list, graph_list = [], [], [], []
            step_infos_list: list[list[dict[str, float]]] = []
            reward_sums: list[float] = []
            active: list[bool] = []
            for ep in batch_episodes:
                env = make_env(cfg, args.base_seed + ep, training=False)
                obs, share_obs, graph = env.reset()
                envs.append(env)
                obs_list.append(obs)
                share_obs_list.append(share_obs)
                graph_list.append(graph)
                step_infos_list.append([])
                reward_sums.append(0.0)
                active.append(True)

            while any(active):
                active_indices = [i for i, is_active in enumerate(active) if is_active]
                graph_batch = stack_graphs([graph_list[i] for i in active_indices])
                actions, _, _, _, _, _ = agent.get_action_and_value(
                    torch.as_tensor(np.stack([obs_list[i] for i in active_indices], axis=0), dtype=torch.float32, device=device),
                    torch.as_tensor(graph_batch["node_feat"], dtype=torch.float32, device=device),
                    torch.as_tensor(graph_batch["edge_feat"], dtype=torch.float32, device=device),
                    torch.as_tensor(graph_batch["role"], dtype=torch.long, device=device),
                    torch.as_tensor(graph_batch["adj"], dtype=torch.float32, device=device),
                    torch.as_tensor(np.stack([share_obs_list[i] for i in active_indices], axis=0), dtype=torch.float32, device=device),
                    relation_adj=torch.as_tensor(graph_batch["relation_adj"], dtype=torch.float32, device=device),
                    deterministic=not args.stochastic,
                )
                action_batch = actions.cpu().numpy()
                for action_i, env_i in enumerate(active_indices):
                    obs, share_obs, graph, rewards, dones, info = envs[env_i].step(action_batch[action_i])
                    reward_sums[env_i] += float(np.sum(rewards))
                    step_infos_list[env_i].append(info)
                    obs_list[env_i] = obs
                    share_obs_list[env_i] = share_obs
                    graph_list[env_i] = graph
                    if np.all(dones):
                        episode = batch_episodes[env_i]
                        row = build_episode_row(
                            args=args,
                            policy_source=policy_source,
                            seed=args.base_seed + episode,
                            episode=episode,
                            step_infos=step_infos_list[env_i],
                            final=info,
                            reward_sum=reward_sums[env_i],
                        )
                        row["method"] = "HAPPO"
                        rows.append(row)
                        active[env_i] = False
    return rows


def write_csv(rows: list[dict[str, float | int | str | bool]], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def write_summary(rows: list[dict[str, float | int | str | bool]], out_md: Path, args: argparse.Namespace) -> None:
    out_md.parent.mkdir(parents=True, exist_ok=True)
    metric_cols = (
        "success",
        "post_failure_chain_recovered",
        "post_failure_chain_recovery_steps",
        "chain_closed_during_failure_rate",
        "tracking_during_failure_rate",
        "connectivity_during_failure",
        "collision",
        "timeout",
        "constraint_violation",
        "steps",
        "avg_mean_range",
        "episode_min_blue_red_distance",
        "episode_min_blue_blue_distance",
    )
    lines = [
        "# 3DOF HAPPO Policy Evaluation",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Configuration",
        "",
        "```text",
        f"checkpoint = {display_path(args.checkpoint)}",
        f"episodes = {args.episodes}",
        f"target_policy = {args.target_policy}",
        f"communication_dropout_prob = {args.communication_dropout_prob}",
        f"failed_blue_agent = {args.failed_blue_agent}",
        f"node_failure_start_step = {args.node_failure_start_step}",
        f"node_failure_duration_steps = {args.node_failure_duration_steps}",
        f"deterministic = {not args.stochastic}",
        "```",
        "",
        "## Metric Means",
        "",
        "| Metric | Mean |",
        "|---|---:|",
    ]
    for col in metric_cols:
        lines.append(f"| `{col}` | {mean_metric(rows, col):.6g} |")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "```text",
            "This evaluates the no-graph HAPPO-style external baseline.",
            "Use paper-facing claims only after checkpoint-sweep selection is connected.",
            "```",
            "",
        ]
    )
    out_md.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a saved 3DOF HAPPO baseline checkpoint.")
    parser.add_argument("--checkpoint", type=Path, default=ROOT / "results" / "happo_baseline_smoke" / "happo_latest.pt")
    parser.add_argument("--episodes", type=int, default=3)
    parser.add_argument("--eval-batch-size", type=int, default=1)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--base-seed", type=int, default=30_000)
    parser.add_argument("--target-policy", type=str, default="straight")
    parser.add_argument("--communication-range-scale", type=float, default=1.0)
    parser.add_argument("--communication-dropout-prob", type=float, default=0.0)
    parser.add_argument("--message-delay-steps", type=int, default=0)
    parser.add_argument("--radar-dropout-prob", type=float, default=0.0)
    parser.add_argument("--strict-target-sensing", action="store_true")
    parser.add_argument("--agent-target-info-bottleneck", action="store_true")
    parser.add_argument("--target-prior-position", type=float, nargs=3, default=(10_000.0, 0.0, 5_000.0))
    parser.add_argument("--max-target-message-age-steps", type=int, default=80)
    parser.add_argument("--min-target-confidence", type=float, default=0.2)
    parser.add_argument("--failed-blue-agent", type=int, default=-1)
    parser.add_argument("--node-failure-start-step", type=int, default=0)
    parser.add_argument("--node-failure-duration-steps", type=int, default=0)
    parser.add_argument("--stochastic", action="store_true")
    parser.add_argument("--allow-random-policy", action="store_true")
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--role-dim", type=int, default=8)
    parser.add_argument("--intent-dim", type=int, default=8)
    parser.add_argument("--graph-relation-ablation", choices=("none",), default="none")
    parser.add_argument("--graph-message-ablation", choices=("none",), default="none")
    parser.add_argument("--graph-input-ablation", choices=("none",), default="none")
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--out-csv", type=Path, default=ROOT / "results" / "happo_3d_policy_eval.csv")
    parser.add_argument("--summary-md", type=Path, default=ROOT / "docs" / "happo_3d_policy_eval.md")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = evaluate(args)
    write_csv(rows, args.out_csv)
    write_summary(rows, args.summary_md, args)
    print(args.out_csv)
    print(args.summary_md)
    print(f"episodes: {len(rows)}")


if __name__ == "__main__":
    main()
