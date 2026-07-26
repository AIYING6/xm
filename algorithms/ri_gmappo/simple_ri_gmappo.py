from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

import csv
import random

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.distributions import Categorical

from envs import (
    EDGE_FEAT_DIM,
    NODE3D_ROLE_IDENTITY_SLICE,
    NUM_INTENTS,
    OBS3D_ROLE_IDENTITY_SLICE,
    UAVIntercept3DConfig,
    UAVIntercept3DEnv,
    UAVPursuitConfig,
    UAVPursuitEnv,
)


@dataclass
class RIGMAPPOConfig:
    env_name: str = "2d_pursuit"
    seed: int = 0
    num_envs: int = 8
    rollout_steps: int = 128
    updates: int = 200
    hidden_dim: int = 128
    role_dim: int = 8
    intent_dim: int = 8
    graph_encoder: str = "single"
    graph_relation_ablation: str = "none"
    graph_message_ablation: str = "none"
    graph_input_ablation: str = "none"
    lr: float = 3e-4
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip_coef: float = 0.2
    entropy_coef: float = 0.01
    value_coef: float = 0.5
    intent_coef: float = 0.1
    intent_balanced_loss: bool = False
    detach_intent: bool = False
    oracle_intent: bool = False
    max_grad_norm: float = 0.5
    ppo_epochs: int = 4
    minibatch_graphs: int = 256
    eval_interval: int = 10
    eval_episodes: int = 20
    target_policy: str = "mixed"
    target_speed: float = 0.75
    communication_radius: float = 8.0
    comm_radius_random_min: float | None = None
    comm_radius_random_max: float | None = None
    communication_range_scale: float = 1.0
    communication_range_random_min: float | None = None
    communication_range_random_max: float | None = None
    communication_dropout_prob: float = 0.0
    communication_dropout_random_min: float | None = None
    communication_dropout_random_max: float | None = None
    message_delay_steps: int = 0
    message_delay_random_min: int | None = None
    message_delay_random_max: int | None = None
    radar_dropout_prob: float = 0.0
    radar_dropout_random_min: float | None = None
    radar_dropout_random_max: float | None = None
    strict_target_sensing: bool = False
    agent_target_info_bottleneck: bool = False
    max_target_message_age_steps: int = 80
    min_target_confidence: float = 0.2
    safety_proximity_distance: float = 0.0
    safety_proximity_penalty_weight: float = 0.0
    attack_geometry_reward_weight: float = 0.0
    failed_blue_agent: int = -1
    node_failure_random_prob: float = 0.0
    node_failure_start_step: int = 0
    node_failure_start_random_min: int | None = None
    node_failure_start_random_max: int | None = None
    node_failure_duration_steps: int = 0
    node_failure_duration_random_min: int | None = None
    node_failure_duration_random_max: int | None = None
    device: str = "cpu"
    out_dir: str = "results/ri_gmappo"
    save_interval: int = 10
    save_snapshots: bool = False
    resume: str | None = None
    update_offset: int = 0
    append_log: bool = False


class MLP(nn.Module):
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


