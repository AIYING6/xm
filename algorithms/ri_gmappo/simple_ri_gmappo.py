from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List

import csv
import hashlib
import json
import random
import subprocess

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
    RELATION_COMMUNICATION,
    RELATION_PERCEPTION,
    RELATION_TASK_SUPPORT,
    UAVIntercept3DConfig,
    UAVIntercept3DEnv,
    UAVPursuitConfig,
    UAVPursuitEnv,
    physical_engagement_ready,
)
from envs.uav_intercept_3d_env import UAV3DType


ROLE_SCOUT_ID = 0
ROLE_RELAY_ID = 1
ROLE_ATTACKER_ID = 2
ROLE_INTERCEPTOR_ID = 3
ROLE_TARGET_ID = 4

CHAIN_AUX_LABEL_NAMES = (
    "perception_active",
    "communication_connected",
    "task_support_active",
    "attack_window_active",
    "fresh_message_available",
)


@dataclass
class RIGMAPPOConfig:
    env_name: str = "2d_pursuit"
    seed: int = 0
    num_blue: int = 3
    blue_types: list[UAV3DType] | None = None
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
    actor_lr: float | None = None
    critic_lr: float | None = None
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip_coef: float = 0.2
    entropy_coef: float = 0.01
    value_coef: float = 0.5
    intent_coef: float = 0.1
    chain_aux_coef: float = 0.0
    chain_aux_warmup_updates: int = 0
    role_gate_prior_strength: float = 0.0
    multi_relation_global_residual_weight: float = 1.0
    intent_balanced_loss: bool = False
    detach_intent: bool = False
    oracle_intent: bool = False
    max_grad_norm: float = 0.5
    target_kl: float | None = None
    critic_warmup_updates: int = 0
    ppo_epochs: int = 4
    minibatch_graphs: int = 256
    eval_interval: int = 10
    eval_episodes: int = 20
    eval_base_seed: int | None = None
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
    target_prior_position: tuple[float, float, float] = (10_000.0, 0.0, 5_000.0)
    max_target_message_age_steps: int = 80
    min_target_confidence: float = 0.2
    safety_proximity_distance: float = 0.0
    safety_proximity_penalty_weight: float = 0.0
    attack_geometry_reward_weight: float = 0.0
    attack_hold_steps: int = 4
    min_success_step: int = 0
    post_loss_chain_reclosure_reward_weight: float = 0.0
    post_loss_chain_reclosure_min_step: int = 0
    # New-project N0/N1 task parameters. Defaults preserve the legacy task.
    mission_neutralization_enabled: bool = False
    guidance_level_action_interface: bool = False
    engage_commit_hold_steps: int = 4
    mission_progress_shaping_enabled: bool = False
    mission_reward_alignment_v1_enabled: bool = False
    target_escape_radius: float | None = None
    mission_max_steps: int = 260
    failed_blue_agent: int = -1
    node_failure_random_prob: float = 0.0
    node_failure_start_step: int = 0
    node_failure_start_random_min: int | None = None
    node_failure_start_random_max: int | None = None
    node_failure_duration_steps: int = 0
    node_failure_duration_random_min: int | None = None
    node_failure_duration_random_max: int | None = None
    device: str = "cpu"
    # --- P3-A OOD eval-side extensions (default no-op, pass through to env) ---
    blue_init_rotation_deg: float = 0.0
    blue_init_spacing_scale: float = 1.0
    target_init_range_scale: float = 1.0
    target_init_bearing_offset_deg: float = 0.0
    comm_topology_mode: str = "none"
    # --- P3-B parameterized target policies (default no-op; used only when
    #     target_policy == "weaving_param" / "break_turn_param") ---
    target_heading_amp: float = 0.45
    target_break_turn_amp_rad: float = 0.5 * 3.141592653589793
    out_dir: str = "results/ri_gmappo"
    save_interval: int = 10
    save_snapshots: bool = False
    # v1.8 protocol-repair switch.  It changes persistence/audit behavior only:
    # the policy, environment, optimizer, and validation population are unchanged.
    validation_event_logging: bool = False
    run_id: str | None = None
    method_label: str | None = None
    protocol_version: str | None = None
    init_checkpoint: str | None = None
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

    def initialize_role_pair_prior(self, pairs: list[tuple[int, int]], strength: float) -> None:
        if not self.use_role_pair_gate or strength <= 0.0:
            return
        with torch.no_grad():
            for receiver_role, sender_role in pairs:
                if receiver_role >= self.num_roles or sender_role >= self.num_roles:
                    continue
                pair_index = receiver_role * self.num_roles + sender_role
                self.role_pair_gate.weight[pair_index].fill_(float(strength))


class MultiRelationGraphEncoder(nn.Module):
    """Separate perception, communication, and task-support message channels."""

    def __init__(
        self,
        hidden_dim: int,
        edge_dim: int,
        num_roles: int,
        num_relations: int = 3,
        use_role_pair_gate: bool = True,
        role_gate_prior_strength: float = 0.0,
        global_residual_weight: float = 1.0,
    ):
        super().__init__()
        if global_residual_weight < 0.0:
            raise ValueError("global_residual_weight must be non-negative")
        self.num_relations = num_relations
        self.global_residual_weight = float(global_residual_weight)
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
        self._initialize_role_pair_priors(role_gate_prior_strength)

    def _initialize_role_pair_priors(self, strength: float) -> None:
        if strength <= 0.0:
            return
        relation_pairs = {
            RELATION_PERCEPTION: [
                (ROLE_SCOUT_ID, ROLE_TARGET_ID),
                (ROLE_RELAY_ID, ROLE_TARGET_ID),
                (ROLE_ATTACKER_ID, ROLE_TARGET_ID),
                (ROLE_INTERCEPTOR_ID, ROLE_TARGET_ID),
            ],
            RELATION_COMMUNICATION: [
                (ROLE_SCOUT_ID, ROLE_RELAY_ID),
                (ROLE_RELAY_ID, ROLE_SCOUT_ID),
                (ROLE_RELAY_ID, ROLE_ATTACKER_ID),
                (ROLE_RELAY_ID, ROLE_INTERCEPTOR_ID),
                (ROLE_ATTACKER_ID, ROLE_RELAY_ID),
                (ROLE_INTERCEPTOR_ID, ROLE_RELAY_ID),
            ],
            RELATION_TASK_SUPPORT: [
                (ROLE_ATTACKER_ID, ROLE_SCOUT_ID),
                (ROLE_INTERCEPTOR_ID, ROLE_SCOUT_ID),
                (ROLE_SCOUT_ID, ROLE_RELAY_ID),
                (ROLE_ATTACKER_ID, ROLE_RELAY_ID),
                (ROLE_INTERCEPTOR_ID, ROLE_RELAY_ID),
                (ROLE_RELAY_ID, ROLE_ATTACKER_ID),
                (ROLE_RELAY_ID, ROLE_INTERCEPTOR_ID),
            ],
        }
        for relation_id, pairs in relation_pairs.items():
            if relation_id >= len(self.layer1):
                continue
            self.layer1[relation_id].initialize_role_pair_prior(pairs, strength)
            self.layer2[relation_id].initialize_role_pair_prior(pairs, strength)

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
        outputs.append(global_output * self.global_residual_weight)
        attentions.append(global_attention * self.global_residual_weight)
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


