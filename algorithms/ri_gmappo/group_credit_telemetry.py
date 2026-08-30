"""Read-only failure-group credit-assignment telemetry for DRTP B5.

The functions in this module never call ``backward`` or ``optimizer.step`` and
never write to parameter ``.grad`` buffers.  They summarize a frozen rollout
immediately before the ordinary PPO update.  Training seed remains the
independent unit; update/group rows are technical repeated measurements.
"""

from __future__ import annotations

from itertools import combinations
from typing import Any, Iterable

import numpy as np
import torch

from algorithms.ri_gmappo.drtp_topology_sampler import ALL_GROUPS


GROUP_FIELDS = [
    "update", "group", "status", "graph_count", "agent_sample_count",
    "return_mean", "return_std", "return_q10", "return_q50", "return_q90",
    "rollout_value_mean", "rollout_value_std",
    "value_residual_mean", "value_residual_std", "value_residual_rmse", "value_residual_abs_q90",
    "td_residual_mean", "td_residual_std", "td_residual_abs_q90", "explained_variance",
    "raw_advantage_mean", "raw_advantage_std", "raw_advantage_q10", "raw_advantage_q50", "raw_advantage_q90",
    "normalized_advantage_mean", "normalized_advantage_std", "normalized_advantage_q10",
    "normalized_advantage_q50", "normalized_advantage_q90",
    "policy_entropy_mean", "actor_gradient_norm", "critic_gradient_norm",
    "gradient_objective", "independent_unit", "repetition_unit",
]

CONFLICT_FIELDS = [
    "update", "group_a", "group_b", "status",
    "actor_gradient_dot", "actor_gradient_cosine", "actor_gradient_conflict",
    "critic_gradient_dot", "critic_gradient_cosine", "critic_gradient_conflict",
    "independent_unit", "repetition_unit",
]


def _tensor_stats(values: torch.Tensor, prefix: str) -> dict[str, float]:
    flat = values.detach().reshape(-1).to(dtype=torch.float64)
    if flat.numel() == 0:
        raise ValueError("statistics require at least one value")
    quantiles = torch.quantile(flat, torch.tensor([0.1, 0.5, 0.9], dtype=flat.dtype, device=flat.device))
    return {
        f"{prefix}_mean": float(flat.mean().cpu()),
        f"{prefix}_std": float(flat.std(unbiased=False).cpu()),
        f"{prefix}_q10": float(quantiles[0].cpu()),
        f"{prefix}_q50": float(quantiles[1].cpu()),
        f"{prefix}_q90": float(quantiles[2].cpu()),
    }


def _gradients(loss: torch.Tensor, parameters: list[torch.nn.Parameter]) -> list[torch.Tensor]:
    gradients = torch.autograd.grad(loss, parameters, retain_graph=True, allow_unused=True)
    return [torch.zeros_like(parameter) if gradient is None else gradient.detach() for parameter, gradient in zip(parameters, gradients)]


def _norm(gradients: Iterable[torch.Tensor]) -> float:
    gradient_list = list(gradients)
    if not gradient_list:
        return 0.0
    total = torch.zeros((), dtype=torch.float64, device=gradient_list[0].device)
    for gradient in gradient_list:
        total = total + gradient.to(dtype=torch.float64).square().sum()
    return float(torch.sqrt(total).cpu())


def _pair(left: list[torch.Tensor], right: list[torch.Tensor]) -> tuple[float, float, bool]:
    if not left or not right:
        return 0.0, 0.0, False
    dot = torch.zeros((), dtype=torch.float64, device=left[0].device)
    left_sq = torch.zeros_like(dot)
    right_sq = torch.zeros_like(dot)
    for a, b in zip(left, right):
        a64, b64 = a.to(dtype=torch.float64), b.to(dtype=torch.float64)
        dot = dot + (a64 * b64).sum()
        left_sq = left_sq + a64.square().sum()
        right_sq = right_sq + b64.square().sum()
    left_norm = torch.sqrt(left_sq)
    right_norm = torch.sqrt(right_sq)
    denominator = left_norm * right_norm
    cosine = torch.zeros_like(dot) if float(denominator.cpu()) <= 1e-18 else dot / denominator
    dot_value = float(dot.cpu())
    return dot_value, float(cosine.cpu()), bool(dot_value < 0.0)


