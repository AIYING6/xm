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

from algorithms.ri_gmappo.simple_ri_gmappo import (
    RIGMAPPOAgent,
    RIGMAPPOConfig,
    load_matching_state_dict,
    make_env,
    stack_graphs,
)


CSV_COLUMNS = (
    "method",
    "checkpoint",
    "policy_source",
    "seed",
    "episode",
    "episodes",
    "target_policy",
    "strict_target_sensing",
    "agent_target_info_bottleneck",
    "target_prior_position",
    "max_target_message_age_steps",
    "min_target_confidence",
    "communication_range_scale",
    "communication_dropout_prob",
    "message_delay_steps",
    "radar_dropout_prob",
    "failed_blue_agent",
    "node_failure_start_step",
    "node_failure_duration_steps",
    "min_success_step",
    "graph_relation_ablation",
    "graph_message_ablation",
    "graph_input_ablation",
    "deterministic",
    "success",
    "chain_closed",
    "attack_window_formed",
    "attack_window_rate",
    "tracking_rate",
    "comm_connectivity",
    "mean_message_age",
    "collision",
    "timeout",
    "constraint_violation",
    "steps",
    "first_attack_window_step",
    "first_chain_close_step",
    "post_failure_chain_recovered",
    "post_failure_chain_recovery_steps",
    "post_failure_chain_recovery_steps_censored",
    "post_failure_chain_recovered_only_steps",
    "post_failure_chain_maintained",
    "post_failure_chain_recovered_after_loss",
    "post_failure_chain_unrecovered",
    "post_failure_fresh_info_recovered",
    "post_failure_fresh_info_recovery_steps",
    "post_failure_fresh_info_acquired_without_prior_loss",
    "post_failure_fresh_direct_recovered",
    "post_failure_fresh_comm_recovered",
    "post_failure_post_delivered_old_info_recovered",
    "post_failure_stale_cache_recovered",
    "post_failure_first_chain_step",
    "chain_closed_during_failure_rate",
    "tracking_during_failure_rate",
    "connectivity_during_failure",
    "avg_mean_range",
    "final_mean_range",
    "episode_min_blue_red_distance",
    "episode_min_blue_blue_distance",
    "final_min_blue_red_distance",
    "final_min_blue_blue_distance",
    "reward_sum",
)


def infer_agent_dims(checkpoint: dict[str, torch.Tensor] | None, args: argparse.Namespace) -> tuple[int, int, int, int | None]:
    if checkpoint is None:
        return args.hidden_dim, args.role_dim, args.intent_dim, None
    hidden_dim = int(checkpoint.get("critic.net.0.weight", torch.empty(args.hidden_dim, 1)).shape[0])
    role_tensor = checkpoint.get("actor.role_emb.weight")
    intent_tensor = checkpoint.get("actor.intent_emb.weight")
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
        attack_hold_steps=args.attack_hold_steps,
        min_success_step=args.min_success_step,
        graph_relation_ablation=args.graph_relation_ablation,
        graph_encoder=args.graph_encoder,
        graph_message_ablation=args.graph_message_ablation,
        graph_input_ablation=args.graph_input_ablation,
        multi_relation_global_residual_weight=getattr(args, "multi_relation_global_residual_weight", 1.0),
        device=args.device,
    )


def build_agent(args: argparse.Namespace, cfg: RIGMAPPOConfig) -> tuple[RIGMAPPOAgent, str]:
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
    hidden_dim, role_dim, intent_dim, checkpoint_roles = infer_agent_dims(checkpoint, args)
    env_roles = int(np.max(graph["role"])) + 1
    num_roles = max(env_roles, checkpoint_roles or env_roles)

    agent = RIGMAPPOAgent(
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
        graph_encoder=args.graph_encoder,
        graph_message_ablation=args.graph_message_ablation,
        graph_input_ablation=args.graph_input_ablation,
        multi_relation_global_residual_weight=getattr(args, "multi_relation_global_residual_weight", 1.0),
        use_intent_context=False,
    )
    if checkpoint is not None:
        load_matching_state_dict(agent, str(args.checkpoint), torch.device(args.device))
    agent.eval()
    return agent, policy_source


def mean_metric(step_infos: list[dict[str, float]], key: str) -> float:
    return float(np.mean([float(info[key]) for info in step_infos])) if step_infos else 0.0