class ProvenanceConditionedRelationFactorEncoder(nn.Module):
    """Relation factorization whose fusion is explicitly driven by legal conflict.

    This candidate v1.9 encoder intentionally has no union/residual relation
    channel and no static Role-Pair gate.  Its only fusion descriptor is
    constructed from already-masked relation adjacency plus delivered-edge age
    and confidence.  It therefore cannot turn a missing packet into actor
    information.
    """

    def __init__(self, hidden_dim: int, edge_dim: int, num_relations: int = 3):
        super().__init__()
        self.num_relations = num_relations
        self.layer1 = nn.ModuleList(
            [GraphAttentionLayer(hidden_dim, hidden_dim, edge_dim=edge_dim) for _ in range(num_relations)]
        )
        self.layer2 = nn.ModuleList(
            [GraphAttentionLayer(hidden_dim, hidden_dim, edge_dim=edge_dim) for _ in range(num_relations)]
        )
        # Relation support (R), pairwise disagreement (R choose 2), and two
        # delivered-communication quality values (age/confidence).
        self.descriptor_dim = num_relations + (num_relations * (num_relations - 1) // 2) + 2
        self.gate_correction = nn.Sequential(
            nn.Linear(self.descriptor_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, num_relations),
        )
        # The baseline is a learnable, receiver-invariant prior over legal
        # information sources.  It is deliberately separated from the
        # conflict-conditioned correction: no-conflict inputs must recover
        # this baseline rather than an arbitrary equal-weight convention.
        self.baseline_gate_logits = nn.Parameter(torch.zeros(num_relations))
        # The output layer starts at zero, but the subtraction in
        # ``fusion_gate`` additionally enforces Delta(0)=0 after learning.
        nn.init.zeros_(self.gate_correction[-1].weight)
        nn.init.zeros_(self.gate_correction[-1].bias)

    def baseline_gate(self) -> torch.Tensor:
        """Return the explicit, auditable no-conflict fusion baseline."""
        return torch.softmax(self.baseline_gate_logits, dim=-1)

    def conflict_descriptor(
        self,
        relation_adj: torch.Tensor,
        edge_feat: torch.Tensor | None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        if relation_adj.ndim != 4 or relation_adj.shape[1] != self.num_relations:
            raise ValueError(
                f"Expected relation_adj [batch, {self.num_relations}, nodes, nodes], got {tuple(relation_adj.shape)}"
            )
        # In recipient-specific views, node 0 is the receiver.  The descriptor
        # reads only its already legal outgoing relation rows.
        receiver_rows = relation_adj[:, :, 0, :].clamp(0.0, 1.0)
        support = receiver_rows.mean(dim=-1)
        disagreements = []
        for left in range(self.num_relations):
            for right in range(left + 1, self.num_relations):
                disagreements.append((receiver_rows[:, left] - receiver_rows[:, right]).abs().mean(dim=-1))
        disagreement = torch.stack(disagreements, dim=-1)

        communication = receiver_rows[:, RELATION_COMMUNICATION]
        denom = communication.sum(dim=-1).clamp_min(1.0)
        if edge_feat is None or edge_feat.shape[-1] <= 16:
            mean_age = torch.zeros_like(denom)
            mean_confidence = torch.ones_like(denom)
        else:
            # Index 15/16 are the v1.8 legal packet age/confidence fields. If
            # no communication edge exists, their neutral values are used.
            age = edge_feat[:, 0, :, 15].clamp(0.0, 1.0)
            confidence = edge_feat[:, 0, :, 16].clamp(0.0, 1.0)
            mean_age = (age * communication).sum(dim=-1) / denom
            mean_confidence = (confidence * communication).sum(dim=-1) / denom
            no_communication = communication.sum(dim=-1) <= 0.0
            mean_age = torch.where(no_communication, torch.zeros_like(mean_age), mean_age)
            mean_confidence = torch.where(no_communication, torch.ones_like(mean_confidence), mean_confidence)
        descriptor = torch.cat([support, disagreement, mean_age.unsqueeze(-1), mean_confidence.unsqueeze(-1)], dim=-1)
        return descriptor, support

    def fusion_gate(
        self,
        relation_adj: torch.Tensor,
        edge_feat: torch.Tensor | None,
    ) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
        descriptor, support = self.conflict_descriptor(relation_adj, edge_feat)
        # A conflict is a *relative* availability/relation disagreement plus
        # delivered-communication freshness/uncertainty.  Centering support
        # makes equal availability a zero-conflict condition regardless of
        # its absolute density.  Packet metadata remain legal because they
        # are read only on delivered communication edges above.
        centered_support = support - support.mean(dim=-1, keepdim=True)
        packet_age = descriptor[:, -2: -1]
        packet_uncertainty = 1.0 - descriptor[:, -1:]
        conflict_features = torch.cat(
            [centered_support, descriptor[:, self.num_relations:-2], packet_age, packet_uncertainty], dim=-1
        )
        zero_conflict = torch.zeros_like(conflict_features)
        # Subtracting the zero-conflict response guarantees that the gate is
        # exactly the baseline when all legal conflict fields are neutral,
        # even after the correction network has been trained.
        gate_delta = self.gate_correction(conflict_features) - self.gate_correction(zero_conflict)
        baseline_logits = self.baseline_gate_logits.unsqueeze(0).expand_as(gate_delta)
        gate = torch.softmax(baseline_logits + gate_delta, dim=-1)
        return gate, {
            "descriptor": descriptor,
            "relation_support": support,
            "pairwise_disagreement": descriptor[:, self.num_relations:-2],
            "conflict_features": conflict_features,
            "baseline_gate": self.baseline_gate().unsqueeze(0).expand_as(gate),
            "gate_delta": gate_delta,
            "gate": gate,
        }

    def _apply_layer(
        self,
        x: torch.Tensor,
        layers: nn.ModuleList,
        relation_adj: torch.Tensor,
        edge_feat: torch.Tensor | None,
        gate: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        outputs, attentions = [], []
        for relation_id, layer in enumerate(layers):
            output, attention = layer(x, relation_adj[:, relation_id], edge_feat)
            outputs.append(output * gate[:, relation_id].view(-1, 1, 1))
            attentions.append(attention)
        fused = torch.stack(outputs, dim=1).sum(dim=1)
        return torch.tanh(fused + x), torch.stack(attentions, dim=1)

    def forward(
        self,
        x: torch.Tensor,
        relation_adj: torch.Tensor,
        edge_feat: torch.Tensor | None,
    ) -> tuple[torch.Tensor, torch.Tensor, dict[str, torch.Tensor]]:
        gate, diagnostics = self.fusion_gate(relation_adj, edge_feat)
        x, _ = self._apply_layer(x, self.layer1, relation_adj, edge_feat, gate)
        x, attention = self._apply_layer(x, self.layer2, relation_adj, edge_feat, gate)
        return x, attention, diagnostics


class TwoSourcePCRFR2Encoder(nn.Module):
    """Faithful two-source PCRF-R2 encoder with no union or cross-source path."""

    def __init__(self, node_feat_dim: int, role_dim: int, edge_dim: int, hidden_dim: int):
        super().__init__()
        self.p_input = nn.Sequential(nn.Linear(node_feat_dim + role_dim, hidden_dim), nn.Tanh())
        self.c_input = nn.Sequential(nn.Linear(node_feat_dim + role_dim, hidden_dim), nn.Tanh())
        self.p_layer1 = GraphAttentionLayer(hidden_dim, hidden_dim, edge_dim=edge_dim)
        self.p_layer2 = GraphAttentionLayer(hidden_dim, hidden_dim, edge_dim=edge_dim)
        self.c_layer1 = GraphAttentionLayer(hidden_dim, hidden_dim, edge_dim=edge_dim)
        self.c_layer2 = GraphAttentionLayer(hidden_dim, hidden_dim, edge_dim=edge_dim)
        self.baseline_gate_logits = nn.Parameter(torch.zeros(2))
        self.gate_correction = nn.Sequential(
            nn.Linear(4, hidden_dim), nn.Tanh(), nn.Linear(hidden_dim, 2)
        )
        nn.init.zeros_(self.gate_correction[-1].weight)
        nn.init.zeros_(self.gate_correction[-1].bias)

    def baseline_gate(self) -> torch.Tensor:
        return torch.softmax(self.baseline_gate_logits, dim=-1)

    def conflict_descriptor(
        self,
        p_node_feat: torch.Tensor,
        c_node_feat: torch.Tensor,
        p_adj: torch.Tensor,
        c_adj: torch.Tensor,
        c_edge_feat: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        target_index = p_node_feat.shape[1] - 1
        p_available = p_adj[:, 0, target_index].clamp(0.0, 1.0)
        c_available = c_adj[:, 0, target_index].clamp(0.0, 1.0)
        both = p_available * c_available
        # First eleven node fields are target kinematics only. They are zeroed
        # before construction when a source is unavailable.
        disagreement = (p_node_feat[:, target_index, :11] - c_node_feat[:, target_index, :11]).abs().mean(dim=-1)
        disagreement = disagreement * both
        age = c_edge_feat[:, 0, target_index, 15].clamp(0.0, 1.0) * c_available
        uncertainty = (1.0 - c_edge_feat[:, 0, target_index, 16].clamp(0.0, 1.0)) * c_available
        descriptor = torch.stack([p_available - c_available, disagreement, age, uncertainty], dim=-1)
        availability = torch.stack([p_available, c_available], dim=-1)
        return descriptor, availability

    def fusion_gate(
        self,
        p_node_feat: torch.Tensor,
        c_node_feat: torch.Tensor,
        p_adj: torch.Tensor,
        c_adj: torch.Tensor,
        c_edge_feat: torch.Tensor,
    ) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
        descriptor, availability = self.conflict_descriptor(p_node_feat, c_node_feat, p_adj, c_adj, c_edge_feat)
        zero = torch.zeros_like(descriptor)
        delta = self.gate_correction(descriptor) - self.gate_correction(zero)
        logits = self.baseline_gate_logits.unsqueeze(0) + delta
        unnormalized = torch.exp(logits) * availability
        weights = unnormalized / unnormalized.sum(dim=-1, keepdim=True).clamp_min(1e-12)
        return weights, {
            "descriptor": descriptor,
            "availability": availability,
            "baseline_gate": self.baseline_gate().unsqueeze(0).expand_as(weights),
            "gate_delta": delta,
            "gate": weights,
        }

    def forward(
        self,
        p_node_feat: torch.Tensor,
        c_node_feat: torch.Tensor,
        p_edge_feat: torch.Tensor,
        c_edge_feat: torch.Tensor,
        p_adj: torch.Tensor,
        c_adj: torch.Tensor,
        role_feat: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, dict[str, torch.Tensor]]:
        weights, diagnostics = self.fusion_gate(p_node_feat, c_node_feat, p_adj, c_adj, c_edge_feat)
        p = self.p_input(torch.cat([p_node_feat, role_feat], dim=-1))
        c = self.c_input(torch.cat([c_node_feat, role_feat], dim=-1))
        p, p_attn1 = self.p_layer1(p, p_adj, p_edge_feat)
        p, p_attn2 = self.p_layer2(p, p_adj, p_edge_feat)
        c, c_attn1 = self.c_layer1(c, c_adj, c_edge_feat)
        c, c_attn2 = self.c_layer2(c, c_adj, c_edge_feat)
        h_p, h_c = p[:, 0], c[:, 0]
        fused = weights[:, :1] * h_p + weights[:, 1:] * h_c
        diagnostics.update({"h_p": h_p, "h_c": h_c, "fused": fused})
        attention = torch.stack([p_attn1, p_attn2, c_attn1, c_attn2], dim=1)
        return fused, attention, diagnostics


class UnifiedR2SingleGraphEncoder(nn.Module):
    """Single-graph R2 comparator retaining every P/C raw source tag."""

    def __init__(self, node_feat_dim: int, role_dim: int, edge_dim: int, hidden_dim: int, *, graph: bool):
        super().__init__()
        self.graph = graph
        self.input = nn.Sequential(nn.Linear(node_feat_dim * 2 + role_dim, hidden_dim), nn.Tanh())
        if graph:
            self.layer1 = GraphAttentionLayer(hidden_dim, hidden_dim, edge_dim=edge_dim * 2)
            self.layer2 = GraphAttentionLayer(hidden_dim, hidden_dim, edge_dim=edge_dim * 2)
        else:
            self.pool_fuse = nn.Sequential(nn.Linear(hidden_dim * 2, hidden_dim), nn.Tanh())

    def forward(
        self,
        p_node_feat: torch.Tensor,
        c_node_feat: torch.Tensor,
        p_edge_feat: torch.Tensor,
        c_edge_feat: torch.Tensor,
        p_adj: torch.Tensor,
        c_adj: torch.Tensor,
        role_feat: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        x = self.input(torch.cat([p_node_feat, c_node_feat, role_feat], dim=-1))
        union_adj = (p_adj + c_adj).clamp(0.0, 1.0)
        if self.graph:
            edge = torch.cat([p_edge_feat, c_edge_feat], dim=-1)
            x, _ = self.layer1(x, union_adj, edge)
            x, attention = self.layer2(x, union_adj, edge)
            return x[:, 0], attention
        source_valid = (p_node_feat[..., -1:] + c_node_feat[..., -1:]).clamp(0.0, 1.0)
        pooled = (x * source_valid).sum(dim=1) / source_valid.sum(dim=1).clamp_min(1.0)
        fused = self.pool_fuse(torch.cat([x[:, 0], pooled], dim=-1))
        attention = torch.zeros(
            x.shape[0], x.shape[1], x.shape[1], dtype=x.dtype, device=x.device
        )
        return fused, attention


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
        role_gate_prior_strength: float = 0.0,
        multi_relation_global_residual_weight: float = 1.0,
    ):
        super().__init__()
        if graph_encoder not in {
            "no_graph", "matched_nongraph", "single", "multi_relation", "pcrf",
            "pcrf_r2", "single_r2", "matched_nongraph_r2",
        }:
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
        if graph_encoder == "pcrf_r2":
            self.r2_context_encoder = nn.Sequential(nn.Linear(obs_dim, hidden_dim), nn.Tanh())
            self.pcrf_r2_graph = TwoSourcePCRFR2Encoder(node_feat_dim, role_dim, edge_feat_dim, hidden_dim)
        elif graph_encoder in {"single_r2", "matched_nongraph_r2"}:
            self.r2_context_encoder = nn.Sequential(nn.Linear(obs_dim, hidden_dim), nn.Tanh())
            self.r2_unified_graph = UnifiedR2SingleGraphEncoder(
                node_feat_dim, role_dim, edge_feat_dim, hidden_dim, graph=graph_encoder == "single_r2"
            )
        elif graph_encoder == "no_graph":
            self.no_graph_intent_head = nn.Sequential(
                nn.Linear(hidden_dim, hidden_dim),
                nn.Tanh(),
                nn.Linear(hidden_dim, num_intents),
            )
        elif graph_encoder == "matched_nongraph":
            self.matched_edge_pool = nn.Sequential(nn.Linear(edge_feat_dim, hidden_dim), nn.Tanh())
            self.matched_pool_fuse = nn.Sequential(nn.Linear(hidden_dim * 4, hidden_dim), nn.Tanh())
        elif graph_encoder == "single":
            self.gat1 = GraphAttentionLayer(hidden_dim, hidden_dim, edge_dim=edge_feat_dim)
            self.gat2 = GraphAttentionLayer(hidden_dim, hidden_dim, edge_dim=edge_feat_dim)
        elif graph_encoder == "multi_relation":
            self.multi_relation_graph = MultiRelationGraphEncoder(
                hidden_dim,
                edge_feat_dim,
                num_roles,
                use_role_pair_gate=graph_message_ablation != "no_role_pair_gate",
                role_gate_prior_strength=role_gate_prior_strength,
                global_residual_weight=multi_relation_global_residual_weight,
            )
        else:
            self.pcrf_graph = ProvenanceConditionedRelationFactorEncoder(hidden_dim, edge_feat_dim)
        self.last_pcrf_diagnostics: dict[str, torch.Tensor] | None = None
        self.intent_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, num_intents),
        )
        self.chain_aux_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, len(CHAIN_AUX_LABEL_NAMES)),
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
        pcrf_r2: dict[str, torch.Tensor] | None = None,
        intent_label: torch.Tensor | None = None,
        detach_intent: bool = False,
        oracle_intent: bool = False,
        return_chain_aux: bool = False,
    ):
        if self.graph_encoder in {"pcrf_r2", "single_r2", "matched_nongraph_r2"}:
            if pcrf_r2 is None:
                raise ValueError(f"pcrf_r2 source tensors are required when graph_encoder='{self.graph_encoder}'")
            required = {
                "p_node_feat", "c_node_feat", "p_edge_feat", "c_edge_feat", "p_adj", "c_adj", "context", "role",
            }
            missing = sorted(required.difference(pcrf_r2))
            if missing:
                raise ValueError(f"Missing PCRF-R2 source tensors: {missing}")
            r2_role = pcrf_r2["role"].long()
            r2_role_feat = self.role_emb(r2_role)
            if self.graph_encoder == "pcrf_r2":
                graph_feat, attn, self.last_pcrf_diagnostics = self.pcrf_r2_graph(
                    pcrf_r2["p_node_feat"], pcrf_r2["c_node_feat"],
                    pcrf_r2["p_edge_feat"], pcrf_r2["c_edge_feat"],
                    pcrf_r2["p_adj"], pcrf_r2["c_adj"], r2_role_feat,
                )
            else:
                graph_feat, attn = self.r2_unified_graph(
                    pcrf_r2["p_node_feat"], pcrf_r2["c_node_feat"],
                    pcrf_r2["p_edge_feat"], pcrf_r2["c_edge_feat"],
                    pcrf_r2["p_adj"], pcrf_r2["c_adj"], r2_role_feat,
                )
                self.last_pcrf_diagnostics = None
            target_feat = graph_feat.unsqueeze(1)
            intent_logits = self.intent_head(target_feat)
            if not self.use_intent_context:
                intent_context = torch.zeros(
                    graph_feat.shape[0], num_agents, self.intent_emb.embedding_dim,
                    dtype=graph_feat.dtype, device=graph_feat.device,
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
            context_feat = self.r2_context_encoder(pcrf_r2["context"])
            graph_actor_feat = graph_feat.unsqueeze(1).expand(-1, num_agents, -1)
            logits = self.policy_head(torch.cat([context_feat.unsqueeze(1).expand(-1, num_agents, -1), graph_actor_feat, intent_context], dim=-1))
            chain_aux_logits = self.chain_aux_head(graph_feat)
            if return_chain_aux:
                return logits, attn, intent_logits, chain_aux_logits
            return logits, attn, intent_logits
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
            chain_aux_logits = self.chain_aux_head(graph_feat.mean(dim=1))
            if return_chain_aux:
                return logits, attn, intent_logits, chain_aux_logits
            return logits, attn, intent_logits
        if self.graph_encoder == "matched_nongraph":
            receiver_feat = x[:, :1]
            target_feat = x[:, -1:]
            teammate_feat = x[:, 1:-1]
            teammate_valid = node_feat[:, 1:-1, -1:].to(dtype=x.dtype)
            denom = teammate_valid.sum(dim=1, keepdim=True).clamp_min(1.0)
            teammate_mean = (teammate_feat * teammate_valid).sum(dim=1, keepdim=True) / denom
            if edge_feat is None:
                edge_context = torch.zeros_like(receiver_feat)
            else:
                edge_context = self.matched_edge_pool(edge_feat.mean(dim=(1, 2))).unsqueeze(1)
            graph_feat = self.matched_pool_fuse(torch.cat([receiver_feat, teammate_mean, target_feat, edge_context], dim=-1))
            intent_logits = self.intent_head(target_feat)
            attn = torch.zeros(
                obs.shape[0], x.shape[1], x.shape[1], dtype=x.dtype, device=x.device
            )
        elif self.graph_encoder == "single":
            x, _ = self.gat1(x, adj, edge_feat)
            x, attn = self.gat2(x, adj, edge_feat)
        elif self.graph_encoder == "multi_relation":
            if relation_adj is None:
                raise ValueError("relation_adj is required when graph_encoder='multi_relation'")
            x, attn = self.multi_relation_graph(x, relation_adj, edge_feat, role, adj)
        else:
            if relation_adj is None:
                raise ValueError("relation_adj is required when graph_encoder='pcrf'")
            x, attn, self.last_pcrf_diagnostics = self.pcrf_graph(x, relation_adj, edge_feat)

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
        chain_aux_logits = self.chain_aux_head(graph_feat.mean(dim=1))
        if return_chain_aux:
            return logits, attn, intent_logits, chain_aux_logits
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
        role_gate_prior_strength: float = 0.0,
        multi_relation_global_residual_weight: float = 1.0,
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
            role_gate_prior_strength=role_gate_prior_strength,
            multi_relation_global_residual_weight=multi_relation_global_residual_weight,
        )
        self.critic = MLP(share_obs_dim + num_roles, 1, hidden_dim)

    def critic_value(self, share_obs: torch.Tensor, role: torch.Tensor) -> torch.Tensor:
        if role.ndim == 3:
            # Recipient-specific views are ordered with the receiver at node 0.
            agent_role = role[:, :, 0].long().clamp(min=0, max=self.num_roles - 1)
        else:
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
        pcrf_r2: dict[str, torch.Tensor] | None = None,
        action: torch.Tensor | None = None,
        deterministic: bool = False,
        intent_label: torch.Tensor | None = None,
        detach_intent: bool = False,
        oracle_intent: bool = False,
    ):
        recipient_views = node_feat.ndim == 4
        if recipient_views:
            batch_size, num_agents, num_nodes, _ = node_feat.shape
            obs_actor = obs.reshape(batch_size * num_agents, 1, -1)
            node_actor = node_feat.reshape(batch_size * num_agents, num_nodes, -1)
            edge_actor = edge_feat.reshape(batch_size * num_agents, num_nodes, num_nodes, -1) if edge_feat is not None else None
            role_actor = role.reshape(batch_size * num_agents, num_nodes)
            adj_actor = adj.reshape(batch_size * num_agents, num_nodes, num_nodes)
            relation_actor = relation_adj.reshape(batch_size * num_agents, relation_adj.shape[2], num_nodes, num_nodes) if relation_adj is not None else None
            r2_actor = None
            if pcrf_r2 is not None:
                r2_actor = {
                    key: value.reshape(batch_size * num_agents, *value.shape[2:])
                    for key, value in pcrf_r2.items()
                }
            intent_actor = intent_label.reshape(batch_size * num_agents, -1) if intent_label is not None else None
            action_actor = action.reshape(batch_size * num_agents, 1) if action is not None else None
            logits, attn, intent_logits, chain_aux_logits = self.actor(
                obs_actor, node_actor, edge_actor, role_actor, adj_actor, 1,
                relation_adj=relation_actor, intent_label=intent_actor,
                pcrf_r2=r2_actor,
                detach_intent=detach_intent, oracle_intent=oracle_intent,
                return_chain_aux=True,
            )
            action_in = action_actor
            dist = Categorical(logits=logits)
            if action_in is None:
                action_in = torch.argmax(logits, dim=-1) if deterministic else dist.sample()
            log_prob = dist.log_prob(action_in)
            entropy = dist.entropy()
            value = self.critic_value(share_obs, role)
            return (
                action_in.reshape(batch_size, num_agents),
                log_prob.reshape(batch_size, num_agents),
                entropy.reshape(batch_size, num_agents),
                value,
                attn.reshape(batch_size, num_agents, *attn.shape[1:]),
                intent_logits.reshape(batch_size, num_agents, *intent_logits.shape[1:]),
                chain_aux_logits.reshape(batch_size, num_agents, *chain_aux_logits.shape[1:]),
            )
        logits, attn, intent_logits, chain_aux_logits = self.actor(
            obs,
            node_feat,
            edge_feat,
            role,
            adj,
            self.num_agents,
            relation_adj=relation_adj,
            pcrf_r2=pcrf_r2,
            intent_label=intent_label,
            detach_intent=detach_intent,
            oracle_intent=oracle_intent,
            return_chain_aux=True,
        )
        dist = Categorical(logits=logits)
        if action is None:
            action = torch.argmax(logits, dim=-1) if deterministic else dist.sample()
        log_prob = dist.log_prob(action)
        entropy = dist.entropy()
        value = self.critic_value(share_obs, role)
        return action, log_prob, entropy, value, attn, intent_logits, chain_aux_logits


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
        env_kwargs = dict(
                seed=seed,
                num_blue=cfg.num_blue,
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
                target_prior_position=cfg.target_prior_position,
                max_target_message_age_steps=cfg.max_target_message_age_steps,
                min_target_confidence=cfg.min_target_confidence,
                safety_proximity_distance=cfg.safety_proximity_distance,
                safety_proximity_penalty_weight=cfg.safety_proximity_penalty_weight,
                attack_geometry_reward_weight=cfg.attack_geometry_reward_weight,
                attack_hold_steps=cfg.attack_hold_steps,
                mission_neutralization_enabled=cfg.mission_neutralization_enabled,
                guidance_level_action_interface=cfg.guidance_level_action_interface,
                engage_commit_hold_steps=cfg.engage_commit_hold_steps,
                mission_progress_shaping_enabled=cfg.mission_progress_shaping_enabled,
                mission_reward_alignment_v1_enabled=cfg.mission_reward_alignment_v1_enabled,
                target_escape_radius=cfg.target_escape_radius,
                max_steps=cfg.mission_max_steps,
                min_success_step=cfg.min_success_step,
                post_loss_chain_reclosure_reward_weight=cfg.post_loss_chain_reclosure_reward_weight,
                post_loss_chain_reclosure_min_step=cfg.post_loss_chain_reclosure_min_step,
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
                blue_init_rotation_deg=cfg.blue_init_rotation_deg,
                blue_init_spacing_scale=cfg.blue_init_spacing_scale,
                target_init_range_scale=cfg.target_init_range_scale,
                target_init_bearing_offset_deg=cfg.target_init_bearing_offset_deg,
                comm_topology_mode=cfg.comm_topology_mode,
                target_heading_amp=cfg.target_heading_amp,
                target_break_turn_amp_rad=cfg.target_break_turn_amp_rad,
            )
        if cfg.blue_types is not None:
            env_kwargs["blue_types"] = cfg.blue_types
        return UAVIntercept3DEnv(UAVIntercept3DConfig(**env_kwargs))
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
    stacked = {
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
    r2_keys = (
        "pcrf_r2_p_node_feat", "pcrf_r2_c_node_feat", "pcrf_r2_p_edge_feat", "pcrf_r2_c_edge_feat",
        "pcrf_r2_p_adj", "pcrf_r2_c_adj", "pcrf_r2_context", "pcrf_r2_role",
    )
    if all(all(key in graph for key in r2_keys) for graph in graphs):
        stacked.update({
            "pcrf_r2_p_node_feat": np.stack([g["pcrf_r2_p_node_feat"] for g in graphs]).astype(np.float32),
            "pcrf_r2_c_node_feat": np.stack([g["pcrf_r2_c_node_feat"] for g in graphs]).astype(np.float32),
            "pcrf_r2_p_edge_feat": np.stack([g["pcrf_r2_p_edge_feat"] for g in graphs]).astype(np.float32),
            "pcrf_r2_c_edge_feat": np.stack([g["pcrf_r2_c_edge_feat"] for g in graphs]).astype(np.float32),
            "pcrf_r2_p_adj": np.stack([g["pcrf_r2_p_adj"] for g in graphs]).astype(np.float32),
            "pcrf_r2_c_adj": np.stack([g["pcrf_r2_c_adj"] for g in graphs]).astype(np.float32),
            "pcrf_r2_context": np.stack([g["pcrf_r2_context"] for g in graphs]).astype(np.float32),
            "pcrf_r2_role": np.stack([g["pcrf_r2_role"] for g in graphs]).astype(np.int64),
        })
    return stacked


PCRF_R2_GRAPH_FIELDS = {
    "p_node_feat": "pcrf_r2_p_node_feat",
    "c_node_feat": "pcrf_r2_c_node_feat",
    "p_edge_feat": "pcrf_r2_p_edge_feat",
    "c_edge_feat": "pcrf_r2_c_edge_feat",
    "p_adj": "pcrf_r2_p_adj",
    "c_adj": "pcrf_r2_c_adj",
    "context": "pcrf_r2_context",
    "role": "pcrf_r2_role",
}


def pcrf_r2_tensors(graph_obs: dict, device: torch.device) -> dict[str, torch.Tensor] | None:
    """Convert the frozen R2 raw contract to tensors without synthesizing data."""
    if not all(field in graph_obs for field in PCRF_R2_GRAPH_FIELDS.values()):
        return None
    return {
        name: torch.as_tensor(
            graph_obs[field],
            dtype=torch.long if name == "role" else torch.float32,
            device=device,
        )
        for name, field in PCRF_R2_GRAPH_FIELDS.items()
    }


def make_optimizer(agent: RIGMAPPOAgent, cfg: RIGMAPPOConfig) -> optim.Optimizer:
    actor_lr = cfg.actor_lr if cfg.actor_lr is not None else cfg.lr
    critic_lr = cfg.critic_lr if cfg.critic_lr is not None else cfg.lr
    if actor_lr == cfg.lr and critic_lr == cfg.lr:
        return optim.Adam(agent.parameters(), lr=cfg.lr, eps=1e-5)

    actor_param_ids = {id(param) for param in agent.actor.parameters()}
    critic_param_ids = {id(param) for param in agent.critic.parameters()}
    other_params = [
        param
        for param in agent.parameters()
        if id(param) not in actor_param_ids and id(param) not in critic_param_ids
    ]
    param_groups = [
        {"params": agent.actor.parameters(), "lr": actor_lr},
        {"params": agent.critic.parameters(), "lr": critic_lr},
    ]
    if other_params:
        param_groups.append({"params": other_params, "lr": actor_lr})
    return optim.Adam(param_groups, eps=1e-5)


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def current_git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNAVAILABLE"


def km_rmst_from_event_records(records: list[dict], tau: float) -> float:
    """Kaplan-Meier restricted mean time to stable establishment.

    Event times and censor times are measured from the frozen failure onset.  The
    implementation groups ties, which is needed for deterministic integer-step
    episodes and avoids treating same-step events as ordered observations.
    """
    observations: list[tuple[float, int]] = []
    for record in records:
        event = bool(record["event_observed"])
        time = float(record["event_time"] if event else record["censor_time"])
        observations.append((min(max(0.0, time), float(tau)), int(event and time <= tau)))
    observations.sort(key=lambda item: item[0])
    at_risk = len(observations)
    survival, previous, area = 1.0, 0.0, 0.0
    index = 0
    while index < len(observations) and previous < tau:
        time = observations[index][0]
        area += survival * (time - previous)
        end = index
        events = 0
        while end < len(observations) and observations[end][0] == time:
            events += observations[end][1]
            end += 1
        if time < tau and at_risk > 0:
            survival *= (at_risk - events) / at_risk
        at_risk -= end - index
        previous = time
        index = end
    if previous < tau:
        area += survival * (tau - previous)
    return float(area)


def restricted_mean_time_to_establishment(records: list[dict], tau: float) -> float:
    """Complete-follow-up RMTE for the frozen v1.9 terminal-outcome estimand.

    There is no random loss to follow-up in a simulated episode.  An
    establishment observed by ``tau`` contributes its event time; terminal
    failure before establishment and an episode still active at the restriction
    horizon both contribute ``tau``.  This deliberately does *not* censor an
    irreversible collision/constraint outcome from later event risk sets.
    """
    if not records:
        raise ValueError("event record set is empty")
    values = []
    for record in records:
        event_time = float(record.get("event_time", -1))
        event = bool(record.get("event_observed")) and 0.0 <= event_time <= tau
        values.append(event_time if event else float(tau))
    return float(np.mean(values))


def restricted_mean_time_to_physical_engagement(records: list[dict], tau: float) -> float:
    """Complete-follow-up RMPE for the frozen evaluator-only endpoint."""
    if not records:
        raise ValueError("physical-engagement record set is empty")
    values = []
    for record in records:
        event_time = float(record.get("physical_event_time", -1))
        event = bool(record.get("physical_event_observed")) and 0.0 <= event_time <= tau
        values.append(event_time if event else float(tau))
    return float(np.mean(values))


def establishment_cumulative_incidence(records: list[dict], tau: float) -> float:
    """Observed cumulative incidence of establishment by ``tau``.

    All simulated episodes are followed until establishment, a terminal outcome,
    or their fixed horizon. Thus the empirical fraction is the appropriate CIF
    for the current complete-follow-up environment; no ordinary KM censoring is
    used.
    """
    if not records:
        raise ValueError("event record set is empty")
    return float(np.mean([
        bool(record.get("event_observed"))
        and 0.0 <= float(record.get("event_time", -1)) <= tau
        for record in records
    ]))


def physical_engagement_cumulative_incidence(records: list[dict], tau: float) -> float:
    if not records:
        raise ValueError("physical-engagement record set is empty")
    return float(np.mean([
        bool(record.get("physical_event_observed"))
        and 0.0 <= float(record.get("physical_event_time", -1)) <= tau
        for record in records
    ]))


def terminal_failure_cumulative_incidence(records: list[dict], tau: float) -> float:
    if not records:
        raise ValueError("event record set is empty")
    return float(np.mean([
        bool(record.get("terminal_failure_observed"))
        and 0.0 <= float(record.get("terminal_failure_time", -1)) <= tau
        for record in records
    ]))


def active_not_established_probability(records: list[dict], tau: float) -> float:
    establishment = establishment_cumulative_incidence(records, tau)
    terminal = terminal_failure_cumulative_incidence(records, tau)
    active = 1.0 - establishment - terminal
    if active < -1e-8:
        raise ValueError("establishment and terminal outcomes overlap before tau")
    return float(max(0.0, active))


def rmte_selector_key(metrics: dict, update: int) -> tuple[float, float, float, float, int]:
    """Frozen v1.9 P0-A selector; lower lexicographic tuple is preferred."""
    return (
        float(metrics["eval_rmte80"]),
        -float(metrics["eval_establishment_probability80"]),
        float(metrics["eval_terminal_failure_incidence80"]),
        float(metrics["eval_rmte220"]),
        int(update),
    )


def termination_reason(info: dict) -> str:
    if float(info.get("success", 0.0)) > 0.5:
        return "success"
    if float(info.get("collision", 0.0)) > 0.5:
        return "collision"
    if float(info.get("constraint_violation", 0.0)) > 0.5:
        return "constraint_violation"
    if float(info.get("timeout", 0.0)) > 0.5:
        return "timeout"
    return "terminal_unspecified"


def summarize_validation_event_records(records: list[dict]) -> dict:
    if not records:
        raise ValueError("validation event record set is empty")
    return {
        "eval_rmte80": restricted_mean_time_to_establishment(records, 80.0),
        "eval_establishment_probability80": establishment_cumulative_incidence(records, 80.0),
        "eval_terminal_failure_incidence80": terminal_failure_cumulative_incidence(records, 80.0),
        "eval_active_not_established_probability80": active_not_established_probability(records, 80.0),
        "eval_rmte220": restricted_mean_time_to_establishment(records, 220.0),
        "eval_establishment_probability220": establishment_cumulative_incidence(records, 220.0),
        "eval_terminal_failure_incidence220": terminal_failure_cumulative_incidence(records, 220.0),
        "eval_active_not_established_probability220": active_not_established_probability(records, 220.0),
        "eval_rmpe80": restricted_mean_time_to_physical_engagement(records, 80.0),
        "eval_physical_engagement_probability80": physical_engagement_cumulative_incidence(records, 80.0),
        "eval_rmpe220": restricted_mean_time_to_physical_engagement(records, 220.0),
        "eval_physical_engagement_probability220": physical_engagement_cumulative_incidence(records, 220.0),
    }


def write_immutable_validation_records(
    out_dir: Path,
    update: int,
    records: list[dict],
    metrics: dict,
    snapshot_path: Path,
    snapshot_sha256: str,
    cfg: RIGMAPPOConfig,
) -> dict:
    """Persist one validation point once; refusing overwrites makes the record immutable."""
    point_dir = out_dir / "validation" / f"update_{update:04d}"
    point_dir.mkdir(parents=True, exist_ok=True)
    records_path = point_dir / "episode_event_records.csv"
    summary_path = point_dir / "summary.json"
    if records_path.exists() or summary_path.exists():
        raise FileExistsError(f"refusing to overwrite immutable validation point: {point_dir}")
    fields = [
        "episode_seed", "failure_onset_step", "event_observed",
        "first_stable_establishment_step", "event_time", "termination_reason",
        "terminal_failure_observed", "terminal_failure_time", "terminal_step",
        "physical_event_observed", "first_stable_physical_engagement_step", "physical_event_time",
    ]
    with records_path.open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows([{name: record[name] for name in fields} for record in records])
    summary = {
        "protocol_version": cfg.protocol_version,
        "run_id": cfg.run_id,
        "method": cfg.method_label,
        "training_seed": cfg.seed,
        "update": update,
        "validation_base_seed": cfg.eval_base_seed,
        "episodes": len(records),
        "snapshot_file": snapshot_path.name,
        "snapshot_sha256": snapshot_sha256,
        **{key: float(value) for key, value in metrics.items()},
    }
    with summary_path.open("x", encoding="utf-8") as f:
        json.dump(summary, f, sort_keys=True, indent=2)
        f.write("\n")
    manifest_row = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "protocol_version": cfg.protocol_version,
        "run_id": cfg.run_id,
        "method": cfg.method_label,
        "training_seed": cfg.seed,
        "update": update,
        "git_commit": current_git_commit(),
        "snapshot_path": str(snapshot_path.name),
        "snapshot_sha256": snapshot_sha256,
        "episode_records_path": str(records_path.relative_to(out_dir)),
        "episode_records_sha256": sha256_file(records_path),
        "summary_path": str(summary_path.relative_to(out_dir)),
        "summary_sha256": sha256_file(summary_path),
    }
    manifest_path = out_dir / "snapshot_manifest.jsonl"
    with manifest_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(manifest_row, sort_keys=True) + "\n")
    return summary


