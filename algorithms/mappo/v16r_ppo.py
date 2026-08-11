"""Minimal PPO update for the v1.6R continuous actor and CTDE critic."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
from torch import Tensor, nn

from .continuous_guidance_policy import ContinuousGuidanceActor


class CentralizedValueCritic(nn.Module):
    def __init__(self, share_obs_dim: int, hidden_dim: int = 128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(share_obs_dim, hidden_dim), nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim), nn.Tanh(),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, share_obs: Tensor) -> Tensor:
        return self.net(share_obs).squeeze(-1)


@dataclass(frozen=True)
class V16RPPOConfig:
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip_eps: float = 0.2
    value_coef: float = 0.5
    entropy_coef: float = 0.0
    learning_rate: float = 3e-4
    epochs: int = 1


def compute_gae(batch: dict[str, np.ndarray], values: Tensor, next_value: Tensor, cfg: V16RPPOConfig) -> tuple[Tensor, Tensor]:
    rewards = torch.as_tensor(batch["rewards"], dtype=torch.float32, device=values.device)
    if rewards.ndim == 3:
        rewards = rewards.squeeze(-1)
    dones = torch.as_tensor(batch["dones"], dtype=torch.float32, device=values.device)
    advantages = torch.zeros_like(values)
    gae = torch.zeros_like(values[-1])
    for t in range(values.shape[0] - 1, -1, -1):
        bootstrap = next_value if t == values.shape[0] - 1 else values[t + 1]
        not_done = 1.0 - dones[t]
        delta = rewards[t] + cfg.gamma * bootstrap * not_done - values[t]
        gae = delta + cfg.gamma * cfg.gae_lambda * not_done * gae
        advantages[t] = gae
    returns = advantages + values
    return advantages, returns


def ppo_update(
    actor: ContinuousGuidanceActor,
    critic: CentralizedValueCritic,
    batch: dict[str, np.ndarray],
    cfg: V16RPPOConfig | None = None,
    device: torch.device | str = "cpu",
    graph_conditioned: bool = False,
    optimizer: torch.optim.Optimizer | None = None,
    reference_actor: ContinuousGuidanceActor | None = None,
    retention_coef: float = 0.0,
    adaptive_retention: bool = False,
    retention_beta: float = 1.0,
) -> dict[str, float]:
    cfg = cfg or V16RPPOConfig()
    actor.to(device)
    critic.to(device)
    obs = torch.as_tensor(batch["obs"], dtype=torch.float32, device=device)
    share = torch.as_tensor(batch["share_obs"], dtype=torch.float32, device=device)
    actions = torch.as_tensor(batch["actions"], dtype=torch.float32, device=device)
    old_logp = torch.as_tensor(batch["logp"], dtype=torch.float32, device=device)
    t_steps, n_agents = obs.shape[:2]
    flat_obs = obs.reshape(t_steps * n_agents, -1)
    flat_share = share.reshape(t_steps * n_agents, -1)
    flat_actions = actions.reshape(t_steps * n_agents, 2)
    evidence_mask = torch.as_tensor(batch.get("evidence_mask", np.ones((t_steps, n_agents))), dtype=torch.float32, device=device).reshape(-1)
    graph_node = torch.as_tensor(batch["node"], dtype=torch.float32, device=device) if graph_conditioned else None
    graph_relation = torch.as_tensor(batch["relation_adj"], dtype=torch.float32, device=device) if graph_conditioned else None
    values = critic(flat_share).reshape(t_steps, n_agents)
    next_value = critic(torch.as_tensor(batch["next_share_obs"], dtype=torch.float32, device=device)).detach()
    advantages, returns = compute_gae(batch, values.detach(), next_value, cfg)
    adv_flat = advantages.reshape(-1)
    ret_flat = returns.reshape(-1)
    adv_norm = (adv_flat - adv_flat.mean()) / (adv_flat.std(unbiased=False) + 1e-8)
    if optimizer is None:
        optimizer = torch.optim.Adam(list(actor.parameters()) + list(critic.parameters()), lr=cfg.learning_rate)
    metrics: dict[str, float] = {}
    for _ in range(cfg.epochs):
        if graph_conditioned:
            dist = actor.distribution(flat_obs, graph_node.reshape(t_steps * n_agents, graph_node.shape[2], graph_node.shape[3]), graph_relation.reshape(t_steps * n_agents, graph_relation.shape[2], graph_relation.shape[3], graph_relation.shape[4]))
        else:
            dist = actor.distribution(flat_obs)
        new_logp = dist.log_prob(flat_actions)
        ratio = torch.exp(new_logp - old_logp.reshape(-1))
        clipped = torch.clamp(ratio, 1.0 - cfg.clip_eps, 1.0 + cfg.clip_eps)
        clip_fraction = ((ratio < 1.0 - cfg.clip_eps) | (ratio > 1.0 + cfg.clip_eps)).float().mean()
        policy_loss = -torch.minimum(ratio * adv_norm, clipped * adv_norm).mean()
        value_pred = critic(flat_share)
        value_loss = 0.5 * (value_pred - ret_flat).square().mean()
        entropy = dist.entropy_proxy().mean()
        retention_loss = torch.zeros((), dtype=torch.float32, device=device)
        if reference_actor is not None and retention_coef > 0.0:
            with torch.no_grad():
                ref_mean = reference_actor.distribution(flat_obs).deterministic()
            retention_error = (dist.deterministic() - ref_mean).square().mean(dim=-1)
            if adaptive_retention:
                gate = torch.sigmoid(-float(retention_beta) * adv_norm.detach()) * (evidence_mask > 0.5).float()
                retention_loss = (retention_error * gate).sum() / gate.sum().clamp_min(1.0)
            else:
                active = evidence_mask > 0.5
                retention_loss = retention_error[active].mean() if bool(active.any()) else retention_error.mean() * 0.0
        loss = policy_loss + cfg.value_coef * value_loss - cfg.entropy_coef * entropy + retention_coef * retention_loss
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        actor_grad_norm = float(torch.sqrt(sum((p.grad.detach().square().sum() for p in actor.parameters() if p.grad is not None))).detach())
        actor_before = [p.detach().clone() for p in actor.parameters()]
        torch.nn.utils.clip_grad_norm_(list(actor.parameters()) + list(critic.parameters()), 0.5)
        optimizer.step()
        actor_delta = torch.sqrt(sum((p.detach() - old).square().sum() for p, old in zip(actor.parameters(), actor_before)))
        metrics = {"loss": float(loss.detach()), "policy_loss": float(policy_loss.detach()), "value_loss": float(value_loss.detach()), "retention_loss": float(retention_loss.detach()), "entropy": float(entropy.detach()), "ratio_mean": float(ratio.detach().mean()), "ratio_std": float(ratio.detach().std(unbiased=False)), "clip_fraction": float(clip_fraction.detach()), "adv_mean": float(adv_flat.detach().mean()), "adv_std": float(adv_flat.detach().std(unbiased=False)), "adv_norm_abs_mean": float(adv_norm.detach().abs().mean()), "actor_grad_norm": actor_grad_norm, "actor_param_delta": float(actor_delta)}
    return metrics