def first_step_where(step_infos: list[dict[str, float]], key: str, threshold: float = 0.0) -> float:
    for info in step_infos:
        if float(info.get(key, 0.0)) > threshold:
            return float(info["step"])
    return -1.0


def mean_metric_where(
    step_infos: list[dict[str, float]],
    key: str,
    mask_key: str,
    threshold: float = 0.0,
    empty_value: float = -1.0,
) -> float:
    values = [float(info[key]) for info in step_infos if float(info.get(mask_key, 0.0)) > threshold]
    return float(np.mean(values)) if values else empty_value


def post_failure_recovery_metrics(step_infos: list[dict[str, float]], args: argparse.Namespace) -> dict[str, float]:
    if args.failed_blue_agent < 0 or args.node_failure_duration_steps <= 0:
        return {
            "post_failure_chain_recovered": -1.0,
            "post_failure_chain_recovery_steps": -1.0,
            "post_failure_chain_recovery_steps_censored": -1.0,
            "post_failure_chain_recovered_only_steps": -1.0,
            "post_failure_chain_maintained": -1.0,
            "post_failure_chain_recovered_after_loss": -1.0,
            "post_failure_chain_unrecovered": -1.0,
            "post_failure_fresh_info_recovered": -1.0,
            "post_failure_fresh_info_recovery_steps": -1.0,
            "post_failure_fresh_info_acquired_without_prior_loss": -1.0,
            "post_failure_fresh_direct_recovered": -1.0,
            "post_failure_fresh_comm_recovered": -1.0,
            "post_failure_post_delivered_old_info_recovered": -1.0,
            "post_failure_stale_cache_recovered": -1.0,
            "post_failure_first_chain_step": -1.0,
            "chain_closed_during_failure_rate": -1.0,
            "tracking_during_failure_rate": -1.0,
            "connectivity_during_failure": -1.0,
        }
    start = float(args.node_failure_start_step)
    first_chain_step = -1.0
    chain_at_failure_start = False
    for info in step_infos:
        step = float(info["step"])
        chain_closed = float(info.get("chain_closed", 0.0)) > 0.5
        if step == start and chain_closed:
            chain_at_failure_start = True
        if step >= start and chain_closed:
            first_chain_step = step
            break
    final_step = float(step_infos[-1]["step"]) if step_infos else start
    hold_steps = max(1.0, float(getattr(args, "attack_hold_steps", 1)))
    stable_window_start = max(start, first_chain_step - hold_steps + 1.0) if first_chain_step >= 0.0 else -1.0
    recovered = float(first_chain_step >= 0.0)
    recovery_steps = stable_window_start - start if recovered > 0.5 else max(0.0, final_step - start)
    recovered_only_steps = recovery_steps if recovered > 0.5 else -1.0
    maintained = float(chain_at_failure_start)
    recovered_after_loss = float(recovered > 0.5 and not chain_at_failure_start)
    unrecovered = float(recovered <= 0.5)

    def has_chain_loss_before(window_start: float) -> bool:
        for item in step_infos:
            step = float(item["step"])
            if start <= step < window_start and float(item.get("chain_closed", 0.0)) <= 0.5:
                return True
        return not chain_at_failure_start

    def fresh_closure(item: dict[str, float]) -> bool:
        return (
            float(item.get("attacker_info_attack_window", 0.0)) > 0.5
            and float(item.get("attacker_window_cache_generation_step_max", -1.0)) >= start
        )

    def post_delivered_old_closure(item: dict[str, float]) -> bool:
        return (
            float(item.get("attacker_info_attack_window", 0.0)) > 0.5
            and 0.0 <= float(item.get("attacker_window_cache_generation_step_max", -1.0)) < start
            and float(item.get("attacker_window_cache_delivery_step_max", -1.0)) >= start
        )

    fresh_rec_end = -1.0
    fresh_window: list[dict[str, float]] = []
    old_delivered_rec_end = -1.0
    for end_idx, info in enumerate(step_infos):
        step = float(info["step"])
        if step < start + hold_steps - 1.0:
            continue
        window = step_infos[max(0, end_idx - int(hold_steps) + 1) : end_idx + 1]
        if len(window) < int(hold_steps):
            continue
        window_start = float(window[0]["step"])
        if window_start < start:
            continue
        if fresh_rec_end < 0.0 and all(fresh_closure(item) for item in window):
            fresh_rec_end = step
            fresh_window = window
        if old_delivered_rec_end < 0.0 and all(post_delivered_old_closure(item) for item in window):
            old_delivered_rec_end = step
        if fresh_rec_end >= 0.0 and old_delivered_rec_end >= 0.0:
            break

    fresh_window_start = fresh_rec_end - hold_steps + 1.0 if fresh_rec_end >= 0.0 else -1.0
    fresh_after_loss = float(fresh_rec_end >= 0.0 and has_chain_loss_before(fresh_window_start))
    fresh_without_prior_loss = float(fresh_rec_end >= 0.0 and not has_chain_loss_before(fresh_window_start))
    fresh_info_recovery_steps = fresh_window_start - start if fresh_after_loss > 0.5 else -1.0
    fresh_direct = float(
        fresh_after_loss > 0.5
        and any(
            float(item.get("attacker_window_direct_info", 0.0)) > 0.5
            and float(item.get("attacker_window_cache_generation_step_max", -1.0)) >= start
            for item in fresh_window
        )
    )
    fresh_comm = float(
        fresh_after_loss > 0.5
        and any(
            float(item.get("attacker_window_comm_info", 0.0)) > 0.5
            and float(item.get("attacker_window_cache_generation_step_max", -1.0)) >= start
            and float(item.get("attacker_window_cache_delivery_step_max", -1.0)) >= start
            for item in fresh_window
        )
    )
    old_delivered_window_start = old_delivered_rec_end - hold_steps + 1.0 if old_delivered_rec_end >= 0.0 else -1.0
    old_delivered_recovered = float(
        old_delivered_rec_end >= 0.0 and has_chain_loss_before(old_delivered_window_start)
    )
    stale_cache_recovered = float(
        recovered_after_loss > 0.5
        and fresh_after_loss <= 0.5
        and old_delivered_recovered <= 0.5
    )
    return {
        "post_failure_chain_recovered": recovered,
        "post_failure_chain_recovery_steps": float(recovery_steps),
        "post_failure_chain_recovery_steps_censored": float(recovery_steps),
        "post_failure_chain_recovered_only_steps": float(recovered_only_steps),
        "post_failure_chain_maintained": maintained,
        "post_failure_chain_recovered_after_loss": recovered_after_loss,
        "post_failure_chain_unrecovered": unrecovered,
        "post_failure_fresh_info_recovered": fresh_after_loss,
        "post_failure_fresh_info_recovery_steps": float(fresh_info_recovery_steps),
        "post_failure_fresh_info_acquired_without_prior_loss": fresh_without_prior_loss,
        "post_failure_fresh_direct_recovered": fresh_direct,
        "post_failure_fresh_comm_recovered": fresh_comm,
        "post_failure_post_delivered_old_info_recovered": old_delivered_recovered,
        "post_failure_stale_cache_recovered": stale_cache_recovered,
        "post_failure_first_chain_step": float(first_chain_step),
        "chain_closed_during_failure_rate": mean_metric_where(
            step_infos, "chain_closed", "node_failure_active", empty_value=0.0
        ),
        "tracking_during_failure_rate": mean_metric_where(
            step_infos, "tracking_rate", "node_failure_active", empty_value=0.0
        ),
        "connectivity_during_failure": mean_metric_where(
            step_infos, "comm_connectivity", "node_failure_active", empty_value=0.0
        ),
    }


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def build_episode_row(
    args: argparse.Namespace,
    policy_source: str,
    seed: int,
    episode: int,
    step_infos: list[dict[str, float]],
    final: dict[str, float],
    reward_sum: float,
) -> dict[str, float | int | str | bool]:
    recovery = post_failure_recovery_metrics(step_infos, args)
    return {
        "method": "EA-RG-MAPPO-S",
        "checkpoint": display_path(args.checkpoint),
        "policy_source": policy_source,
        "seed": seed,
        "episode": episode,
        "episodes": args.episodes,
        "target_policy": args.target_policy,
        "strict_target_sensing": args.strict_target_sensing,
        "agent_target_info_bottleneck": args.agent_target_info_bottleneck,
        "target_prior_position": ";".join(f"{float(x):.6g}" for x in args.target_prior_position),
        "max_target_message_age_steps": args.max_target_message_age_steps,
        "min_target_confidence": args.min_target_confidence,
        "communication_range_scale": args.communication_range_scale,
        "communication_dropout_prob": args.communication_dropout_prob,
        "message_delay_steps": args.message_delay_steps,
        "radar_dropout_prob": args.radar_dropout_prob,
        "failed_blue_agent": args.failed_blue_agent,
        "node_failure_start_step": args.node_failure_start_step,
        "node_failure_duration_steps": args.node_failure_duration_steps,
        "min_success_step": args.min_success_step,
        "graph_relation_ablation": args.graph_relation_ablation,
        "graph_message_ablation": args.graph_message_ablation,
        "graph_input_ablation": args.graph_input_ablation,
        "deterministic": not args.stochastic,
        "success": float(final["success"]),
        "chain_closed": float(final["chain_closed"]),
        "attack_window_formed": float(max(info["attack_window_rate"] for info in step_infos) > 0.0),
        "attack_window_rate": mean_metric(step_infos, "attack_window_rate"),
        "tracking_rate": mean_metric(step_infos, "tracking_rate"),
        "comm_connectivity": mean_metric(step_infos, "comm_connectivity"),
        "mean_message_age": mean_metric(step_infos, "mean_message_age"),
        "collision": float(final["collision"]),
        "timeout": float(final["timeout"]),
        "constraint_violation": float(final["constraint_violation"]),
        "steps": float(final["step"]),
        "first_attack_window_step": first_step_where(step_infos, "attack_window_rate"),
        "first_chain_close_step": first_step_where(step_infos, "chain_closed", threshold=0.5),
        **recovery,
        "avg_mean_range": mean_metric(step_infos, "mean_range"),
        "final_mean_range": float(final["mean_range"]),
        "episode_min_blue_red_distance": float(min(info["min_blue_red_distance"] for info in step_infos)),
        "episode_min_blue_blue_distance": float(min(info["min_blue_blue_distance"] for info in step_infos)),
        "final_min_blue_red_distance": float(final["min_blue_red_distance"]),
        "final_min_blue_blue_distance": float(final["min_blue_blue_distance"]),
        "reward_sum": reward_sum,
    }