class GraphAttentionLayer(nn.Module):
    def __init__(self, in_dim: int, out_dim: int, edge_dim: int = 0):
        super().__init__()
        self.proj = nn.Linear(in_dim, out_dim, bias=False)
        self.attn = nn.Linear(out_dim * 2, 1, bias=False)
        self.edge_score = None
        if edge_dim > 0:
            self.edge_score = nn.Sequential(
                nn.Linear(edge_dim, out_dim),
                nn.Tanh(),
                nn.Linear(out_dim, 1, bias=False),
            )
            nn.init.zeros_(self.edge_score[-1].weight)
        self.leaky_relu = nn.LeakyReLU(0.2)

    def forward(
        self,
        x: torch.Tensor,
        adj: torch.Tensor,
        edge_feat: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        h = self.proj(x)
        bsz, num_nodes, hidden = h.shape
        hi = h.unsqueeze(2).expand(bsz, num_nodes, num_nodes, hidden)
        hj = h.unsqueeze(1).expand(bsz, num_nodes, num_nodes, hidden)
        scores = self.leaky_relu(self.attn(torch.cat([hi, hj], dim=-1))).squeeze(-1)
        if self.edge_score is not None and edge_feat is not None:
            scores = scores + self.edge_score(edge_feat).squeeze(-1)

        eye = torch.eye(num_nodes, dtype=adj.dtype, device=adj.device).unsqueeze(0)
        mask = torch.clamp(adj + eye, 0.0, 1.0)
        scores = scores.masked_fill(mask <= 0.0, -1e9)
        weights = torch.softmax(scores, dim=-1)
        out = torch.bmm(weights, h)
        return torch.tanh(out), weights


class RoleConditionedGraphAttentionLayer(nn.Module):
    """Graph attention with receiver-sender role-conditioned message gates."""

    def __init__(self, in_dim: int, out_dim: int, num_roles: int, edge_dim: int = 0, use_role_pair_gate: bool = True):
        super().__init__()
        self.num_roles = num_roles
        self.use_role_pair_gate = use_role_pair_gate
        self.proj = nn.Linear(in_dim, out_dim, bias=False)
        self.attn = nn.Linear(out_dim * 2, 1, bias=False)
        self.edge_score = None
        if edge_dim > 0:
            self.edge_score = nn.Sequential(
                nn.Linear(edge_dim, out_dim),
                nn.Tanh(),
                nn.Linear(out_dim, 1, bias=False),
            )
            nn.init.zeros_(self.edge_score[-1].weight)
        self.role_pair_gate = nn.Embedding(num_roles * num_roles, out_dim)
        nn.init.zeros_(self.role_pair_gate.weight)
        self.leaky_relu = nn.LeakyReLU(0.2)

    def forward(
        self,
        x: torch.Tensor,
        adj: torch.Tensor,
        edge_feat: torch.Tensor | None,
        role: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        h = self.proj(x)
        bsz, num_nodes, hidden = h.shape
        hi = h.unsqueeze(2).expand(bsz, num_nodes, num_nodes, hidden)
        hj = h.unsqueeze(1).expand(bsz, num_nodes, num_nodes, hidden)
        scores = self.leaky_relu(self.attn(torch.cat([hi, hj], dim=-1))).squeeze(-1)
        if self.edge_score is not None and edge_feat is not None:
            scores = scores + self.edge_score(edge_feat).squeeze(-1)
        eye = torch.eye(num_nodes, dtype=adj.dtype, device=adj.device).unsqueeze(0)
        mask = torch.clamp(adj + eye, 0.0, 1.0)
        scores = scores.masked_fill(mask <= 0.0, -1e9)
        weights = torch.softmax(scores, dim=-1)

        receiver_role = role.long().unsqueeze(2)
        sender_role = role.long().unsqueeze(1)
        pair_index = receiver_role * self.num_roles + sender_role
        gate = torch.sigmoid(self.role_pair_gate(pair_index)) if self.use_role_pair_gate else torch.full_like(hj, 0.5)
        out = torch.sum(weights.unsqueeze(-1) * hj * gate, dim=2)
        return torch.tanh(out), weights


class MultiRelationGraphEncoder(nn.Module):
    """Separate perception, communication, and task-support message channels."""

    def __init__(
        self,
        hidden_dim: int,
        edge_dim: int,
        num_roles: int,
        num_relations: int = 3,
        use_role_pair_gate: bool = True,
    ):
        super().__init__()
        self.num_relations = num_relations
        self.layer1 = nn.ModuleList(
            [
                RoleConditionedGraphAttentionLayer(
                    hidden_dim, hidden_dim, num_roles, edge_dim, use_role_pair_gate=use_role_pair_gate
                )
                for _ in range(num_relations)
            ]
        )
        self.layer2 = nn.ModuleList(
            [
                RoleConditionedGraphAttentionLayer(
                    hidden_dim, hidden_dim, num_roles, edge_dim, use_role_pair_gate=use_role_pair_gate
                )
                for _ in range(num_relations)
            ]
        )
        # The union graph is retained as a residual information path. It keeps
        # sparse relation channels from discarding useful global context early in training.
        self.global_layer1 = GraphAttentionLayer(hidden_dim, hidden_dim, edge_dim=edge_dim)
        self.global_layer2 = GraphAttentionLayer(hidden_dim, hidden_dim, edge_dim=edge_dim)
        self.fuse1 = nn.Sequential(nn.Linear(hidden_dim * (num_relations + 1), hidden_dim), nn.Tanh())
        self.fuse2 = nn.Sequential(nn.Linear(hidden_dim * (num_relations + 1), hidden_dim), nn.Tanh())

    def _apply_layer(
        self,
        x: torch.Tensor,
        layers: nn.ModuleList,
        relation_adj: torch.Tensor,
        union_adj: torch.Tensor,
        edge_feat: torch.Tensor | None,
        role: torch.Tensor,
        fuse: nn.Module,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        outputs, attentions = [], []
        for relation_id, layer in enumerate(layers):
            output, attention = layer(x, relation_adj[:, relation_id], edge_feat, role)
            outputs.append(output)
            attentions.append(attention)
        global_layer = self.global_layer1 if layers is self.layer1 else self.global_layer2
        global_output, global_attention = global_layer(x, union_adj, edge_feat)
        outputs.append(global_output)
        attentions.append(global_attention)
        return torch.tanh(fuse(torch.cat(outputs, dim=-1)) + x), torch.stack(attentions, dim=1)

    def forward(
        self,
        x: torch.Tensor,
        relation_adj: torch.Tensor,
        edge_feat: torch.Tensor | None,
        role: torch.Tensor,
        union_adj: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        if relation_adj.ndim != 4 or relation_adj.shape[1] != self.num_relations:
            raise ValueError(
                f"Expected relation_adj with shape [batch, {self.num_relations}, nodes, nodes], got {tuple(relation_adj.shape)}"
            )
        x, _ = self._apply_layer(x, self.layer1, relation_adj, union_adj, edge_feat, role, self.fuse1)
        return self._apply_layer(x, self.layer2, relation_adj, union_adj, edge_feat, role, self.fuse2)


OBS_ROLE_IDENTITY_SLICE = OBS3D_ROLE_IDENTITY_SLICE
NODE_ROLE_IDENTITY_SLICE = NODE3D_ROLE_IDENTITY_SLICE


def zero_feature_slice(x: torch.Tensor, feature_slice: slice) -> torch.Tensor:
    start = 0 if feature_slice.start is None else feature_slice.start
    if x.shape[-1] <= start:
        return x
    stop = x.shape[-1] if feature_slice.stop is None else min(feature_slice.stop, x.shape[-1])
    out = x.clone()
    out[..., start:stop] = 0.0
    return out


class RIActor(nn.Module):
    def __init__(
        self,
        obs_dim: int,
        node_feat_dim: int,
        edge_feat_dim: int,
        num_roles: int,
        role_dim: int,
        intent_dim: int,
        hidden_dim: int,
        action_dim: int,
        graph_encoder: str = "single",
        graph_message_ablation: str = "none",
        graph_input_ablation: str = "none",
        num_intents: int = NUM_INTENTS,
        use_intent_context: bool = True,
    ):
        super().__init__()
        if graph_encoder not in {"no_graph", "single", "multi_relation"}:
            raise ValueError(f"Unsupported graph_encoder: {graph_encoder}")
        if graph_message_ablation not in {"none", "no_role_pair_gate"}:
            raise ValueError(f"Unsupported graph_message_ablation: {graph_message_ablation}")
        if graph_input_ablation not in {"none", "no_edge_features", "no_role_identity"}:
            raise ValueError(f"Unsupported graph_input_ablation: {graph_input_ablation}")
        self.graph_encoder = graph_encoder
        self.graph_message_ablation = graph_message_ablation
        self.graph_input_ablation = graph_input_ablation
        self.num_intents = num_intents
        self.use_intent_context = use_intent_context
        self.role_emb = nn.Embedding(num_roles, role_dim)
        self.intent_emb = nn.Embedding(num_intents, intent_dim)
        self.obs_encoder = nn.Sequential(nn.Linear(obs_dim, hidden_dim), nn.Tanh())
        self.input = nn.Sequential(nn.Linear(node_feat_dim + role_dim, hidden_dim), nn.Tanh())
        if graph_encoder == "no_graph":
            self.no_graph_intent_head = nn.Sequential(
                nn.Linear(hidden_dim, hidden_dim),
                nn.Tanh(),
                nn.Linear(hidden_dim, num_intents),
            )
        elif graph_encoder == "single":
            self.gat1 = GraphAttentionLayer(hidden_dim, hidden_dim, edge_dim=edge_feat_dim)
            self.gat2 = GraphAttentionLayer(hidden_dim, hidden_dim, edge_dim=edge_feat_dim)
        else:
            self.multi_relation_graph = MultiRelationGraphEncoder(
                hidden_dim,
                edge_feat_dim,
                num_roles,
                use_role_pair_gate=graph_message_ablation != "no_role_pair_gate",
            )
        self.intent_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, num_intents),
        )
        self.policy_head = nn.Sequential(
            nn.Linear(hidden_dim * 2 + intent_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, action_dim),
        )

    def forward(
        self,
        obs: torch.Tensor,
        node_feat: torch.Tensor,
        edge_feat: torch.Tensor | None,
        role: torch.Tensor,
        adj: torch.Tensor,
        num_agents: int,
        relation_adj: torch.Tensor | None = None,
        intent_label: torch.Tensor | None = None,
        detach_intent: bool = False,
        oracle_intent: bool = False,
    ):
        if self.graph_input_ablation == "no_edge_features" and edge_feat is not None:
            edge_feat = torch.zeros_like(edge_feat)
        if self.graph_input_ablation == "no_role_identity":
            obs = zero_feature_slice(obs, OBS_ROLE_IDENTITY_SLICE)
            node_feat = zero_feature_slice(node_feat, NODE_ROLE_IDENTITY_SLICE)
            role = torch.zeros_like(role)
        role_feat = self.role_emb(role.long())
        x = self.input(torch.cat([node_feat, role_feat], dim=-1))
        if self.graph_encoder == "no_graph":
            graph_feat = torch.zeros(
                obs.shape[0],
                num_agents,
                x.shape[-1],
                dtype=x.dtype,
                device=x.device,
            )
            target_summary = torch.zeros(
                obs.shape[0],
                1,
                x.shape[-1],
                dtype=x.dtype,
                device=x.device,
            )
            intent_logits = self.no_graph_intent_head(target_summary)
            intent_context = torch.zeros(
                obs.shape[0],
                num_agents,
                self.intent_emb.embedding_dim,
                dtype=x.dtype,
                device=x.device,
            )
            attn = torch.zeros(
                obs.shape[0],
                x.shape[1],
                x.shape[1],
                dtype=x.dtype,
                device=x.device,
            )
            obs_feat = self.obs_encoder(obs)
            logits = self.policy_head(torch.cat([obs_feat, graph_feat, intent_context], dim=-1))
            return logits, attn, intent_logits
        if self.graph_encoder == "single":
            x, _ = self.gat1(x, adj, edge_feat)
            x, attn = self.gat2(x, adj, edge_feat)
        else:
            if relation_adj is None:
                raise ValueError("relation_adj is required when graph_encoder='multi_relation'")
            x, attn = self.multi_relation_graph(x, relation_adj, edge_feat, role, adj)

        graph_feat = x[:, :num_agents]
        target_feat = x[:, num_agents:]
        intent_logits = self.intent_head(target_feat)

        if not self.use_intent_context:
            intent_context = torch.zeros(
                obs.shape[0],
                num_agents,
                self.intent_emb.embedding_dim,
                dtype=x.dtype,
                device=x.device,
            )
        elif oracle_intent:
            if intent_label is None:
                raise ValueError("intent_label is required when oracle_intent=True")
            intent_context = self.intent_emb(intent_label.long())
        else:
            intent_probs = torch.softmax(intent_logits, dim=-1)
            if detach_intent:
                intent_probs = intent_probs.detach()
            intent_context = intent_probs @ self.intent_emb.weight
        intent_context = intent_context.mean(dim=1).unsqueeze(1).expand(-1, num_agents, -1)

        obs_feat = self.obs_encoder(obs)
        logits = self.policy_head(torch.cat([obs_feat, graph_feat, intent_context], dim=-1))
        return logits, attn, intent_logits


class RIGMAPPOAgent(nn.Module):
    def __init__(
        self,
        obs_dim: int,
        node_feat_dim: int,
        edge_feat_dim: int,
        share_obs_dim: int,
        action_dim: int,
        num_agents: int,
        num_roles: int,
        hidden_dim: int,
        role_dim: int,
        intent_dim: int,
        graph_encoder: str = "single",
        graph_message_ablation: str = "none",
        graph_input_ablation: str = "none",
        use_intent_context: bool = True,
    ):
        super().__init__()
        self.num_agents = num_agents
        self.num_roles = num_roles
        self.actor = RIActor(
            obs_dim,
            node_feat_dim,
            edge_feat_dim,
            num_roles=num_roles,
            role_dim=role_dim,
            intent_dim=intent_dim,
            hidden_dim=hidden_dim,
            action_dim=action_dim,
            graph_encoder=graph_encoder,
            graph_message_ablation=graph_message_ablation,
            graph_input_ablation=graph_input_ablation,
            use_intent_context=use_intent_context,
        )
        self.critic = MLP(share_obs_dim + num_roles, 1, hidden_dim)

    def critic_value(self, share_obs: torch.Tensor, role: torch.Tensor) -> torch.Tensor:
        agent_role = role[:, : self.num_agents].long().clamp(min=0, max=self.num_roles - 1)
        role_one_hot = F.one_hot(agent_role, num_classes=self.num_roles).to(dtype=share_obs.dtype, device=share_obs.device)
        return self.critic(torch.cat([share_obs, role_one_hot], dim=-1)).squeeze(-1)

    def get_action_and_value(
        self,
        obs: torch.Tensor,
        node_feat: torch.Tensor,
        edge_feat: torch.Tensor | None,
        role: torch.Tensor,
        adj: torch.Tensor,
        share_obs: torch.Tensor,
        relation_adj: torch.Tensor | None = None,
        action: torch.Tensor | None = None,
        deterministic: bool = False,
        intent_label: torch.Tensor | None = None,
        detach_intent: bool = False,
        oracle_intent: bool = False,
    ):
        logits, attn, intent_logits = self.actor(
            obs,
            node_feat,
            edge_feat,
            role,
            adj,
            self.num_agents,
            relation_adj=relation_adj,
            intent_label=intent_label,
            detach_intent=detach_intent,
            oracle_intent=oracle_intent,
        )
        dist = Categorical(logits=logits)
        if action is None:
            action = torch.argmax(logits, dim=-1) if deterministic else dist.sample()
        log_prob = dist.log_prob(action)
        entropy = dist.entropy()
        value = self.critic_value(share_obs, role)
        return action, log_prob, entropy, value, attn, intent_logits


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def make_env(cfg: RIGMAPPOConfig, seed: int, training: bool = True):
    if cfg.env_name == "2d_pursuit":
        return UAVPursuitEnv(
            UAVPursuitConfig(
                seed=seed,
                target_policy=cfg.target_policy,
                target_speed=cfg.target_speed,
                communication_radius=sample_comm_radius(cfg) if training else cfg.communication_radius,
                communication_dropout_prob=cfg.communication_dropout_prob,
            )
        )
    if cfg.env_name == "3d_intercept":
        return UAVIntercept3DEnv(
            UAVIntercept3DConfig(
                seed=seed,
                target_policy=cfg.target_policy,
                communication_range_scale=sample_communication_range_scale(cfg) if training else cfg.communication_range_scale,
                communication_dropout_prob=sample_float_curriculum(
                    cfg.communication_dropout_prob,
                    cfg.communication_dropout_random_min,
                    cfg.communication_dropout_random_max,
                )
                if training
                else cfg.communication_dropout_prob,
                message_delay_steps=sample_int_curriculum(
                    cfg.message_delay_steps,
                    cfg.message_delay_random_min,
                    cfg.message_delay_random_max,
                )
                if training
                else cfg.message_delay_steps,
                radar_dropout_prob=sample_float_curriculum(
                    cfg.radar_dropout_prob,
                    cfg.radar_dropout_random_min,
                    cfg.radar_dropout_random_max,
                )
                if training
                else cfg.radar_dropout_prob,
                strict_target_sensing=cfg.strict_target_sensing,
                agent_target_info_bottleneck=cfg.agent_target_info_bottleneck,
                max_target_message_age_steps=cfg.max_target_message_age_steps,
                min_target_confidence=cfg.min_target_confidence,
                safety_proximity_distance=cfg.safety_proximity_distance,
                safety_proximity_penalty_weight=cfg.safety_proximity_penalty_weight,
                attack_geometry_reward_weight=cfg.attack_geometry_reward_weight,
                failed_blue_agent=sample_failed_blue_agent(cfg) if training else cfg.failed_blue_agent,
                node_failure_start_step=sample_int_curriculum(
                    cfg.node_failure_start_step,
                    cfg.node_failure_start_random_min,
                    cfg.node_failure_start_random_max,
                )
                if training
                else cfg.node_failure_start_step,
                node_failure_duration_steps=sample_int_curriculum(
                    cfg.node_failure_duration_steps,
                    cfg.node_failure_duration_random_min,
                    cfg.node_failure_duration_random_max,
                )
                if training
                else cfg.node_failure_duration_steps,
                graph_relation_ablation=cfg.graph_relation_ablation,
            )
        )
    raise ValueError(f"Unsupported env_name: {cfg.env_name}")


def make_envs(cfg: RIGMAPPOConfig) -> List[UAVPursuitEnv | UAVIntercept3DEnv]:
    return [make_env(cfg, cfg.seed + i, training=True) for i in range(cfg.num_envs)]


def sample_comm_radius(cfg: RIGMAPPOConfig) -> float:
    if cfg.comm_radius_random_min is None or cfg.comm_radius_random_max is None:
        return cfg.communication_radius
    lo = min(cfg.comm_radius_random_min, cfg.comm_radius_random_max)
    hi = max(cfg.comm_radius_random_min, cfg.comm_radius_random_max)
    return random.uniform(lo, hi)


def sample_communication_range_scale(cfg: RIGMAPPOConfig) -> float:
    if cfg.communication_range_random_min is None or cfg.communication_range_random_max is None:
        return cfg.communication_range_scale
    lo = min(cfg.communication_range_random_min, cfg.communication_range_random_max)
    hi = max(cfg.communication_range_random_min, cfg.communication_range_random_max)
    return random.uniform(lo, hi)


def sample_float_curriculum(default: float, lo: float | None, hi: float | None) -> float:
    if lo is None or hi is None:
        return default
    return random.uniform(min(lo, hi), max(lo, hi))


def sample_int_curriculum(default: int, lo: int | None, hi: int | None) -> int:
    if lo is None or hi is None:
        return default
    return random.randint(min(lo, hi), max(lo, hi))


def sample_failed_blue_agent(cfg: RIGMAPPOConfig) -> int:
    if cfg.node_failure_random_prob <= 0.0 or random.random() >= cfg.node_failure_random_prob:
        return cfg.failed_blue_agent
    return random.randint(0, 2)


def stack_graphs(graphs: List[dict]) -> dict:
    target_counts = [
        len(g["intent_label"])
        if "intent_label" in g
        else int(np.sum(g["role"] == np.max(g["role"])))
        for g in graphs
    ]
    if len(set(target_counts)) != 1:
        raise ValueError("All vectorized environments must have the same target-node count")
    target_count = target_counts[0]
    return {
        "node_feat": np.stack([g["node_feat"] for g in graphs]).astype(np.float32),
        "edge_feat": np.stack(
            [g.get("edge_feat", np.zeros((*g["adj"].shape, EDGE_FEAT_DIM), dtype=np.float32)) for g in graphs]
        ).astype(np.float32),
        "role": np.stack([g["role"] for g in graphs]).astype(np.int64),
        "adj": np.stack([g["adj"] for g in graphs]).astype(np.float32),
        "relation_adj": np.stack(
            [
                g.get("relation_adj", np.repeat(g["adj"][None, ...], 3, axis=0))
                for g in graphs
            ]
        ).astype(np.float32),
        # 3DOF does not expose an artificial target-intent label. Keep a neutral
        # placeholder so the latent intent context remains shape-compatible.
        "intent_label": np.stack(
            [g.get("intent_label", np.zeros(target_count, dtype=np.int64)) for g in graphs]
        ).astype(np.int64),
        "has_intent_label": np.asarray([bool(g.get("has_intent_label", "intent_label" in g)) for g in graphs], dtype=bool),
    }


def checkpoint_model_state(checkpoint: dict) -> dict:
    if "model_state" in checkpoint:
        return checkpoint["model_state"]
    return checkpoint


def load_matching_state_dict(agent: nn.Module, checkpoint_path: str, device: torch.device) -> tuple[dict, bool]:
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
    model_state = checkpoint_model_state(checkpoint)
    current = agent.state_dict()
    loaded = 0
    partial = 0
    for key, value in model_state.items():
        if key not in current:
            continue
        if current[key].shape == value.shape:
            current[key] = value
            loaded += 1
        elif (
            value.ndim == 2
            and current[key].ndim == 2
            and current[key].shape[0] == value.shape[0]
            and current[key].shape[1] > value.shape[1]
        ):
            expanded = current[key].clone()
            expanded[:, : value.shape[1]] = value
            expanded[:, value.shape[1] :] = 0.0
            current[key] = expanded
            partial += 1
    agent.load_state_dict(current)
    skipped = len(model_state) - loaded - partial
    print(
        f"loaded {loaded} matching tensors and {partial} partial tensors from {checkpoint_path}; skipped {skipped}",
        flush=True,
    )
    exact_match = partial == 0 and skipped == 0 and loaded == len(model_state)
    return checkpoint, exact_match


def load_training_checkpoint(
    agent: nn.Module,
    optimizer: optim.Optimizer,
    checkpoint_path: str,
    device: torch.device,
) -> None:
    checkpoint, exact_match = load_matching_state_dict(agent, checkpoint_path, device)
    optimizer_state = checkpoint.get("optimizer_state") if isinstance(checkpoint, dict) else None
    if optimizer_state is not None:
        if exact_match:
            optimizer.load_state_dict(optimizer_state)
            print(f"loaded optimizer state from {checkpoint_path}", flush=True)
        else:
            print(f"skipped optimizer state from {checkpoint_path} because model tensors were not an exact match", flush=True)


def save_training_checkpoint(
    path: Path,
    agent: nn.Module,
    optimizer: optim.Optimizer,
    update: int,
    best_eval_key: tuple[float, float, float, float] | None = None,
) -> None:
    payload = {
        "model_state": agent.state_dict(),
        "optimizer_state": optimizer.state_dict(),
        "update": int(update),
    }
    if best_eval_key is not None:
        payload["best_eval_key"] = tuple(float(x) for x in best_eval_key)
    torch.save(payload, path)


def eval_policy(agent: RIGMAPPOAgent, cfg: RIGMAPPOConfig, base_seed: int = 10_000) -> dict:
    device = torch.device(cfg.device)
    records = []
    intent_correct, intent_total = 0, 0
    agent.eval()
    with torch.no_grad():
        for ep in range(cfg.eval_episodes):
            env = make_env(cfg, base_seed + ep, training=False)
            obs, share_obs, graph = env.reset()
            while True:
                g = stack_graphs([graph])
                actions, _, _, _, _, intent_logits = agent.get_action_and_value(
                    torch.as_tensor(obs[None, ...], dtype=torch.float32, device=device),
                    torch.as_tensor(g["node_feat"], dtype=torch.float32, device=device),
                    torch.as_tensor(g["edge_feat"], dtype=torch.float32, device=device),
                    torch.as_tensor(g["role"], dtype=torch.long, device=device),
                    torch.as_tensor(g["adj"], dtype=torch.float32, device=device),
                    torch.as_tensor(share_obs[None, ...], dtype=torch.float32, device=device),
                    relation_adj=torch.as_tensor(g["relation_adj"], dtype=torch.float32, device=device),
                    deterministic=True,
                    intent_label=torch.as_tensor(g["intent_label"], dtype=torch.long, device=device),
                    detach_intent=cfg.detach_intent,
                    oracle_intent=cfg.oracle_intent,
                )
                if bool(g["has_intent_label"][0]):
                    pred = intent_logits.argmax(dim=-1).cpu().numpy()
                    intent_correct += int((pred == g["intent_label"]).sum())
                    intent_total += int(np.prod(g["intent_label"].shape))

                obs, share_obs, graph, _, dones, info = env.step(actions.squeeze(0).cpu().numpy())
                if np.all(dones):
                    records.append(info)
                    break
    agent.train()
    return {
        "eval_success_rate": float(np.mean([r["success"] for r in records])),
        "eval_collision_rate": float(np.mean([r["collision"] for r in records])),
        "eval_timeout_rate": float(np.mean([r["timeout"] for r in records])),
        "eval_avg_steps": float(np.mean([r["step"] for r in records])),
        "eval_avg_distance": float(np.mean([r.get("mean_distance", r.get("mean_range", 0.0)) for r in records])),
        "eval_intent_acc": float(intent_correct / intent_total) if intent_total else float("nan"),
    }


def train_ri_gmappo(cfg: RIGMAPPOConfig) -> Path:
    if cfg.env_name == "3d_intercept" and cfg.oracle_intent:
        raise ValueError("oracle_intent is unavailable for 3d_intercept because it has no intent supervision")
    set_seed(cfg.seed)
    device = torch.device(cfg.device)
    out_dir = Path(cfg.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    envs = make_envs(cfg)
    obs_list, share_list, graph_list = [], [], []
    for env in envs:
        obs, share_obs, graph = env.reset()
        obs_list.append(obs)
        share_list.append(share_obs)
        graph_list.append(graph)
    obs = np.stack(obs_list)
    share_obs = np.stack(share_list)
    graph_obs = stack_graphs(graph_list)

    sample_env = envs[0]
    sample_graph = graph_list[0]
    agent = RIGMAPPOAgent(
        obs_dim=sample_env.obs_dim,
        node_feat_dim=sample_graph["node_feat"].shape[-1],
        edge_feat_dim=sample_graph["edge_feat"].shape[-1],
        share_obs_dim=sample_env.share_obs_dim,
        action_dim=sample_env.action_dim,
        num_agents=sample_env.num_agents,
        hidden_dim=cfg.hidden_dim,
        role_dim=cfg.role_dim,
        intent_dim=cfg.intent_dim,
        graph_encoder=cfg.graph_encoder,
        graph_message_ablation=cfg.graph_message_ablation,
        graph_input_ablation=cfg.graph_input_ablation,
        use_intent_context=cfg.env_name != "3d_intercept",
        num_roles=max(4, int(np.max(sample_graph["role"])) + 1),
    ).to(device)
    optimizer = optim.Adam(agent.parameters(), lr=cfg.lr, eps=1e-5)
    if cfg.resume:
        load_training_checkpoint(agent, optimizer, cfg.resume, device)

    log_path = out_dir / "train_log.csv"
    fieldnames = [
        "update",
        "loss",
        "policy_loss",
        "value_loss",
        "entropy",
        "intent_loss",
        "intent_acc",
        "train_avg_reward",
        "eval_success_rate",
        "eval_collision_rate",
        "eval_timeout_rate",
        "eval_avg_steps",
        "eval_avg_distance",
        "eval_intent_acc",
    ]
    write_header = not (cfg.append_log and log_path.exists())
    mode = "a" if cfg.append_log else "w"
    with log_path.open(mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        f.flush()
        best_eval_key = (-1.0, float("-inf"), float("-inf"), float("-inf"))
        for local_update in range(1, cfg.updates + 1):
            update = cfg.update_offset + local_update
            batch = collect_rollout(agent, envs, obs, share_obs, graph_obs, cfg, device)
            obs, share_obs, graph_obs = batch["next_obs"], batch["next_share_obs"], batch["next_graph_obs"]
            train_info = update_policy(agent, optimizer, batch, cfg, device)
            row = {"update": update, **train_info, "train_avg_reward": float(batch["rewards"].mean())}
            if update % cfg.eval_interval == 0 or update == 1:
                row.update(eval_policy(agent, cfg, base_seed=10_000 + update * 100))
                print(row, flush=True)
                eval_key = (
                    float(row["eval_success_rate"]),
                    -float(row["eval_collision_rate"]),
                    -float(row["eval_timeout_rate"]),
                    -float(row["eval_avg_steps"]),
                )
                if eval_key > best_eval_key:
                    best_eval_key = eval_key
                    torch.save(agent.state_dict(), out_dir / "actor_critic_best.pt")
            else:
                row.update(
                    {
                        "eval_success_rate": "",
                        "eval_collision_rate": "",
                        "eval_timeout_rate": "",
                        "eval_avg_steps": "",
                        "eval_avg_distance": "",
                        "eval_intent_acc": "",
                    }
                )
            writer.writerow(row)
            f.flush()
            if update % cfg.save_interval == 0 or local_update == cfg.updates:
                torch.save(agent.state_dict(), out_dir / "actor_critic_latest.pt")
                save_training_checkpoint(
                    out_dir / "actor_critic_training_state_latest.pt",
                    agent,
                    optimizer,
                    update,
                    best_eval_key,
                )
                if cfg.save_snapshots:
                    torch.save(agent.state_dict(), out_dir / f"actor_critic_update_{update:04d}.pt")
                    save_training_checkpoint(
                        out_dir / f"actor_critic_training_state_update_{update:04d}.pt",
                        agent,
                        optimizer,
                        update,
                        best_eval_key,
                    )
    return log_path


def collect_rollout(
    agent: RIGMAPPOAgent,
    envs: List[UAVPursuitEnv | UAVIntercept3DEnv],
    obs: np.ndarray,
    share_obs: np.ndarray,
    graph_obs: dict,
    cfg: RIGMAPPOConfig,
    device: torch.device,
) -> dict:
    obs_buf, share_buf, node_buf, edge_buf, role_buf, adj_buf, intent_buf = [], [], [], [], [], [], []
    relation_adj_buf = []
    action_buf, logp_buf, reward_buf, done_buf, value_buf = [], [], [], [], []

    for _ in range(cfg.rollout_steps):
        with torch.no_grad():
            actions, logp, _, values, _, _ = agent.get_action_and_value(
                torch.as_tensor(obs, dtype=torch.float32, device=device),
                torch.as_tensor(graph_obs["node_feat"], dtype=torch.float32, device=device),
                torch.as_tensor(graph_obs["edge_feat"], dtype=torch.float32, device=device),
                torch.as_tensor(graph_obs["role"], dtype=torch.long, device=device),
                torch.as_tensor(graph_obs["adj"], dtype=torch.float32, device=device),
                torch.as_tensor(share_obs, dtype=torch.float32, device=device),
                relation_adj=torch.as_tensor(graph_obs["relation_adj"], dtype=torch.float32, device=device),
                intent_label=torch.as_tensor(graph_obs["intent_label"], dtype=torch.long, device=device),
                detach_intent=cfg.detach_intent,
                oracle_intent=cfg.oracle_intent,
            )

        actions_np = actions.cpu().numpy()
        values_np = values.cpu().numpy()
        logp_np = logp.cpu().numpy()
        next_obs, next_share, next_graphs, rewards, dones = [], [], [], [], []
        for e, env in enumerate(envs):
            o, s, g, r, d, _ = env.step(actions_np[e])
            if np.all(d):
                if cfg.env_name == "2d_pursuit":
                    env.config.communication_radius = sample_comm_radius(cfg)
                elif cfg.env_name == "3d_intercept":
                    env.config.communication_range_scale = sample_communication_range_scale(cfg)
                    env.config.communication_dropout_prob = sample_float_curriculum(
                        cfg.communication_dropout_prob,
                        cfg.communication_dropout_random_min,
                        cfg.communication_dropout_random_max,
                    )
                    env.config.message_delay_steps = sample_int_curriculum(
                        cfg.message_delay_steps,
                        cfg.message_delay_random_min,
                        cfg.message_delay_random_max,
                    )
                    env.config.radar_dropout_prob = sample_float_curriculum(
                        cfg.radar_dropout_prob,
                        cfg.radar_dropout_random_min,
                        cfg.radar_dropout_random_max,
                    )
                    env.config.failed_blue_agent = sample_failed_blue_agent(cfg)
                    env.config.node_failure_start_step = sample_int_curriculum(
                        cfg.node_failure_start_step,
                        cfg.node_failure_start_random_min,
                        cfg.node_failure_start_random_max,
                    )
                    env.config.node_failure_duration_steps = sample_int_curriculum(
                        cfg.node_failure_duration_steps,
                        cfg.node_failure_duration_random_min,
                        cfg.node_failure_duration_random_max,
                    )
                o, s, g = env.reset()
            next_obs.append(o)
            next_share.append(s)
            next_graphs.append(g)
            rewards.append(r[:, 0])
            dones.append(d[:, 0])

        obs_buf.append(obs.copy())
        share_buf.append(share_obs.copy())
        node_buf.append(graph_obs["node_feat"].copy())
        edge_buf.append(graph_obs["edge_feat"].copy())
        role_buf.append(graph_obs["role"].copy())
        adj_buf.append(graph_obs["adj"].copy())
        relation_adj_buf.append(graph_obs["relation_adj"].copy())
        intent_buf.append(graph_obs["intent_label"].copy())
        action_buf.append(actions_np.copy())
        logp_buf.append(logp_np.copy())
        value_buf.append(values_np.copy())
        reward_buf.append(np.asarray(rewards, dtype=np.float32))
        done_buf.append(np.asarray(dones, dtype=np.float32))

        obs = np.stack(next_obs)
        share_obs = np.stack(next_share)
        graph_obs = stack_graphs(next_graphs)

    with torch.no_grad():
        next_values = agent.critic_value(
            torch.as_tensor(share_obs, dtype=torch.float32, device=device),
            torch.as_tensor(graph_obs["role"], dtype=torch.long, device=device),
        )
        next_values = next_values.cpu().numpy()

    rewards_np = np.asarray(reward_buf, dtype=np.float32)
    dones_np = np.asarray(done_buf, dtype=np.float32)
    values_np = np.asarray(value_buf, dtype=np.float32)
    advantages, returns = compute_gae(rewards_np, dones_np, values_np, next_values, cfg.gamma, cfg.gae_lambda)
    return {
        "obs": np.asarray(obs_buf, dtype=np.float32),
        "share_obs": np.asarray(share_buf, dtype=np.float32),
        "node_feat": np.asarray(node_buf, dtype=np.float32),
        "edge_feat": np.asarray(edge_buf, dtype=np.float32),
        "role": np.asarray(role_buf, dtype=np.int64),
        "adj": np.asarray(adj_buf, dtype=np.float32),
        "relation_adj": np.asarray(relation_adj_buf, dtype=np.float32),
        "intent_label": np.asarray(intent_buf, dtype=np.int64),
        "has_intent_label": bool(np.all(graph_obs["has_intent_label"])),
        "actions": np.asarray(action_buf, dtype=np.int64),
        "logp": np.asarray(logp_buf, dtype=np.float32),
        "values": values_np,
        "rewards": rewards_np,
        "dones": dones_np,
        "advantages": advantages,
        "returns": returns,
        "next_obs": obs,
        "next_share_obs": share_obs,
        "next_graph_obs": graph_obs,
    }


def compute_gae(rewards, dones, values, next_values, gamma, gae_lambda):
    advantages = np.zeros_like(rewards, dtype=np.float32)
    last_gae = np.zeros_like(next_values, dtype=np.float32)
    for t in reversed(range(rewards.shape[0])):
        next_nonterminal = 1.0 - dones[t]
        next_value = next_values if t == rewards.shape[0] - 1 else values[t + 1]
        delta = rewards[t] + gamma * next_value * next_nonterminal - values[t]
        last_gae = delta + gamma * gae_lambda * next_nonterminal * last_gae
        advantages[t] = last_gae
    return advantages, advantages + values


def effective_intent_coef(cfg: RIGMAPPOConfig) -> float:
    return cfg.intent_coef if cfg.env_name == "2d_pursuit" else 0.0


def update_policy(agent: RIGMAPPOAgent, optimizer: optim.Optimizer, batch: dict, cfg: RIGMAPPOConfig, device):
    t_steps, n_envs, num_agents = batch["actions"].shape
    num_graphs = t_steps * n_envs
    obs = torch.as_tensor(batch["obs"].reshape(num_graphs, num_agents, -1), dtype=torch.float32, device=device)
    node_feat = torch.as_tensor(batch["node_feat"].reshape(num_graphs, *batch["node_feat"].shape[2:]), dtype=torch.float32, device=device)
    edge_feat = torch.as_tensor(batch["edge_feat"].reshape(num_graphs, *batch["edge_feat"].shape[2:]), dtype=torch.float32, device=device)
    role = torch.as_tensor(batch["role"].reshape(num_graphs, *batch["role"].shape[2:]), dtype=torch.long, device=device)
    adj = torch.as_tensor(batch["adj"].reshape(num_graphs, *batch["adj"].shape[2:]), dtype=torch.float32, device=device)
    relation_adj = torch.as_tensor(
        batch["relation_adj"].reshape(num_graphs, *batch["relation_adj"].shape[2:]), dtype=torch.float32, device=device
    )
    intent_label = torch.as_tensor(batch["intent_label"].reshape(num_graphs, -1), dtype=torch.long, device=device)
    share_obs = torch.as_tensor(batch["share_obs"].reshape(num_graphs, num_agents, -1), dtype=torch.float32, device=device)
    actions = torch.as_tensor(batch["actions"].reshape(num_graphs, num_agents), dtype=torch.long, device=device)
    old_logp = torch.as_tensor(batch["logp"].reshape(num_graphs, num_agents), dtype=torch.float32, device=device)
    advantages = torch.as_tensor(batch["advantages"].reshape(num_graphs, num_agents), dtype=torch.float32, device=device)
    returns = torch.as_tensor(batch["returns"].reshape(num_graphs, num_agents), dtype=torch.float32, device=device)
    advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

    losses, policy_losses, value_losses, entropies, intent_losses, intent_accs = [], [], [], [], [], []
    indices = np.arange(num_graphs)
    for _ in range(cfg.ppo_epochs):
        np.random.shuffle(indices)
        for start in range(0, num_graphs, cfg.minibatch_graphs):
            mb = indices[start : start + cfg.minibatch_graphs]
            _, new_logp, entropy, values, _, intent_logits = agent.get_action_and_value(
                obs[mb],
                node_feat[mb],
                edge_feat[mb],
                role[mb],
                adj[mb],
                share_obs[mb],
                relation_adj=relation_adj[mb],
                action=actions[mb],
                intent_label=intent_label[mb],
                detach_intent=cfg.detach_intent,
                oracle_intent=cfg.oracle_intent,
            )
            ratio = (new_logp - old_logp[mb]).exp()
            pg_loss1 = -advantages[mb] * ratio
            pg_loss2 = -advantages[mb] * torch.clamp(ratio, 1.0 - cfg.clip_coef, 1.0 + cfg.clip_coef)
            policy_loss = torch.max(pg_loss1, pg_loss2).mean()
            value_loss = 0.5 * (returns[mb] - values).pow(2).mean()
            entropy_loss = entropy.mean()
            if batch["has_intent_label"]:
                flat_intent_label = intent_label[mb].reshape(-1)
                intent_weight = None
                if cfg.intent_balanced_loss:
                    counts = torch.bincount(flat_intent_label, minlength=NUM_INTENTS).float()
                    present = counts > 0
                    intent_weight = torch.zeros_like(counts)
                    intent_weight[present] = counts[present].sum() / (present.float().sum() * counts[present])
                intent_loss = F.cross_entropy(
                    intent_logits.reshape(-1, NUM_INTENTS),
                    flat_intent_label,
                    weight=intent_weight,
                )
                intent_pred = intent_logits.argmax(dim=-1)
                intent_acc = (intent_pred == intent_label[mb]).float().mean()
            else:
                intent_loss = torch.zeros((), device=device)
                intent_acc = torch.zeros((), device=device)
            loss = (
                policy_loss
                + cfg.value_coef * value_loss
                - cfg.entropy_coef * entropy_loss
                + effective_intent_coef(cfg) * intent_loss
            )

            optimizer.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(agent.parameters(), cfg.max_grad_norm)
            optimizer.step()

            losses.append(float(loss.detach().cpu()))
            policy_losses.append(float(policy_loss.detach().cpu()))
            value_losses.append(float(value_loss.detach().cpu()))
            entropies.append(float(entropy_loss.detach().cpu()))
            intent_losses.append(float(intent_loss.detach().cpu()))
            intent_accs.append(float(intent_acc.detach().cpu()))
    return {
        "loss": float(np.mean(losses)),
        "policy_loss": float(np.mean(policy_losses)),
        "value_loss": float(np.mean(value_losses)),
        "entropy": float(np.mean(entropies)),
        "intent_loss": float(np.mean(intent_losses)),
        "intent_acc": float(np.mean(intent_accs)),
    }