def save_immutable_validation_snapshot(
    out_dir: Path,
    agent: RIGMAPPOAgent,
    optimizer: optim.Optimizer,
    update: int,
    best_eval_key: tuple[float, float, float, float] | None,
    cfg: RIGMAPPOConfig,
) -> tuple[Path, str]:
    snapshot_path = out_dir / f"actor_critic_update_{update:04d}.pt"
    if snapshot_path.exists():
        raise FileExistsError(f"refusing to overwrite immutable snapshot: {snapshot_path}")
    created_at = datetime.now(timezone.utc).isoformat()
    payload = {
        "model_state": agent.state_dict(),
        "optimizer_state": optimizer.state_dict(),
        "update": int(update),
        "metadata": {
            "method": cfg.method_label,
            "training_seed": cfg.seed,
            "update": int(update),
            "git_commit": current_git_commit(),
            "protocol_version": cfg.protocol_version,
            "run_id": cfg.run_id,
            "created_at_utc": created_at,
        },
    }
    if best_eval_key is not None:
        payload["best_eval_key_before_update"] = tuple(float(x) for x in best_eval_key)
    torch.save(payload, snapshot_path)
    snapshot_sha = sha256_file(snapshot_path)
    metadata_path = out_dir / f"actor_critic_update_{update:04d}.metadata.json"
    if metadata_path.exists():
        raise FileExistsError(f"refusing to overwrite immutable metadata: {metadata_path}")
    with metadata_path.open("x", encoding="utf-8") as f:
        json.dump({**payload["metadata"], "snapshot_file": snapshot_path.name, "sha256": snapshot_sha}, f, sort_keys=True, indent=2)
        f.write("\n")
    return snapshot_path, snapshot_sha