def evaluate(args: argparse.Namespace) -> list[dict[str, float | int | str | bool]]:
    cfg = build_config(args)
    agent, policy_source = build_agent(args, cfg)
    device = torch.device(args.device)
    rows: list[dict[str, float | int | str | bool]] = []
    eval_batch_size = max(1, int(getattr(args, "eval_batch_size", 1)))

    with torch.no_grad():
        for batch_start in range(0, args.episodes, eval_batch_size):
            batch_episodes = list(range(batch_start, min(args.episodes, batch_start + eval_batch_size)))
            envs = []
            obs_list = []
            share_obs_list = []
            graph_list = []
            step_infos_list: list[list[dict[str, float]]] = []
            reward_sums: list[float] = []
            active: list[bool] = []
            for ep in batch_episodes:
                seed = args.base_seed + ep
                env = make_env(cfg, seed, training=False)
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
                g = stack_graphs([graph_list[i] for i in active_indices])
                actions, _, _, _, _, _, _ = agent.get_action_and_value(
                    torch.as_tensor(np.stack([obs_list[i] for i in active_indices], axis=0), dtype=torch.float32, device=device),
                    torch.as_tensor(g["node_feat"], dtype=torch.float32, device=device),
                    torch.as_tensor(g["edge_feat"], dtype=torch.float32, device=device),
                    torch.as_tensor(g["role"], dtype=torch.long, device=device),
                    torch.as_tensor(g["adj"], dtype=torch.float32, device=device),
                    torch.as_tensor(np.stack([share_obs_list[i] for i in active_indices], axis=0), dtype=torch.float32, device=device),
                    relation_adj=torch.as_tensor(g["relation_adj"], dtype=torch.float32, device=device),
                    deterministic=not args.stochastic,
                    intent_label=torch.as_tensor(g["intent_label"], dtype=torch.long, device=device),
                    detach_intent=False,
                    oracle_intent=False,
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
                        rows.append(
                            build_episode_row(
                                args=args,
                                policy_source=policy_source,
                                seed=args.base_seed + episode,
                                episode=episode,
                                step_infos=step_infos_list[env_i],
                                final=info,
                                reward_sum=reward_sums[env_i],
                            )
                        )
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
        "chain_closed",
        "attack_window_formed",
        "attack_window_rate",
        "tracking_rate",
        "comm_connectivity",
        "mean_message_age",
        "collision",
        "timeout",
        "constraint_violation",
        "steps",
        "first_attack_window_step",
        "first_chain_close_step",
        "post_failure_chain_recovered",
        "post_failure_chain_recovery_steps",
        "post_failure_chain_recovery_steps_censored",
        "post_failure_chain_recovered_only_steps",
        "post_failure_fresh_info_recovered",
        "post_failure_fresh_info_recovery_steps",
        "post_failure_fresh_info_acquired_without_prior_loss",
        "post_failure_fresh_direct_recovered",
        "post_failure_fresh_comm_recovered",
        "post_failure_post_delivered_old_info_recovered",
        "post_failure_stale_cache_recovered",
        "chain_closed_during_failure_rate",
        "tracking_during_failure_rate",
        "connectivity_during_failure",
        "avg_mean_range",
        "episode_min_blue_red_distance",
        "episode_min_blue_blue_distance",
        "final_min_blue_red_distance",
        "final_min_blue_blue_distance",
    )
    lines = [
        "# 3DOF RI-GMAPPO Policy Evaluation",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Purpose:",
        "",
        "```text",
        "Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.",
        "This is a diagnostic artifact until multi-seed 3DOF training is completed.",
        "```",
        "",
        "## Configuration",
        "",
        "```text",
        f"checkpoint = {display_path(args.checkpoint)}",
        f"episodes = {args.episodes}",
        f"target_policy = {args.target_policy}",
        f"communication_range_scale = {args.communication_range_scale}",
        f"communication_dropout_prob = {args.communication_dropout_prob}",
        f"message_delay_steps = {args.message_delay_steps}",
        f"radar_dropout_prob = {args.radar_dropout_prob}",
        f"failed_blue_agent = {args.failed_blue_agent}",
        f"node_failure_start_step = {args.node_failure_start_step}",
        f"node_failure_duration_steps = {args.node_failure_duration_steps}",
        f"graph_relation_ablation = {args.graph_relation_ablation}",
        f"graph_message_ablation = {args.graph_message_ablation}",
        f"graph_input_ablation = {args.graph_input_ablation}",
        f"multi_relation_global_residual_weight = {getattr(args, 'multi_relation_global_residual_weight', 1.0)}",
        f"deterministic = {not args.stochastic}",
        "```",
        "",
        "## Metric Means",
        "",
        "| Metric | Mean |",
        "|---|---:|",
    ]
    for col in metric_cols:
        values = [float(row[col]) for row in rows]
        lines.append(f"| `{col}` | {float(np.mean(values)):.6g} |")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "```text",
            "Do not use this smoke-scale 3DOF policy evaluation as a paper result.",
            "Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.",
            "```",
            "",
        ]
    )
    out_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, default=ROOT / "results" / "ri_gmappo_3d_smoke" / "actor_critic_latest.pt")
    parser.add_argument("--episodes", type=int, default=3)
    parser.add_argument("--eval-batch-size", type=int, default=1)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--base-seed", type=int, default=30_000)
    parser.add_argument("--target-policy", type=str, default="evasive")
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
    parser.add_argument("--min-success-step", type=int, default=0)
    parser.add_argument("--attack-hold-steps", type=int, default=4)
    parser.add_argument("--stochastic", action="store_true")
    parser.add_argument("--allow-random-policy", action="store_true")
    parser.add_argument("--hidden-dim", type=int, default=128)
    parser.add_argument("--role-dim", type=int, default=8)
    parser.add_argument("--intent-dim", type=int, default=8)
    parser.add_argument("--graph-encoder", choices=("no_graph", "single", "multi_relation"), default="single")
    parser.add_argument("--graph-relation-ablation", choices=("none", "no_task_support"), default="none")
    parser.add_argument("--graph-message-ablation", choices=("none", "no_role_pair_gate"), default="none")
    parser.add_argument("--graph-input-ablation", choices=("none", "no_edge_features", "no_role_identity"), default="none")
    parser.add_argument("--multi-relation-global-residual-weight", type=float, default=1.0)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--out-csv", type=Path, default=ROOT / "results" / "intercept_3d_policy_eval.csv")
    parser.add_argument("--summary-md", type=Path, default=ROOT / "docs" / "intercept_3d_policy_eval.md")
    args = parser.parse_args()

    rows = evaluate(args)
    write_csv(rows, args.out_csv)
    write_summary(rows, args.summary_md, args)
    print(args.out_csv)
    print(args.summary_md)
    print(f"episodes: {len(rows)}")


if __name__ == "__main__":
    main()