def _empty_group_row(update: int, group: str) -> dict[str, Any]:
    row: dict[str, Any] = {field: None for field in GROUP_FIELDS}
    row.update({
        "update": update,
        "group": group,
        "status": "NO_SAMPLES",
        "graph_count": 0,
        "agent_sample_count": 0,
        "gradient_objective": "ppo_policy_entropy_and_value",
        "independent_unit": "training_seed",
        "repetition_unit": "ppo_update_x_failure_group",
    })
    return row


def summarize_group_credit_assignment(
    agent,
    batch: dict[str, Any],
    cfg,
    device: torch.device,
    *,
    update: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return group summaries and pairwise gradient conflicts without mutation."""

    if "condition_group" not in batch or "td_residuals" not in batch:
        raise KeyError("B5 telemetry requires condition_group and td_residuals in the rollout batch")
    t_steps, n_envs, num_agents = batch["actions"].shape
    num_graphs = t_steps * n_envs
    groups_np = np.asarray(batch["condition_group"]).reshape(num_graphs).astype(str)
    unknown = sorted(set(groups_np) - set(ALL_GROUPS))
    if unknown:
        raise ValueError(f"unknown failure groups in rollout: {unknown}")

    obs = torch.as_tensor(batch["obs"].reshape(num_graphs, num_agents, -1), dtype=torch.float32, device=device)
    node_feat = torch.as_tensor(batch["node_feat"].reshape(num_graphs, *batch["node_feat"].shape[2:]), dtype=torch.float32, device=device)
    edge_feat = torch.as_tensor(batch["edge_feat"].reshape(num_graphs, *batch["edge_feat"].shape[2:]), dtype=torch.float32, device=device)
    role = torch.as_tensor(batch["role"].reshape(num_graphs, *batch["role"].shape[2:]), dtype=torch.long, device=device)
    adj = torch.as_tensor(batch["adj"].reshape(num_graphs, *batch["adj"].shape[2:]), dtype=torch.float32, device=device)
    relation_adj = torch.as_tensor(batch["relation_adj"].reshape(num_graphs, *batch["relation_adj"].shape[2:]), dtype=torch.float32, device=device)
    intent_label = torch.as_tensor(batch["intent_label"].reshape(num_graphs, -1), dtype=torch.long, device=device)
    share_obs = torch.as_tensor(batch["share_obs"].reshape(num_graphs, num_agents, -1), dtype=torch.float32, device=device)
    actions = torch.as_tensor(batch["actions"].reshape(num_graphs, num_agents), dtype=torch.long, device=device)
    old_logp = torch.as_tensor(batch["logp"].reshape(num_graphs, num_agents), dtype=torch.float32, device=device)
    raw_advantages = torch.as_tensor(batch["advantages"].reshape(num_graphs, num_agents), dtype=torch.float32, device=device)
    returns = torch.as_tensor(batch["returns"].reshape(num_graphs, num_agents), dtype=torch.float32, device=device)
    rollout_values = torch.as_tensor(batch["values"].reshape(num_graphs, num_agents), dtype=torch.float32, device=device)
    td_residuals = torch.as_tensor(batch["td_residuals"].reshape(num_graphs, num_agents), dtype=torch.float32, device=device)
    normalized_advantages = (raw_advantages - raw_advantages.mean()) / (raw_advantages.std() + 1e-8)

    _, new_logp, entropy, current_values, _, _, _ = agent.get_action_and_value(
        obs, node_feat, edge_feat, role, adj, share_obs,
        relation_adj=relation_adj, action=actions, intent_label=intent_label,
        detach_intent=cfg.detach_intent, oracle_intent=cfg.oracle_intent,
    )
    ratio = (new_logp - old_logp).exp()
    policy_per_graph = torch.max(
        -normalized_advantages * ratio,
        -normalized_advantages * torch.clamp(ratio, 1.0 - cfg.clip_coef, 1.0 + cfg.clip_coef),
    ).mean(dim=1)
    entropy_per_graph = entropy.mean(dim=1)
    actor_per_graph = policy_per_graph - float(cfg.entropy_coef) * entropy_per_graph
    critic_per_graph = 0.5 * (returns - current_values).square().mean(dim=1)

    actor_parameters = [parameter for parameter in agent.actor.parameters() if parameter.requires_grad]
    critic_parameters = [parameter for parameter in agent.critic.parameters() if parameter.requires_grad]
    group_rows: list[dict[str, Any]] = []
    actor_gradients: dict[str, list[torch.Tensor]] = {}
    critic_gradients: dict[str, list[torch.Tensor]] = {}

    for group in ALL_GROUPS:
        indices_np = np.flatnonzero(groups_np == group)
        if len(indices_np) == 0:
            group_rows.append(_empty_group_row(update, group))
            continue
        indices = torch.as_tensor(indices_np, dtype=torch.long, device=device)
        actor_loss = actor_per_graph[indices].mean()
        critic_loss = critic_per_graph[indices].mean()
        actor_group_gradients = _gradients(actor_loss, actor_parameters)
        critic_group_gradients = _gradients(critic_loss, critic_parameters)
        actor_gradients[group] = actor_group_gradients
        critic_gradients[group] = critic_group_gradients

        group_returns = returns[indices]
        group_rollout_values = rollout_values[indices]
        value_residuals = group_returns - group_rollout_values
        group_td = td_residuals[indices]
        returns_variance = group_returns.reshape(-1).var(unbiased=False)
        residual_variance = value_residuals.reshape(-1).var(unbiased=False)
        explained_variance = None if float(returns_variance.cpu()) <= 1e-12 else float((1.0 - residual_variance / returns_variance).cpu())
        return_stats = _tensor_stats(group_returns, "return")
        raw_stats = _tensor_stats(raw_advantages[indices], "raw_advantage")
        normalized_stats = _tensor_stats(normalized_advantages[indices], "normalized_advantage")
        row = {
            "update": update,
            "group": group,
            "status": "OK",
            "graph_count": int(len(indices_np)),
            "agent_sample_count": int(len(indices_np) * num_agents),
            **return_stats,
            "rollout_value_mean": float(group_rollout_values.mean().detach().cpu()),
            "rollout_value_std": float(group_rollout_values.std(unbiased=False).detach().cpu()),
            "value_residual_mean": float(value_residuals.mean().detach().cpu()),
            "value_residual_std": float(value_residuals.std(unbiased=False).detach().cpu()),
            "value_residual_rmse": float(torch.sqrt(value_residuals.square().mean()).detach().cpu()),
            "value_residual_abs_q90": float(torch.quantile(value_residuals.abs().reshape(-1), 0.9).detach().cpu()),
            "td_residual_mean": float(group_td.mean().detach().cpu()),
            "td_residual_std": float(group_td.std(unbiased=False).detach().cpu()),
            "td_residual_abs_q90": float(torch.quantile(group_td.abs().reshape(-1), 0.9).detach().cpu()),
            "explained_variance": explained_variance,
            **raw_stats,
            **normalized_stats,
            "policy_entropy_mean": float(entropy_per_graph[indices].mean().detach().cpu()),
            "actor_gradient_norm": _norm(actor_group_gradients),
            "critic_gradient_norm": _norm(critic_group_gradients),
            "gradient_objective": "ppo_policy_entropy_and_value",
            "independent_unit": "training_seed",
            "repetition_unit": "ppo_update_x_failure_group",
        }
        group_rows.append(row)

    conflict_rows: list[dict[str, Any]] = []
    present_groups = [group for group in ALL_GROUPS if group in actor_gradients]
    for group_a, group_b in combinations(present_groups, 2):
        actor_dot, actor_cosine, actor_conflict = _pair(actor_gradients[group_a], actor_gradients[group_b])
        critic_dot, critic_cosine, critic_conflict = _pair(critic_gradients[group_a], critic_gradients[group_b])
        conflict_rows.append({
            "update": update,
            "group_a": group_a,
            "group_b": group_b,
            "status": "OK",
            "actor_gradient_dot": actor_dot,
            "actor_gradient_cosine": actor_cosine,
            "actor_gradient_conflict": actor_conflict,
            "critic_gradient_dot": critic_dot,
            "critic_gradient_cosine": critic_cosine,
            "critic_gradient_conflict": critic_conflict,
            "independent_unit": "training_seed",
            "repetition_unit": "ppo_update_x_group_pair",
        })
    return group_rows, conflict_rows