def eval_policy(
    agent: RIGMAPPOAgent,
    cfg: RIGMAPPOConfig,
    base_seed: int = 10_000,
    return_event_records: bool = False,
) -> dict | tuple[dict, list[dict]]:
    device = torch.device(cfg.device)
    records = []
    event_records: list[dict] = []
    intent_correct, intent_total = 0, 0
    agent.eval()
    with torch.no_grad():
        for ep in range(cfg.eval_episodes):
            env = make_env(cfg, base_seed + ep, training=False)
            obs, share_obs, graph = env.reset()
            post_failure_chain_step: int | None = None
            post_failure_physical_step: int | None = None
            physical_hold = 0
            terminal_info: dict | None = None
            while True:
                g = stack_graphs([graph])
                actions, _, _, _, _, intent_logits, _ = agent.get_action_and_value(
                    torch.as_tensor(obs[None, ...], dtype=torch.float32, device=device),
                    torch.as_tensor(g["node_feat"], dtype=torch.float32, device=device),
                    torch.as_tensor(g["edge_feat"], dtype=torch.float32, device=device),
                    torch.as_tensor(g["role"], dtype=torch.long, device=device),
                    torch.as_tensor(g["adj"], dtype=torch.float32, device=device),
                    torch.as_tensor(share_obs[None, ...], dtype=torch.float32, device=device),
                    relation_adj=torch.as_tensor(g["relation_adj"], dtype=torch.float32, device=device),
                    pcrf_r2=pcrf_r2_tensors(g, device),
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
                if int(info.get("step", 0)) >= cfg.node_failure_start_step:
                    physical_ready = any(
                        physical_engagement_ready(env, agent_id) for agent_id in range(env.num_agents)
                    )
                    physical_hold = physical_hold + 1 if physical_ready else 0
                    if physical_hold >= 4 and post_failure_physical_step is None:
                        post_failure_physical_step = int(info["step"]) - 3
                if (
                    int(info.get("step", 0)) >= cfg.node_failure_start_step
                    and float(info.get("chain_closed", 0.0)) > 0.5
                    and post_failure_chain_step is None
                ):
                    post_failure_chain_step = int(info["step"])
                if np.all(dones):
                    records.append(info)
                    terminal_info = info
                    break
            if return_event_records:
                assert terminal_info is not None
                terminal_step = int(terminal_info["step"])
                onset = int(cfg.node_failure_start_step)
                event_observed = post_failure_chain_step is not None
                event_time = (post_failure_chain_step - onset) if event_observed else -1
                physical_event_observed = post_failure_physical_step is not None
                physical_event_time = (post_failure_physical_step - onset) if physical_event_observed else -1
                reason = termination_reason(terminal_info)
                terminal_failure = (not event_observed) and reason in {
                    "collision", "constraint_violation", "target_escape", "mission_failure",
                }
                event_records.append({
                    "episode_seed": int(base_seed + ep),
                    "failure_onset_step": onset,
                    "event_observed": int(event_observed),
                    "first_stable_establishment_step": int(post_failure_chain_step) if event_observed else -1,
                    "event_time": int(event_time),
                    "termination_reason": reason,
                    "terminal_failure_observed": int(terminal_failure),
                    "terminal_failure_time": int(max(0, terminal_step - onset)) if terminal_failure else -1,
                    "terminal_step": terminal_step,
                    "physical_event_observed": int(physical_event_observed),
                    "first_stable_physical_engagement_step": int(post_failure_physical_step) if physical_event_observed else -1,
                    "physical_event_time": int(physical_event_time),
                })
    agent.train()
    metrics = {
        "eval_success_rate": float(np.mean([r["success"] for r in records])),
        "eval_collision_rate": float(np.mean([r["collision"] for r in records])),
        "eval_timeout_rate": float(np.mean([r["timeout"] for r in records])),
        "eval_avg_steps": float(np.mean([r["step"] for r in records])),
        "eval_avg_distance": float(np.mean([r.get("mean_distance", r.get("mean_range", 0.0)) for r in records])),
        "eval_intent_acc": float(intent_correct / intent_total) if intent_total else float("nan"),
    }
    if return_event_records:
        metrics.update(summarize_validation_event_records(event_records))
        return metrics, event_records
    return metrics


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
        role_gate_prior_strength=cfg.role_gate_prior_strength,
        multi_relation_global_residual_weight=cfg.multi_relation_global_residual_weight,
        num_roles=max(4, int(np.max(sample_graph["role"])) + 1),
    ).to(device)
    optimizer = make_optimizer(agent, cfg)
    if cfg.init_checkpoint:
        load_matching_state_dict(agent, cfg.init_checkpoint, device)
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
        "chain_aux_loss",
        "chain_aux_acc",
        "chain_aux_effective_coef",
        "approx_kl",
        "clip_fraction",
        "grad_norm",
        "explained_variance",
        "ppo_epochs_ran",
        "critic_warmup_active",
        "train_avg_reward",
        "eval_success_rate",
        "eval_collision_rate",
        "eval_timeout_rate",
        "eval_avg_steps",
        "eval_avg_distance",
        "eval_intent_acc",
        "eval_rmte80",
        "eval_establishment_probability80",
        "eval_terminal_failure_incidence80",
        "eval_active_not_established_probability80",
        "eval_rmte220",
        "eval_establishment_probability220",
        "eval_terminal_failure_incidence220",
        "eval_active_not_established_probability220",
        "eval_rmpe80",
        "eval_physical_engagement_probability80",
        "eval_rmpe220",
        "eval_physical_engagement_probability220",
    ]
    write_header = not (cfg.append_log and log_path.exists())
    mode = "a" if cfg.append_log else "w"
    with log_path.open(mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        f.flush()
        best_eval_key: tuple[float, float, float, float] | None = None
        for local_update in range(1, cfg.updates + 1):
            update = cfg.update_offset + local_update
            batch = collect_rollout(agent, envs, obs, share_obs, graph_obs, cfg, device)
            obs, share_obs, graph_obs = batch["next_obs"], batch["next_share_obs"], batch["next_graph_obs"]
            train_info = update_policy(agent, optimizer, batch, cfg, device, update)
            row = {"update": update, **train_info, "train_avg_reward": float(batch["rewards"].mean())}
            if update % cfg.eval_interval == 0 or update == 1:
                eval_base_seed = cfg.eval_base_seed if cfg.eval_base_seed is not None else 10_000 + update * 100
                snapshot_path: Path | None = None
                snapshot_sha256: str | None = None
                if cfg.validation_event_logging:
                    if not cfg.save_snapshots:
                        raise ValueError("validation_event_logging requires immutable --save-snapshots")
                    snapshot_path, snapshot_sha256 = save_immutable_validation_snapshot(
                        out_dir, agent, optimizer, update, best_eval_key, cfg
                    )
                    eval_result = eval_policy(
                        agent, cfg, base_seed=eval_base_seed, return_event_records=True
                    )
                    eval_metrics, event_records = eval_result
                    write_immutable_validation_records(
                        out_dir,
                        update,
                        event_records,
                        eval_metrics,
                        snapshot_path,
                        snapshot_sha256,
                        cfg,
                    )
                    row.update(eval_metrics)
                else:
                    row.update(eval_policy(agent, cfg, base_seed=eval_base_seed))
                print(row, flush=True)
                if cfg.validation_event_logging:
                    # P0-A frozen selector: lower RMTE80; then higher
                    # establishment incidence; lower terminal-failure incidence;
                    # lower RMTE220; then earlier update.
                    selector_key = rmte_selector_key(row, update)
                    incumbent_key = None if best_eval_key is None else (*best_eval_key, -1)
                    is_better = incumbent_key is None or selector_key < incumbent_key
                    new_best_eval_key = selector_key[:4]
                else:
                    legacy_key = (
                        float(row["eval_success_rate"]),
                        -float(row["eval_collision_rate"]),
                        -float(row["eval_timeout_rate"]),
                        -float(row["eval_avg_steps"]),
                    )
                    is_better = best_eval_key is None or legacy_key > best_eval_key
                    new_best_eval_key = legacy_key
                if is_better:
                    best_eval_key = new_best_eval_key
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
                        "eval_rmte80": "",
                        "eval_establishment_probability80": "",
                        "eval_terminal_failure_incidence80": "",
                        "eval_active_not_established_probability80": "",
                        "eval_rmte220": "",
                        "eval_establishment_probability220": "",
                        "eval_terminal_failure_incidence220": "",
                        "eval_active_not_established_probability220": "",
                        "eval_rmpe80": "",
                        "eval_physical_engagement_probability80": "",
                        "eval_rmpe220": "",
                        "eval_physical_engagement_probability220": "",
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
                if cfg.save_snapshots and not cfg.validation_event_logging:
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
    r2_buf: dict[str, list[np.ndarray]] = {name: [] for name in PCRF_R2_GRAPH_FIELDS}
    action_buf, logp_buf, reward_buf, done_buf, value_buf = [], [], [], [], []

    for _ in range(cfg.rollout_steps):
        with torch.no_grad():
            actions, logp, _, values, _, _, _ = agent.get_action_and_value(
                torch.as_tensor(obs, dtype=torch.float32, device=device),
                torch.as_tensor(graph_obs["node_feat"], dtype=torch.float32, device=device),
                torch.as_tensor(graph_obs["edge_feat"], dtype=torch.float32, device=device),
                torch.as_tensor(graph_obs["role"], dtype=torch.long, device=device),
                torch.as_tensor(graph_obs["adj"], dtype=torch.float32, device=device),
                torch.as_tensor(share_obs, dtype=torch.float32, device=device),
                relation_adj=torch.as_tensor(graph_obs["relation_adj"], dtype=torch.float32, device=device),
                pcrf_r2=pcrf_r2_tensors(graph_obs, device),
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
        for name, field in PCRF_R2_GRAPH_FIELDS.items():
            if field in graph_obs:
                r2_buf[name].append(graph_obs[field].copy())
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
    rollout = {
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
    if all(len(values) == cfg.rollout_steps for values in r2_buf.values()):
        rollout["pcrf_r2"] = {
            name: np.asarray(values, dtype=np.int64 if name == "role" else np.float32)
            for name, values in r2_buf.items()
        }
    return rollout


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


def effective_chain_aux_coef(cfg: RIGMAPPOConfig, update: int) -> float:
    # The historical auxiliary target includes Task-Support. It must remain
    # disabled for the two-source R2 line so it cannot become an implicit third
    # relation through gradient flow.
    if cfg.graph_encoder in {"pcrf_r2", "single_r2", "matched_nongraph_r2"}:
        return 0.0
    if cfg.env_name != "3d_intercept" or cfg.chain_aux_coef <= 0.0:
        return 0.0
    if cfg.chain_aux_warmup_updates > 0 and update <= cfg.chain_aux_warmup_updates:
        return 0.0
    return float(cfg.chain_aux_coef)


def build_chain_aux_targets(node_feat: torch.Tensor, edge_feat: torch.Tensor, relation_adj: torch.Tensor, num_agents: int) -> torch.Tensor:
    """Build actor-visible kill-chain state labels from current graph observations."""
    blue_slice = slice(0, num_agents)
    target_index = num_agents
    perception_active = relation_adj[:, RELATION_PERCEPTION, blue_slice, target_index].amax(dim=1)

    comm_adj = relation_adj[:, RELATION_COMMUNICATION, blue_slice, blue_slice]
    if num_agents > 1:
        eye = torch.eye(num_agents, dtype=torch.bool, device=comm_adj.device).unsqueeze(0)
        off_diag = comm_adj.masked_select(~eye).reshape(comm_adj.shape[0], num_agents, num_agents - 1)
        communication_connected = off_diag.mean(dim=(1, 2)).clamp(0.0, 1.0)
    else:
        communication_connected = torch.ones_like(perception_active)

    task_support_active = relation_adj[:, RELATION_TASK_SUPPORT, blue_slice, blue_slice].amax(dim=(1, 2))
    attack_window_active = node_feat[:, blue_slice, 17].amax(dim=1).clamp(0.0, 1.0)
    message_age = edge_feat[:, blue_slice, blue_slice, 15]
    fresh_message_available = (1.0 - message_age).clamp(0.0, 1.0).amax(dim=(1, 2))

    return torch.stack(
        (
            perception_active,
            communication_connected,
            task_support_active,
            attack_window_active,
            fresh_message_available,
        ),
        dim=-1,
    )


def update_policy(agent: RIGMAPPOAgent, optimizer: optim.Optimizer, batch: dict, cfg: RIGMAPPOConfig, device, update: int):
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
    r2_batch = None
    if "pcrf_r2" in batch:
        r2_batch = {
            name: torch.as_tensor(
                values.reshape(num_graphs, *values.shape[2:]),
                dtype=torch.long if name == "role" else torch.float32,
                device=device,
            )
            for name, values in batch["pcrf_r2"].items()
        }
    intent_label = torch.as_tensor(batch["intent_label"].reshape(num_graphs, -1), dtype=torch.long, device=device)
    share_obs = torch.as_tensor(batch["share_obs"].reshape(num_graphs, num_agents, -1), dtype=torch.float32, device=device)
    actions = torch.as_tensor(batch["actions"].reshape(num_graphs, num_agents), dtype=torch.long, device=device)
    old_logp = torch.as_tensor(batch["logp"].reshape(num_graphs, num_agents), dtype=torch.float32, device=device)
    advantages = torch.as_tensor(batch["advantages"].reshape(num_graphs, num_agents), dtype=torch.float32, device=device)
    returns = torch.as_tensor(batch["returns"].reshape(num_graphs, num_agents), dtype=torch.float32, device=device)
    advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
    chain_aux_coef = effective_chain_aux_coef(cfg, update)
    critic_warmup_active = update <= cfg.critic_warmup_updates

    losses, policy_losses, value_losses, entropies, intent_losses, intent_accs = [], [], [], [], [], []
    chain_aux_losses, chain_aux_accs = [], []
    approx_kls, clip_fractions, grad_norms, explained_variances = [], [], [], []
    indices = np.arange(num_graphs)
    epochs_ran = 0
    stop_ppo = False
    for _ in range(cfg.ppo_epochs):
        epochs_ran += 1
        np.random.shuffle(indices)
        for start in range(0, num_graphs, cfg.minibatch_graphs):
            mb = indices[start : start + cfg.minibatch_graphs]
            _, new_logp, entropy, values, _, intent_logits, chain_aux_logits = agent.get_action_and_value(
                obs[mb],
                node_feat[mb],
                edge_feat[mb],
                role[mb],
                adj[mb],
                share_obs[mb],
                relation_adj=relation_adj[mb],
                pcrf_r2={name: value[mb] for name, value in r2_batch.items()} if r2_batch is not None else None,
                action=actions[mb],
                intent_label=intent_label[mb],
                detach_intent=cfg.detach_intent,
                oracle_intent=cfg.oracle_intent,
            )
            log_ratio = new_logp - old_logp[mb]
            ratio = log_ratio.exp()
            with torch.no_grad():
                approx_kl = ((ratio - 1.0) - log_ratio).mean()
                clip_fraction = ((ratio - 1.0).abs() > cfg.clip_coef).float().mean()
                returns_mb = returns[mb]
                value_error_var = torch.var(returns_mb - values)
                returns_var = torch.var(returns_mb)
                explained_variance = 1.0 - value_error_var / (returns_var + 1e-8)
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
            if chain_aux_coef > 0.0:
                chain_aux_target = build_chain_aux_targets(node_feat[mb], edge_feat[mb], relation_adj[mb], num_agents)
                chain_aux_loss = F.binary_cross_entropy_with_logits(chain_aux_logits, chain_aux_target)
                chain_aux_pred = (torch.sigmoid(chain_aux_logits) >= 0.5).to(chain_aux_target.dtype)
                chain_aux_acc = (chain_aux_pred == (chain_aux_target >= 0.5).to(chain_aux_target.dtype)).float().mean()
            else:
                chain_aux_loss = torch.zeros((), device=device)
                chain_aux_acc = torch.zeros((), device=device)
            if critic_warmup_active:
                loss = cfg.value_coef * value_loss
            else:
                loss = (
                    policy_loss
                    + cfg.value_coef * value_loss
                    - cfg.entropy_coef * entropy_loss
                    + effective_intent_coef(cfg) * intent_loss
                    + chain_aux_coef * chain_aux_loss
                )

            optimizer.zero_grad()
            loss.backward()
            grad_norm = nn.utils.clip_grad_norm_(agent.parameters(), cfg.max_grad_norm)
            optimizer.step()

            losses.append(float(loss.detach().cpu()))
            policy_losses.append(float(policy_loss.detach().cpu()))
            value_losses.append(float(value_loss.detach().cpu()))
            entropies.append(float(entropy_loss.detach().cpu()))
            intent_losses.append(float(intent_loss.detach().cpu()))
            intent_accs.append(float(intent_acc.detach().cpu()))
            chain_aux_losses.append(float(chain_aux_loss.detach().cpu()))
            chain_aux_accs.append(float(chain_aux_acc.detach().cpu()))
            approx_kls.append(float(approx_kl.detach().cpu()))
            clip_fractions.append(float(clip_fraction.detach().cpu()))
            grad_norms.append(float(grad_norm.detach().cpu()))
            explained_variances.append(float(explained_variance.detach().cpu()))
        if cfg.target_kl is not None and approx_kls and float(np.mean(approx_kls[-max(1, num_graphs // cfg.minibatch_graphs) :])) > cfg.target_kl:
            stop_ppo = True
        if stop_ppo:
            break
    return {
        "loss": float(np.mean(losses)),
        "policy_loss": float(np.mean(policy_losses)),
        "value_loss": float(np.mean(value_losses)),
        "entropy": float(np.mean(entropies)),
        "intent_loss": float(np.mean(intent_losses)),
        "intent_acc": float(np.mean(intent_accs)),
        "chain_aux_loss": float(np.mean(chain_aux_losses)),
        "chain_aux_acc": float(np.mean(chain_aux_accs)),
        "chain_aux_effective_coef": chain_aux_coef,
        "approx_kl": float(np.mean(approx_kls)),
        "clip_fraction": float(np.mean(clip_fractions)),
        "grad_norm": float(np.mean(grad_norms)),
        "explained_variance": float(np.mean(explained_variances)),
        "ppo_epochs_ran": epochs_ran,
        "critic_warmup_active": float(critic_warmup_active),
    }
