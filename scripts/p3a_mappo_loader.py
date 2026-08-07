# p3a_mappo_loader.py — P3-A MAPPO STRICT loader (protocol v1.1).
#
# Purpose: load the MAPPO v1.5 formal checkpoint with the EXACT agent class and
# loader used by the formal held-out evaluation (evaluate_mappo_v1_5.py:
# MAPPOAgent3D + STRICT state_dict load). P3-A must NOT route the MAPPO
# checkpoint through RIGMAPPOAgent / load_matching_state_dict.
#
# Provenance: MAPPOAgent3D and MLP below are frozen copies of
# scripts/train_mappo_3d_formal_v1_5.py (v1.5 MAPPO worktree). State-dict keys
# are ONLY 'actor.*' and 'critic.*' (no graph / gate / EA-RG modules).
from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.distributions import Categorical

from algorithms.ri_gmappo.simple_ri_gmappo import (  # noqa: E402
    RIGMAPPOConfig,
    checkpoint_model_state,
    make_env,
)


class MLP(nn.Module):
    """Frozen copy of the v1.5 MAPPO MLP (identical to RIGMAPPO's MLP)."""

    def __init__(self, in_dim: int, out_dim: int, hidden_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, out_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class MAPPOAgent3D(nn.Module):
    """Shared actor + role one-hot + centralized critic (v1.5 formal baseline).

    State-dict keys are ONLY 'actor.*' and 'critic.*'.
    """

    def __init__(self, obs_dim: int, role_dim: int, share_obs_dim: int, action_dim: int, hidden_dim: int):
        super().__init__()
        self.actor = MLP(obs_dim + role_dim, action_dim, hidden_dim)
        self.critic = MLP(share_obs_dim, 1, hidden_dim)
        self.role_dim = role_dim

    def get_action_and_value(self, obs, share_obs, action=None, deterministic=False):
        logits = self.actor(obs)
        dist = Categorical(logits=logits)
        if action is None:
            action = torch.argmax(logits, dim=-1) if deterministic else dist.sample()
        log_prob = dist.log_prob(action)
        entropy = dist.entropy()
        value = self.critic(share_obs).squeeze(-1)
        return action, log_prob, entropy, value


def role_onehot(role: np.ndarray, num_roles: int) -> np.ndarray:
    """role: (..., num_agents) -> one-hot (..., num_agents, num_roles)."""
    r = np.asarray(role, dtype=np.int64)
    out = np.zeros((*r.shape, num_roles), dtype=np.float32)
    flat = r.reshape(-1)
    out.reshape(-1, num_roles)[np.arange(flat.size), flat] = 1.0
    return out


def checkpoint_update(path: Path) -> int:
    match = re.search(r"update_(\d+)", path.name)
    return int(match.group(1)) if match else -99


def build_config(args: argparse.Namespace) -> RIGMAPPOConfig:
    """Same env config as the RI/HAPPO evaluators (same make_env), plus the
    P3-A OOD eval-side extensions (default no-op). graph_encoder is irrelevant
    for MAPPOAgent3D but kept no_graph to mirror evaluate_mappo_v1_5.py."""
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
        graph_encoder="no_graph",
        graph_relation_ablation="none",
        graph_message_ablation="none",
        graph_input_ablation="none",
        device=args.device,
        blue_init_rotation_deg=float(getattr(args, "blue_init_rotation_deg", 0.0)),
        blue_init_spacing_scale=float(getattr(args, "blue_init_spacing_scale", 1.0)),
        target_init_range_scale=float(getattr(args, "target_init_range_scale", 1.0)),
        target_init_bearing_offset_deg=float(getattr(args, "target_init_bearing_offset_deg", 0.0)),
        comm_topology_mode=str(getattr(args, "comm_topology_mode", "none")),
    )


def load_agent_strict(args: argparse.Namespace, cfg: RIGMAPPOConfig) -> tuple[MAPPOAgent3D, dict]:
    """STRICT MAPPOAgent3D load. Raises on any missing/unexpected key, so a
    shape / architecture mismatch cannot pass silently. Returns (agent, audit)
    where audit carries the load signature for the checkpoint manifest."""
    checkpoint = Path(args.checkpoint)
    if not checkpoint.exists():
        raise FileNotFoundError(checkpoint)
    sd = torch.load(checkpoint, map_location=args.device, weights_only=True)
    if "actor.net.0.weight" not in sd:
        raise RuntimeError(
            f"not a MAPPO PPO checkpoint (missing actor.net.0.weight): {checkpoint} "
            f"- an actor-only BC checkpoint must not be passed to P3-A evaluation"
        )
    obs_in = int(sd["actor.net.0.weight"].shape[1])
    action_out = int(sd["actor.net.4.weight"].shape[0])
    hidden = int(sd["actor.net.0.weight"].shape[0])
    env = make_env(cfg, args.seed, training=False)
    role_dim = obs_in - env.obs_dim
    if role_dim <= 0:
        raise RuntimeError(f"invalid MAPPO role_dim={role_dim} (obs_in={obs_in}, env_obs_dim={env.obs_dim})")
    agent = MAPPOAgent3D(
        obs_dim=env.obs_dim,
        role_dim=role_dim,
        share_obs_dim=env.share_obs_dim,
        action_dim=action_out,
        hidden_dim=hidden,
    )
    # STRICT: missing/extra/shape keys fail
    result = agent.load_state_dict(sd, strict=False)  # returns (missing, unexpected)
    missing, unexpected = result
    for k in sd:
        kl = k.lower()
        for banned in ("graph", "attention", "edge", "role_pair_gate", "task_support", "relation"):
            if banned in kl:
                raise RuntimeError(f"unexpected key {k} in MAPPO checkpoint")
    if missing or unexpected:
        raise RuntimeError(
            f"MAPPO strict load failed: missing={list(missing)}, unexpected={list(unexpected)}"
        )
    agent.to(torch.device(args.device))
    agent.eval()
    audit = {
        "agent_class": "MAPPOAgent3D",
        "strict_load": True,
        "matched_tensors": len(sd),
        "partial_tensors": 0,
        "skipped_tensors": 0,
        "missing_tensors": len(missing),
        "unexpected_tensors": len(unexpected),
    }
    return agent, audit


def compute_load_signature(agent: nn.Module, checkpoint_path: str, device: torch.device) -> dict:
    """Pure audit: count matched/partial/skipped for an arbitrary agent without
    mutating it. Used to verify that Full/HAPPO/Wider load signatures match the
    formal held-out behavior before any rollout starts."""
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
    model_state = checkpoint_model_state(checkpoint)
    current = agent.state_dict()
    loaded = 0
    partial = 0
    for key, value in model_state.items():
        if key not in current:
            continue
        if current[key].shape == value.shape:
            loaded += 1
        elif (
            value.ndim == 2
            and current[key].ndim == 2
            and current[key].shape[0] == value.shape[0]
            and current[key].shape[1] > value.shape[1]
        ):
            partial += 1
    skipped = len(model_state) - loaded - partial
    return {
        "matched_tensors": loaded,
        "partial_tensors": partial,
        "skipped_tensors": skipped,
    }


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()
