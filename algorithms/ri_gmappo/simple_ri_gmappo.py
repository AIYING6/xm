from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

import copy
import csv
import hashlib
import json
import math
import random
from contextlib import nullcontext

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
)
from algorithms.ri_gmappo.topology_curriculum import TopologyCurriculum
from algorithms.ri_gmappo.fixed_condition_mixture import FixedConditionMixture
from algorithms.ri_gmappo.drtp_topology_sampler import (
    ADAPT_INTERVAL,
    ALL_GROUPS,
    FAILURE_GROUPS,
    GROUP_MEMBERS,
    NOMINAL_GROUP,
    WARMUP_UPDATES,
    DRTPSelection,
    DRTPTopologySampler,
    PairedProbeTopologySampler,
)
from algorithms.ri_gmappo.snr_topology_sampler import StaticNonuniformTopologySampler
from algorithms.ri_gmappo.drtp_topology_sampler import EGTRTopologySampler
from algorithms.ri_gmappo.rng_streams import RNGStreams
from algorithms.ri_gmappo.tcr_topology_sampler import FixedStratifiedTopologySampler
from algorithms.ri_gmappo.failure_aware_telemetry import FailureAwareTelemetryWriter
from algorithms.ri_gmappo.group_credit_telemetry import (
    CONFLICT_FIELDS as GROUP_CREDIT_CONFLICT_FIELDS,
    GROUP_FIELDS as GROUP_CREDIT_FIELDS,
    summarize_group_credit_assignment,
)


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

# RSG-TC deliberately uses only receiver-local edge state.  These indices are
# the frozen 3D edge-feature contract: normalized distance, sensing validity,
# communication validity, task-support validity, message age, and confidence.
RSG_TC_EDGE_FEATURE_INDICES = (3, 11, 12, 13, 15, 16)
RSG_TC_RELATION_COUNT = 3

# D4 frozen numerical resolution for the opt-in KL-boundary projection.  This
# is an implementation tolerance, not a scientific hyperparameter or sweep.
POLICY_KL_BACKTRACK_BISECTION_STEPS = 24


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
    role_gate_mode: str = "relation_conditioned"
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
    # Stable-v2 opt-in actor update transaction.  The default preserves every
    # historical PPO path.  Guard modes make target_kl a hard post-step
    # empirical-KL boundary rather than only an epoch-stop hint.
    policy_update_guard_mode: str = "none"
    critic_warmup_updates: int = 0
    ppo_epochs: int = 4
    minibatch_graphs: int = 256
    eval_interval: int = 10
    eval_episodes: int = 20
    eval_base_seed: int | None = None
    evaluation_enabled: bool = True
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
    relay_dependent_task: bool = False
    business_grounded_geometry: bool = False
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
    # Fixed diagnostic milestones; never used for checkpoint selection.
    milestone_updates: dict[int, str] | None = None
    init_checkpoint: str | None = None
    resume: str | None = None
    update_offset: int = 0
    append_log: bool = False
    role_gate_telemetry: bool = False
    # TP-0: training-condition curriculum only; "none" preserves legacy behavior.
    topology_curriculum_schedule: str = "none"
    topology_curriculum_seed: int | None = None
    topology_curriculum_logging: bool = False
    # Static episode-level nominal/F0 mix.  This is not a curriculum.
    fixed_f0_probability: float | None = None
    fixed_condition_mixture_seed: int | None = None
    fixed_condition_mixture_logging: bool = False
    # Frozen DRTP/UTR reset-time topology sampler. It changes no policy input,
    # reward, PPO objective, or environment semantics beyond selected failure
    # onset/duration from the pre-registered condition set.
    drtp_sampler_mode: str = "none"
    drtp_sampler_seed: int | None = None
    drtp_sampler_logging: bool = False
    # The sampler's protocol horizon can differ from this invocation's local
    # update count during an exact runtime continuation.
    drtp_sampler_total_updates: int | None = None
    # PP-DRTP uses deterministic paired probe rollouts only to update sampler
    # evidence. These fields are inert unless ``drtp_sampler_mode=pp_drtp``.
    pp_drtp_probe_count: int = 4
    pp_drtp_probe_seed: int | None = None
    # Phase-B TCR/SPC fixed-exposure condition sampler and actor-only update
    # mode.  Both are training-side metadata; neither changes policy inputs.
    fixed_stratified_topology_sampler: bool = False
    fixed_stratified_topology_sampler_seed: int | None = None
    actor_gradient_mode: str = "standard"
    actor_gradient_logging: bool = False
    # Zero-training failure-mechanism diagnosis.  The writer is a read-only
    # sink and never enters actor/critic inputs or reward/sampler decisions.
    failure_aware_telemetry: bool = False
    failure_telemetry_pre_steps: int = 20
    failure_telemetry_post_steps: int = 60
    failure_telemetry_pseudo_onset: int = 44
    # B5 read-only credit-assignment telemetry.  It adds deterministic
    # pre-update diagnostics only and is never consumed by PPO or the sampler.
    group_credit_telemetry: bool = False
    group_credit_telemetry_interval: int = 20
    # TC-SAM-UTR: standard Euclidean SAM applied to actor parameters only.
    # These fields are inert unless sam_enabled=True and are intentionally
    # fixed rather than adapted from returns, topology, or training seed.
    sam_enabled: bool = False
    sam_rho: float = 0.05
    sam_epsilon: float = 1e-12
    # Exact runtime continuation is opt-in.  Legacy checkpoints only contain
    # model/optimizer/update and must use the separately documented warm
    # restart path rather than this strict continuation mechanism.
    runtime_state_resume: str | None = None
    runtime_state_checkpointing: bool = False
    runtime_state_save_interval: int | None = None
    # DRTP-SEED-S1 opt-in independent RNG decomposition.  The historical
    # path remains unchanged when this flag is false.
    rng_decomposition: bool = False
    rng_seed_tuple: dict[str, int] | None = None


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


class EdgeDeletionResilientGraphAttentionLayer(nn.Module):
    """Deletion-local graph aggregation for the frozen EDR-SG-MAPPO method.

    This layer has exactly the same trainable tensors as ``GraphAttentionLayer``.
    Unlike neighbour-softmax aggregation, each legal incoming message has an
    independent sigmoid gate and a fixed ``1 / 4`` reduction.  Consequently,
    removing one incoming edge deletes only that edge's pre-aggregation
    contribution; it does not renormalize surviving messages.

    The graph convention remains ``adj[receiver, sender]``.  The identity edge
    follows the existing SG convention and is included in the legal mask.
    """

    FIXED_NORMALIZER = 4.0

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
        scores = self.attn(torch.cat([hi, hj], dim=-1)).squeeze(-1)
        if self.edge_score is not None and edge_feat is not None:
            scores = scores + self.edge_score(edge_feat).squeeze(-1)
        scores = self.leaky_relu(scores)

        eye = torch.eye(num_nodes, dtype=adj.dtype, device=adj.device).unsqueeze(0)
        mask = torch.clamp(adj + eye, 0.0, 1.0)
        gates = torch.sigmoid(scores) * mask
        contributions = gates.unsqueeze(-1) * h.unsqueeze(1)
        out = contributions.sum(dim=2) / self.FIXED_NORMALIZER
        return torch.tanh(out), gates


class TopologyConditionedGraphAttentionLayer(nn.Module):
    """Shared GAT layer with a zero-initialized local relation-state bias.

    The relation state is a multi-hot ``[P, C, T]`` vector concatenated with
    the frozen receiver-local edge features.  It enters only as an additive
    attention-score bias; the sender payload remains ``h_j``.  Zero
    initialization makes the initial forward pass structurally equivalent to
    the ordinary edge-feature GAT before the relation correction is learned.
    """

    def __init__(
        self,
        in_dim: int,
        out_dim: int,
        edge_dim: int = 0,
        relation_count: int = RSG_TC_RELATION_COUNT,
        relation_edge_indices: tuple[int, ...] = RSG_TC_EDGE_FEATURE_INDICES,
    ):
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
        self.relation_edge_indices = tuple(relation_edge_indices)
        if edge_dim > 0 and max(self.relation_edge_indices, default=-1) >= edge_dim:
            raise ValueError(
                f"RSG-TC edge feature index exceeds edge_dim={edge_dim}: {self.relation_edge_indices}"
            )
        context_dim = relation_count + len(self.relation_edge_indices)
        self.relation_bias = nn.Sequential(
            nn.Linear(context_dim, out_dim),
            nn.Tanh(),
            nn.Linear(out_dim, 1, bias=False),
        )
        # The last projection is exactly zero, so the initial bias is zero for
        # every relation/state vector without requiring a special input.
        nn.init.zeros_(self.relation_bias[-1].weight)
        self.leaky_relu = nn.LeakyReLU(0.2)

    def forward(
        self,
        x: torch.Tensor,
        adj: torch.Tensor,
        edge_feat: torch.Tensor,
        relation_adj: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        if relation_adj.ndim != 4 or relation_adj.shape[1] != RSG_TC_RELATION_COUNT:
            raise ValueError(
                "RSG-TC requires relation_adj with shape "
                f"[batch, {RSG_TC_RELATION_COUNT}, nodes, nodes], got {tuple(relation_adj.shape)}"
            )
        h = self.proj(x)
        bsz, num_nodes, hidden = h.shape
        hi = h.unsqueeze(2).expand(bsz, num_nodes, num_nodes, hidden)
        hj = h.unsqueeze(1).expand(bsz, num_nodes, num_nodes, hidden)
        scores = self.leaky_relu(self.attn(torch.cat([hi, hj], dim=-1))).squeeze(-1)
        if self.edge_score is not None and edge_feat is not None:
            scores = scores + self.edge_score(edge_feat).squeeze(-1)
        relation_multi_hot = relation_adj.permute(0, 2, 3, 1)
        local_edge_state = edge_feat[..., list(self.relation_edge_indices)]
        context = torch.cat([relation_multi_hot, local_edge_state], dim=-1)
        scores = scores + self.relation_bias(context).squeeze(-1)

        eye = torch.eye(num_nodes, dtype=adj.dtype, device=adj.device).unsqueeze(0)
        mask = torch.clamp(adj + eye, 0.0, 1.0)
        scores = scores.masked_fill(mask <= 0.0, -1e9)
        weights = torch.softmax(scores, dim=-1)
        out = torch.bmm(weights, h)
        return torch.tanh(out), weights


class RoleConditionedGraphAttentionLayer(nn.Module):
    """Graph attention with receiver-sender role-conditioned message gates."""

    def __init__(self, in_dim: int, out_dim: int, num_roles: int, edge_dim: int = 0, use_role_pair_gate: bool = True, shared_gate: nn.Embedding | None = None):
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
        self.role_pair_gate = None if not use_role_pair_gate else (shared_gate if shared_gate is not None else nn.Embedding(num_roles * num_roles, out_dim))
        if self.role_pair_gate is not None and shared_gate is None:
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
        gate = torch.sigmoid(self.role_pair_gate(pair_index)) if self.role_pair_gate is not None else torch.ones_like(hj)
        out = torch.sum(weights.unsqueeze(-1) * hj * gate, dim=2)
        return torch.tanh(out), weights

    def initialize_role_pair_prior(self, pairs: list[tuple[int, int]], strength: float) -> None:
        if not self.use_role_pair_gate or strength <= 0.0:
            return
        if not 0.0 < strength < 1.0:
            raise ValueError("role_gate_prior_strength must be a probability in (0, 1)")
        logit = math.log(strength / (1.0 - strength))
        with torch.no_grad():
            for receiver_role, sender_role in pairs:
                if receiver_role >= self.num_roles or sender_role >= self.num_roles:
                    continue
                pair_index = receiver_role * self.num_roles + sender_role
                assert self.role_pair_gate is not None
                self.role_pair_gate.weight[pair_index].fill_(float(logit))


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
        role_gate_mode: str = "relation_conditioned",
    ):
        super().__init__()
        if global_residual_weight < 0.0:
            raise ValueError("global_residual_weight must be non-negative")
        self.num_relations = num_relations
        self.global_residual_weight = float(global_residual_weight)
        if role_gate_mode not in {"none", "shared", "relation_conditioned"}:
            raise ValueError(f"Unsupported role_gate_mode: {role_gate_mode}")
        self.role_gate_mode = role_gate_mode
        shared_gate = None
        if role_gate_mode == "shared":
            shared_gate = nn.Embedding(num_roles * num_roles, hidden_dim)
            nn.init.zeros_(shared_gate.weight)
        self.layer1 = nn.ModuleList(
            [
                RoleConditionedGraphAttentionLayer(
                    hidden_dim, hidden_dim, num_roles, edge_dim,
                    use_role_pair_gate=use_role_pair_gate and role_gate_mode != "none",
                    shared_gate=shared_gate,
                )
                for _ in range(num_relations)
            ]
        )
        self.layer2 = nn.ModuleList(
            [
                RoleConditionedGraphAttentionLayer(
                    hidden_dim, hidden_dim, num_roles, edge_dim,
                    use_role_pair_gate=use_role_pair_gate and role_gate_mode != "none",
                    shared_gate=shared_gate,
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
        role_gate_mode: str = "relation_conditioned",
    ):
        super().__init__()
        if graph_encoder not in {"no_graph", "single", "edr", "rsg_tc", "multi_relation"}:
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
        elif graph_encoder == "edr":
            self.edr_gat1 = EdgeDeletionResilientGraphAttentionLayer(
                hidden_dim, hidden_dim, edge_dim=edge_feat_dim
            )
            self.edr_gat2 = EdgeDeletionResilientGraphAttentionLayer(
                hidden_dim, hidden_dim, edge_dim=edge_feat_dim
            )
        elif graph_encoder == "rsg_tc":
            self.rsg_tc_gat1 = TopologyConditionedGraphAttentionLayer(hidden_dim, hidden_dim, edge_dim=edge_feat_dim)
            self.rsg_tc_gat2 = TopologyConditionedGraphAttentionLayer(hidden_dim, hidden_dim, edge_dim=edge_feat_dim)
        else:
            self.multi_relation_graph = MultiRelationGraphEncoder(
                hidden_dim,
                edge_feat_dim,
                num_roles,
                use_role_pair_gate=graph_message_ablation != "no_role_pair_gate",
                role_gate_prior_strength=role_gate_prior_strength,
                global_residual_weight=multi_relation_global_residual_weight,
                role_gate_mode=role_gate_mode,
            )
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
        intent_label: torch.Tensor | None = None,
        detach_intent: bool = False,
        oracle_intent: bool = False,
        return_chain_aux: bool = False,
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
            chain_aux_logits = self.chain_aux_head(graph_feat.mean(dim=1))
            if return_chain_aux:
                return logits, attn, intent_logits, chain_aux_logits
            return logits, attn, intent_logits
        if self.graph_encoder == "single":
            x, _ = self.gat1(x, adj, edge_feat)
            x, attn = self.gat2(x, adj, edge_feat)
        elif self.graph_encoder == "edr":
            x, _ = self.edr_gat1(x, adj, edge_feat)
            x, attn = self.edr_gat2(x, adj, edge_feat)
        elif self.graph_encoder == "rsg_tc":
            if relation_adj is None:
                raise ValueError("relation_adj is required when graph_encoder='rsg_tc'")
            x, _ = self.rsg_tc_gat1(x, adj, edge_feat, relation_adj)
            x, attn = self.rsg_tc_gat2(x, adj, edge_feat, relation_adj)
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
        role_gate_mode: str = "relation_conditioned",
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
            role_gate_mode=role_gate_mode,
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
        action_generator: torch.Generator | None = None,
        intent_label: torch.Tensor | None = None,
        detach_intent: bool = False,
        oracle_intent: bool = False,
    ):
        logits, attn, intent_logits, chain_aux_logits = self.actor(
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
            return_chain_aux=True,
        )
        dist = Categorical(logits=logits)
        if action is None:
            if deterministic:
                action = torch.argmax(logits, dim=-1)
            elif action_generator is None:
                action = dist.sample()
            else:
                probs = dist.probs.reshape(-1, dist.probs.shape[-1])
                action = torch.multinomial(probs, num_samples=1, generator=action_generator).reshape(logits.shape[:-1])
        log_prob = dist.log_prob(action)
        entropy = dist.entropy()
        value = self.critic_value(share_obs, role)
        return action, log_prob, entropy, value, attn, intent_logits, chain_aux_logits


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def make_env(cfg: RIGMAPPOConfig, seed: int, training: bool = True, rng: random.Random | None = None):
    if cfg.env_name == "2d_pursuit":
        return UAVPursuitEnv(
            UAVPursuitConfig(
                seed=seed,
                target_policy=cfg.target_policy,
                target_speed=cfg.target_speed,
                communication_radius=sample_comm_radius(cfg, rng=rng) if training else cfg.communication_radius,
                communication_dropout_prob=cfg.communication_dropout_prob,
            )
        )
    if cfg.env_name == "3d_intercept":
        return UAVIntercept3DEnv(
            UAVIntercept3DConfig(
                seed=seed,
                target_policy=cfg.target_policy,
                communication_range_scale=sample_communication_range_scale(cfg, rng=rng) if training else cfg.communication_range_scale,
                communication_dropout_prob=sample_float_curriculum(
                    cfg.communication_dropout_prob,
                    cfg.communication_dropout_random_min,
                    cfg.communication_dropout_random_max,
                    rng=rng,
                )
                if training
                else cfg.communication_dropout_prob,
                message_delay_steps=sample_int_curriculum(
                    cfg.message_delay_steps,
                    cfg.message_delay_random_min,
                    cfg.message_delay_random_max,
                    rng=rng,
                )
                if training
                else cfg.message_delay_steps,
                radar_dropout_prob=sample_float_curriculum(
                    cfg.radar_dropout_prob,
                    cfg.radar_dropout_random_min,
                    cfg.radar_dropout_random_max,
                    rng=rng,
                )
                if training
                else cfg.radar_dropout_prob,
                strict_target_sensing=cfg.strict_target_sensing,
                agent_target_info_bottleneck=cfg.agent_target_info_bottleneck,
                relay_dependent_task=cfg.relay_dependent_task,
                business_grounded_geometry=cfg.business_grounded_geometry,
                target_prior_position=cfg.target_prior_position,
                max_target_message_age_steps=cfg.max_target_message_age_steps,
                min_target_confidence=cfg.min_target_confidence,
                safety_proximity_distance=cfg.safety_proximity_distance,
                safety_proximity_penalty_weight=cfg.safety_proximity_penalty_weight,
                attack_geometry_reward_weight=cfg.attack_geometry_reward_weight,
                attack_hold_steps=cfg.attack_hold_steps,
                min_success_step=cfg.min_success_step,
                post_loss_chain_reclosure_reward_weight=cfg.post_loss_chain_reclosure_reward_weight,
                post_loss_chain_reclosure_min_step=cfg.post_loss_chain_reclosure_min_step,
                failed_blue_agent=sample_failed_blue_agent(cfg, rng=rng) if training else cfg.failed_blue_agent,
                node_failure_start_step=sample_int_curriculum(
                    cfg.node_failure_start_step,
                    cfg.node_failure_start_random_min,
                    cfg.node_failure_start_random_max,
                    rng=rng,
                )
                if training
                else cfg.node_failure_start_step,
                node_failure_duration_steps=sample_int_curriculum(
                    cfg.node_failure_duration_steps,
                    cfg.node_failure_duration_random_min,
                    cfg.node_failure_duration_random_max,
                    rng=rng,
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
        )
    raise ValueError(f"Unsupported env_name: {cfg.env_name}")


def make_envs(cfg: RIGMAPPOConfig, rng_streams: RNGStreams | None = None) -> List[UAVPursuitEnv | UAVIntercept3DEnv]:
    return [
        make_env(
            cfg,
            cfg.seed + i if rng_streams is None else rng_streams.seed("env", i),
            training=True,
            rng=None if rng_streams is None else rng_streams.python_rng("env", i),
        )
        for i in range(cfg.num_envs)
    ]


def sample_comm_radius(cfg: RIGMAPPOConfig, rng: random.Random | None = None) -> float:
    if cfg.comm_radius_random_min is None or cfg.comm_radius_random_max is None:
        return cfg.communication_radius
    lo = min(cfg.comm_radius_random_min, cfg.comm_radius_random_max)
    hi = max(cfg.comm_radius_random_min, cfg.comm_radius_random_max)
    return (rng or random).uniform(lo, hi)


def sample_communication_range_scale(cfg: RIGMAPPOConfig, rng: random.Random | None = None) -> float:
    if cfg.communication_range_random_min is None or cfg.communication_range_random_max is None:
        return cfg.communication_range_scale
    lo = min(cfg.communication_range_random_min, cfg.communication_range_random_max)
    hi = max(cfg.communication_range_random_min, cfg.communication_range_random_max)
    return (rng or random).uniform(lo, hi)


def sample_float_curriculum(default: float, lo: float | None, hi: float | None, rng: random.Random | None = None) -> float:
    if lo is None or hi is None:
        return default
    return (rng or random).uniform(min(lo, hi), max(lo, hi))


def sample_int_curriculum(default: int, lo: int | None, hi: int | None, rng: random.Random | None = None) -> int:
    if lo is None or hi is None:
        return default
    return (rng or random).randint(min(lo, hi), max(lo, hi))


def sample_failed_blue_agent(cfg: RIGMAPPOConfig, rng: random.Random | None = None) -> int:
    source = rng or random
    if cfg.node_failure_random_prob <= 0.0 or source.random() >= cfg.node_failure_random_prob:
        return cfg.failed_blue_agent
    return source.randint(0, 2)


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


RUNTIME_STATE_FORMAT = "ri_gmappo_runtime_state_v1"


def _capture_runtime_rng_state() -> dict:
    """Capture process RNG state after a completed PPO update."""
    payload = {
        "python": random.getstate(),
        "numpy": np.random.get_state(),
        "torch_cpu": torch.get_rng_state(),
        "torch_cuda": None,
    }
    if torch.cuda.is_available():
        payload["torch_cuda"] = torch.cuda.get_rng_state_all()
    return payload


def _restore_runtime_rng_state(state: dict) -> None:
    """Restore the process RNG state after all constructors have run."""
    required = {"python", "numpy", "torch_cpu", "torch_cuda"}
    if not required.issubset(state):
        raise ValueError("incomplete runtime RNG state")
    random.setstate(state["python"])
    np.random.set_state(state["numpy"])
    # A CUDA map_location can move this persisted CPU RNG tensor onto the
    # active GPU.  The CPU generator accepts only a CPU ByteTensor; restoring
    # it explicitly on CPU keeps strict continuation device-independent.
    torch_cpu_state = state["torch_cpu"]
    if isinstance(torch_cpu_state, torch.Tensor) and torch_cpu_state.device.type != "cpu":
        torch_cpu_state = torch_cpu_state.cpu()
    torch.set_rng_state(torch_cpu_state)
    if state["torch_cuda"] is not None:
        if not torch.cuda.is_available():
            raise RuntimeError("runtime checkpoint requires CUDA RNG restoration on a CUDA-capable host")
        torch_cuda_states = [
            value.cpu() if isinstance(value, torch.Tensor) and value.device.type != "cpu" else value
            for value in state["torch_cuda"]
        ]
        torch.cuda.set_rng_state_all(torch_cuda_states)


def _selection_to_state(selection: DRTPSelection | None) -> dict | None:
    if selection is None:
        return None
    return {
        "group": selection.group,
        "condition": selection.condition,
        "failure_start_step": int(selection.failure_start_step),
        "failure_duration_steps": int(selection.failure_duration_steps),
        "failed_blue_agent": int(selection.failed_blue_agent),
    }


def _selection_from_state(state: dict | None) -> DRTPSelection | None:
    if state is None:
        return None
    return DRTPSelection(
        group=str(state["group"]),
        condition=str(state["condition"]),
        failure_start_step=int(state["failure_start_step"]),
        failure_duration_steps=int(state["failure_duration_steps"]),
        failed_blue_agent=int(state["failed_blue_agent"]),
    )


def save_runtime_training_checkpoint(
    path: Path,
    agent: nn.Module,
    optimizer: optim.Optimizer,
    update: int,
    best_eval_key: tuple[float, float, float, float],
    envs: list[UAVPursuitEnv | UAVIntercept3DEnv],
    obs: np.ndarray,
    share_obs: np.ndarray,
    graph_obs: dict,
    episode_counts: list[int],
    drtp_episode_returns: list[float],
    drtp_selections: list[DRTPSelection | None],
    drtp_sampler: DRTPTopologySampler | None,
    rng_streams: RNGStreams | None = None,
    action_generator: torch.Generator | None = None,
    minibatch_rng: np.random.Generator | None = None,
    env_rngs: list[random.Random] | None = None,
    failure_telemetry_state: dict | None = None,
) -> None:
    """Persist every state that can alter the following rollout/update.

    Runtime checkpointing deliberately does not add any state to the actor or
    critic input.  It exists only to make a future *strict continuation*
    auditable after the one documented 3M warm-restart boundary.
    """
    environment_states = []
    for env in envs:
        runtime_state = getattr(env, "runtime_state_dict", None)
        if runtime_state is None:
            raise TypeError(f"{type(env).__name__} does not support runtime-state persistence")
        environment_states.append(runtime_state())
    payload = {
        "format": RUNTIME_STATE_FORMAT,
        "model_state": agent.state_dict(),
        "optimizer_state": optimizer.state_dict(),
        "update": int(update),
        "best_eval_key": tuple(float(value) for value in best_eval_key),
        "rng_state": _capture_runtime_rng_state(),
        "environment_states": environment_states,
        "obs": copy.deepcopy(obs),
        "share_obs": copy.deepcopy(share_obs),
        "graph_obs": copy.deepcopy(graph_obs),
        "episode_counts": [int(value) for value in episode_counts],
        "drtp_episode_returns": [float(value) for value in drtp_episode_returns],
        "drtp_selections": [_selection_to_state(value) for value in drtp_selections],
        "drtp_sampler_state": None if drtp_sampler is None else drtp_sampler.state_dict(),
        # No observation/reward normalization is currently used, but its
        # explicit placeholder makes the continuation contract unambiguous.
        "normalization_state": None,
        "s1_rng_state": None if rng_streams is None else {
            "manifest": rng_streams.manifest(),
            "action_generator": None if action_generator is None else action_generator.get_state(),
            "minibatch_rng": None if minibatch_rng is None else copy.deepcopy(minibatch_rng.bit_generator.state),
            "env_rngs": None if env_rngs is None else [rng.getstate() for rng in env_rngs],
        },
        "failure_telemetry_state": copy.deepcopy(failure_telemetry_state),
    }
    torch.save(payload, path)


def load_runtime_training_checkpoint(path: str | Path, device: torch.device) -> dict:
    """Read and validate a strict-continuation checkpoint without mutating state."""
    payload = torch.load(path, map_location=device, weights_only=False)
    if not isinstance(payload, dict) or payload.get("format") != RUNTIME_STATE_FORMAT:
        raise ValueError("unsupported runtime training checkpoint format")
    required = {
        "model_state", "optimizer_state", "update", "best_eval_key", "rng_state",
        "environment_states", "obs", "share_obs", "graph_obs", "episode_counts",
        "drtp_episode_returns", "drtp_selections", "drtp_sampler_state", "normalization_state",
    }
    missing = sorted(required.difference(payload))
    if missing:
        raise ValueError(f"incomplete runtime training checkpoint: {missing}")
    return payload


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
                actions, _, _, _, _, intent_logits, _ = agent.get_action_and_value(
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


def _pp_drtp_probe_base_seed(probe_seed: int, update: int, base_index: int) -> int:
    """Derive a local-only probe seed without touching training RNG streams."""
    payload = f"pp-drtp-v1/{int(probe_seed)}/{int(update)}/{int(base_index)}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") % 2_000_000_000


def _pp_probe_initial_hash(obs: np.ndarray, share_obs: np.ndarray, graph: dict) -> str:
    """Hash reset state to audit nominal/failure paired-reset equivalence."""
    digest = hashlib.sha256()
    for value in (obs, share_obs, graph["node_feat"], graph["edge_feat"], graph["role"], graph["adj"]):
        digest.update(np.ascontiguousarray(value).tobytes())
    return digest.hexdigest()


def run_pp_drtp_probe_rollouts(
    agent: RIGMAPPOAgent,
    cfg: RIGMAPPOConfig,
    device: torch.device,
    *,
    update: int,
    probe_seed: int,
    probe_count: int,
) -> list[dict]:
    """Run isolated, deterministic, same-base-id probe episodes.

    The returned records are deliberately plain Python data.  They never enter
    a rollout buffer, optimizer transaction, training environment, or training
    RNG stream.  New environments are seeded before every reset.
    """
    if update % ADAPT_INTERVAL != 0 or update <= WARMUP_UPDATES:
        raise ValueError("PP-DRTP probe requested outside a post-warm-up adaptation boundary")
    if int(probe_count) <= 0:
        raise ValueError("PP-DRTP probe_count must be positive")
    was_training = agent.training
    records: list[dict] = []
    agent.eval()
    try:
        with torch.no_grad():
            for base_index in range(int(probe_count)):
                base_id = _pp_drtp_probe_base_seed(probe_seed, update, base_index)
                for group in ALL_GROUPS:
                    members = GROUP_MEMBERS[group]
                    condition, onset, duration = members[base_id % len(members)]
                    env = make_env(cfg, base_id, training=False)
                    env.seed(base_id)
                    env.config.failed_blue_agent = -1 if group == NOMINAL_GROUP else 1
                    env.config.node_failure_start_step = int(onset)
                    env.config.node_failure_duration_steps = int(duration)
                    obs, share_obs, graph = env.reset()
                    initial_hash = _pp_probe_initial_hash(obs, share_obs, graph)
                    episode_return = 0.0
                    while True:
                        stacked = stack_graphs([graph])
                        actions, _, _, _, _, _, _ = agent.get_action_and_value(
                            torch.as_tensor(obs[None, ...], dtype=torch.float32, device=device),
                            torch.as_tensor(stacked["node_feat"], dtype=torch.float32, device=device),
                            torch.as_tensor(stacked["edge_feat"], dtype=torch.float32, device=device),
                            torch.as_tensor(stacked["role"], dtype=torch.long, device=device),
                            torch.as_tensor(stacked["adj"], dtype=torch.float32, device=device),
                            torch.as_tensor(share_obs[None, ...], dtype=torch.float32, device=device),
                            relation_adj=torch.as_tensor(stacked["relation_adj"], dtype=torch.float32, device=device),
                            deterministic=True,
                            intent_label=torch.as_tensor(stacked["intent_label"], dtype=torch.long, device=device),
                            detach_intent=cfg.detach_intent,
                            oracle_intent=cfg.oracle_intent,
                        )
                        obs, share_obs, graph, reward, dones, info = env.step(actions.squeeze(0).cpu().numpy())
                        episode_return += float(np.sum(reward))
                        if np.all(dones):
                            break
                    records.append({
                        "update": int(update),
                        "base_id": int(base_id),
                        "group": group,
                        "condition": condition,
                        "failed_blue_agent": -1 if group == NOMINAL_GROUP else 1,
                        "failure_start_step": int(onset),
                        "failure_duration_steps": int(duration),
                        "initial_state_hash": initial_hash,
                        "episode_return": episode_return,
                        "steps": int(info.get("step", 0)),
                    })
    finally:
        agent.train(was_training)
    return records


def train_ri_gmappo(cfg: RIGMAPPOConfig) -> Path:
    if cfg.env_name == "3d_intercept" and cfg.oracle_intent:
        raise ValueError("oracle_intent is unavailable for 3d_intercept because it has no intent supervision")
    if cfg.runtime_state_resume and (cfg.resume or cfg.init_checkpoint):
        raise ValueError("runtime_state_resume is mutually exclusive with legacy resume/init_checkpoint")
    if cfg.runtime_state_resume and not cfg.append_log:
        raise ValueError("runtime_state_resume requires append_log=True to preserve one trajectory log")
    rng_streams = None
    if cfg.rng_decomposition:
        if cfg.rng_seed_tuple is None:
            rng_streams = RNGStreams.from_master(cfg.seed)
        else:
            from algorithms.ri_gmappo.rng_streams import RNGSeedTuple
            rng_streams = RNGStreams(RNGSeedTuple(**{key: int(value) for key, value in cfg.rng_seed_tuple.items()}))
        set_seed(rng_streams.seeds.init_seed)
    else:
        set_seed(cfg.seed)
    device = torch.device(cfg.device)
    out_dir = Path(cfg.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    runtime_payload = (
        load_runtime_training_checkpoint(cfg.runtime_state_resume, device)
        if cfg.runtime_state_resume is not None
        else None
    )
    if runtime_payload is not None and int(runtime_payload["update"]) != int(cfg.update_offset):
        raise ValueError("runtime_state_resume update must equal the configured update_offset")

    curriculum = TopologyCurriculum(
        cfg.topology_curriculum_schedule,
        cfg.topology_curriculum_seed if cfg.topology_curriculum_seed is not None else cfg.seed,
        cfg.updates,
    )
    drtp_mode = str(cfg.drtp_sampler_mode).lower()
    if drtp_mode not in {"none", "utr", "snr", "drtp", "pp_drtp", "r_drtp", "egtr", "drtp_tr", "conservative_drtp"}:
        raise ValueError("unsupported drtp_sampler_mode")
    actor_gradient_mode = str(cfg.actor_gradient_mode).lower()
    if actor_gradient_mode not in {"standard", "utr", "spc", "tcr"}:
        raise ValueError("actor_gradient_mode must be standard, utr, spc, or tcr")
    if cfg.sam_enabled:
        if actor_gradient_mode != "utr" or not cfg.fixed_stratified_topology_sampler:
            raise ValueError("TC-SAM requires the frozen UTR actor mode and fixed stratified sampler")
        if not math.isfinite(float(cfg.sam_rho)) or float(cfg.sam_rho) < 0.0:
            raise ValueError("sam_rho must be a finite non-negative scalar")
        if not math.isfinite(float(cfg.sam_epsilon)) or float(cfg.sam_epsilon) <= 0.0:
            raise ValueError("sam_epsilon must be a finite positive scalar")
    policy_guard_mode = str(cfg.policy_update_guard_mode).lower()
    if policy_guard_mode not in {"none", "post_step_actor_rollback", "post_step_actor_backtrack"}:
        raise ValueError("unsupported policy_update_guard_mode")
    if policy_guard_mode != "none":
        if actor_gradient_mode != "standard" or cfg.sam_enabled:
            raise ValueError("post-step actor guards are defined only for standard non-SAM PPO")
        if cfg.target_kl is None or not math.isfinite(float(cfg.target_kl)) or float(cfg.target_kl) <= 0.0:
            raise ValueError("post-step actor guards require a finite positive target_kl")
        if cfg.rollout_steps * cfg.num_envs != cfg.minibatch_graphs:
            raise ValueError("post-step actor guards require one complete rollout minibatch per PPO epoch")
    if sum((curriculum.enabled, cfg.fixed_f0_probability is not None, drtp_mode != "none", cfg.fixed_stratified_topology_sampler)) > 1:
        raise ValueError("curriculum, fixed mixture, DRTP sampler, and fixed stratified sampler are mutually exclusive")
    if actor_gradient_mode != "standard":
        if not cfg.fixed_stratified_topology_sampler:
            raise ValueError("UTR/SPC/TCR actor modes require the fixed stratified topology sampler")
        if cfg.num_envs != 4 or cfg.rollout_steps * cfg.num_envs != cfg.minibatch_graphs:
            raise ValueError("UTR/SPC/TCR require the frozen 4x64 rollout and one 256-graph projection minibatch")
    mixture = (
        FixedConditionMixture(
            cfg.fixed_f0_probability,
            cfg.fixed_condition_mixture_seed if cfg.fixed_condition_mixture_seed is not None else cfg.seed,
        )
        if cfg.fixed_f0_probability is not None
        else None
    )
    sampler_seed = cfg.drtp_sampler_seed if cfg.drtp_sampler_seed is not None else cfg.seed
    sampler_updates = cfg.drtp_sampler_total_updates if cfg.drtp_sampler_total_updates is not None else cfg.updates
    if drtp_mode == "egtr":
        drtp_sampler = EGTRTopologySampler(
            sampler_seed,
            sampler_updates,
        )
    elif drtp_mode == "pp_drtp":
        drtp_sampler = PairedProbeTopologySampler(
            sampler_seed,
            sampler_updates,
            probe_count=cfg.pp_drtp_probe_count,
        )
    elif drtp_mode == "snr":
        drtp_sampler = StaticNonuniformTopologySampler(sampler_seed, sampler_updates)
    elif drtp_mode != "none":
        drtp_sampler = DRTPTopologySampler(
            drtp_mode,
            sampler_seed,
            sampler_updates,
        )
    else:
        drtp_sampler = None
    if cfg.fixed_stratified_topology_sampler:
        drtp_sampler = FixedStratifiedTopologySampler(
            cfg.fixed_stratified_topology_sampler_seed
            if cfg.fixed_stratified_topology_sampler_seed is not None
            else cfg.seed,
            cfg.num_envs,
        )
    curriculum_rows: list[dict] = []
    drtp_rows: list[dict] = []
    pp_probe_rows: list[dict] = []
    episode_counts = [0 for _ in range(cfg.num_envs)]
    drtp_episode_returns = [0.0 for _ in range(cfg.num_envs)]
    drtp_selections: list[DRTPSelection | None] = [None for _ in range(cfg.num_envs)]
    if curriculum.enabled:
        (out_dir / "topology_curriculum_manifest.json").write_text(
            json.dumps({**curriculum.manifest(), "training_seed": cfg.seed,
                        "graph_encoder": cfg.graph_encoder, "hidden_dim": cfg.hidden_dim},
                       indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if mixture is not None:
        (out_dir / "fixed_condition_mixture_manifest.json").write_text(
            json.dumps({**mixture.manifest(), "training_seed": cfg.seed,
                        "graph_encoder": cfg.graph_encoder, "hidden_dim": cfg.hidden_dim},
                       indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if drtp_sampler is not None:
        sampler_name = (
            "fixed_stratified_topology_sampler_manifest.json"
            if cfg.fixed_stratified_topology_sampler
            else "snr_static_nonuniform_topology_sampler_manifest.json"
            if drtp_mode == "snr"
            else "drtp_topology_sampler_manifest.json"
        )
        (out_dir / sampler_name).write_text(
            json.dumps({**drtp_sampler.manifest(), "training_seed": cfg.seed,
                        "graph_encoder": cfg.graph_encoder, "hidden_dim": cfg.hidden_dim,
                        "parameter_count": 116728}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    envs = make_envs(cfg, rng_streams=rng_streams)
    telemetry_writer = None
    if cfg.failure_aware_telemetry:
        telemetry_method = "utr" if drtp_mode == "utr" else "drtp" if drtp_mode == "drtp" else drtp_mode
        telemetry_writer = FailureAwareTelemetryWriter(
            out_dir / "failure_telemetry",
            training_seed=cfg.seed,
            method=telemetry_method,
            pre_steps=cfg.failure_telemetry_pre_steps,
            post_steps=cfg.failure_telemetry_post_steps,
            pseudo_onset=cfg.failure_telemetry_pseudo_onset,
        )
    env_rngs = (
        [rng_streams.python_rng("env", env_index, 1) for env_index in range(cfg.num_envs)]
        if rng_streams is not None else None
    )
    action_generator = rng_streams.torch_generator("action", device) if rng_streams is not None else None
    minibatch_rng = rng_streams.numpy_rng("minibatch") if rng_streams is not None else None
    if rng_streams is not None:
        (out_dir / "rng_stream_manifest.json").write_text(
            json.dumps(rng_streams.manifest(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    obs_list, share_list, graph_list = [], [], []
    for env_index, env in enumerate(envs):
        if runtime_payload is None:
            if curriculum.enabled:
                selection = curriculum.select(update=0, env_index=env_index, episode_index=0)
                curriculum.apply(env, selection)
                curriculum_rows.append(curriculum.row(0, env_index, 0, selection))
            elif mixture is not None:
                selection = mixture.select(env_index=env_index, episode_index=0)
                mixture.apply(env, selection)
                curriculum_rows.append(mixture.row(0, env_index, 0, selection))
            elif drtp_sampler is not None:
                selection = drtp_sampler.select(update=0, env_index=env_index, episode_index=0)
                drtp_sampler.apply(env, selection)
                drtp_selections[env_index] = selection
                drtp_rows.append(drtp_sampler.selection_row(0, env_index, 0, selection))
        # A temporary reset provides graph dimensions for agent construction.
        # Its state/RNG effects are overwritten below for strict continuation.
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
        role_gate_mode=cfg.role_gate_mode,
        num_roles=max(4, int(np.max(sample_graph["role"])) + 1),
    ).to(device)
    optimizer = make_optimizer(agent, cfg)
    if runtime_payload is not None:
        agent.load_state_dict(runtime_payload["model_state"], strict=True)
        optimizer.load_state_dict(runtime_payload["optimizer_state"])
        if len(runtime_payload["environment_states"]) != len(envs):
            raise ValueError("runtime checkpoint environment count does not match configuration")
        for env, environment_state in zip(envs, runtime_payload["environment_states"]):
            loader = getattr(env, "load_runtime_state_dict", None)
            if loader is None:
                raise TypeError(f"{type(env).__name__} does not support runtime-state restoration")
            loader(environment_state)
        obs = copy.deepcopy(runtime_payload["obs"])
        share_obs = copy.deepcopy(runtime_payload["share_obs"])
        graph_obs = copy.deepcopy(runtime_payload["graph_obs"])
        episode_counts = [int(value) for value in runtime_payload["episode_counts"]]
        drtp_episode_returns = [float(value) for value in runtime_payload["drtp_episode_returns"]]
        drtp_selections = [_selection_from_state(value) for value in runtime_payload["drtp_selections"]]
        if drtp_sampler is None and runtime_payload["drtp_sampler_state"] is not None:
            raise ValueError("runtime checkpoint requires a DRTP/UTR sampler")
        if drtp_sampler is not None:
            if runtime_payload["drtp_sampler_state"] is None:
                raise ValueError("runtime checkpoint is missing DRTP/UTR sampler state")
            drtp_sampler.load_state_dict(runtime_payload["drtp_sampler_state"])
        if telemetry_writer is not None and runtime_payload.get("failure_telemetry_state") is not None:
            telemetry_writer.load_state_dict(runtime_payload["failure_telemetry_state"])
        _restore_runtime_rng_state(runtime_payload["rng_state"])
    elif cfg.init_checkpoint:
        load_matching_state_dict(agent, cfg.init_checkpoint, device)
    if cfg.resume:
        load_training_checkpoint(agent, optimizer, cfg.resume, device)
    agent._role_gate_initial_state = {
        name: parameter.detach().clone()
        for name, parameter in agent.named_parameters()
        if "role_pair_gate" in name
    }

    log_path = out_dir / "train_log.csv"
    telemetry_path = out_dir / "role_gate_telemetry.csv"
    curriculum_log_path = out_dir / "topology_curriculum_log.csv"
    mixture_log_path = out_dir / "fixed_condition_mixture_log.csv"
    drtp_log_path = out_dir / (
        "fixed_stratified_topology_sampler_log.csv"
        if cfg.fixed_stratified_topology_sampler
        else "snr_static_nonuniform_topology_sampler_log.csv"
        if drtp_mode == "snr"
        else "drtp_topology_sampler_log.csv"
    )
    pp_probe_log_path = out_dir / "pp_drtp_probe_log.csv"
    actor_gradient_log_path = out_dir / "actor_gradient_telemetry.csv"
    group_credit_log_path = out_dir / "group_credit_telemetry.csv"
    group_credit_conflict_log_path = out_dir / "group_credit_gradient_conflicts.csv"
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
        "role_gate_grad_norm",
        "role_gate_mean",
        "role_gate_std",
        "role_gate_min",
        "role_gate_max",
        "role_gate_displacement_l2",
        "actor_nominal_sample_count",
        "actor_failure_sample_count",
        "actor_gradient_dot",
        "actor_gradient_cosine",
        "actor_post_projection_cosine",
        "actor_projection_applied_fraction",
        "actor_g_nominal_norm",
        "actor_g_failure_norm",
        "actor_projected_gradient_norm",
        "actor_projection_magnitude",
        "actor_final_gradient_norm",
        "sam_enabled",
        "sam_first_gradient_norm",
        "sam_perturbation_norm",
        "sam_second_gradient_norm",
        # S1 optimization telemetry contract.  Values that the frozen PPO
        # path does not expose are written explicitly as NOT_AVAILABLE.
        "actor_gradient_norm",
        "critic_gradient_norm",
        "actor_update_norm",
        "critic_update_norm",
        "advantage_mean",
        "advantage_std",
        "value_target_mean",
        "value_target_std",
        "learning_rate",
        "policy_kl_post_step",
        "policy_kl_attempted_max",
        "policy_kl_threshold",
        "policy_guard_triggered",
        "policy_guard_reason",
        "policy_guard_epoch",
        "policy_steps_attempted",
        "policy_steps_accepted",
        "actor_attempted_update_l2",
        "actor_accepted_update_l2",
        "actor_rollback_l2",
        "actor_projection_l2",
        "policy_backtrack_alpha",
        "policy_backtrack_iterations",
        "actor_optimizer_state_restored",
        "actor_optimizer_state_retained_after_projection",
        "critic_step_retained_after_actor_rollback",
        "critic_step_retained_after_policy_guard",
        "policy_guard_cumulative_triggers",
        "policy_guard_cumulative_attempts",
        "policy_guard_cumulative_intervention_rate",
    ]
    write_header = not (cfg.append_log and log_path.exists())
    mode = "a" if cfg.append_log else "w"
    policy_guard_cumulative_triggers = 0
    policy_guard_cumulative_attempts = 0
    if cfg.append_log and log_path.exists():
        with log_path.open("r", newline="", encoding="utf-8") as prior_log:
            for prior_row in csv.DictReader(prior_log):
                try:
                    policy_guard_cumulative_triggers += int(float(prior_row.get("policy_guard_triggered", 0) or 0))
                    policy_guard_cumulative_attempts += int(float(prior_row.get("policy_steps_attempted", 0) or 0))
                except (TypeError, ValueError):
                    raise ValueError("invalid Stable-v2 cumulative telemetry in existing train_log.csv")
    curriculum_log_context = (
        curriculum_log_path.open("a" if cfg.append_log else "w", newline="", encoding="utf-8")
        if curriculum.enabled and cfg.topology_curriculum_logging
        else nullcontext()
    )
    mixture_log_context = (
        mixture_log_path.open("a" if cfg.append_log else "w", newline="", encoding="utf-8")
        if mixture is not None and cfg.fixed_condition_mixture_logging
        else nullcontext()
    )
    drtp_log_context = (
        drtp_log_path.open("a" if cfg.append_log else "w", newline="", encoding="utf-8")
        if drtp_sampler is not None and cfg.drtp_sampler_logging
        else nullcontext()
    )
    pp_probe_log_context = (
        pp_probe_log_path.open("a" if cfg.append_log else "w", newline="", encoding="utf-8")
        if isinstance(drtp_sampler, PairedProbeTopologySampler)
        else nullcontext()
    )
    actor_gradient_log_context = (
        actor_gradient_log_path.open("a" if cfg.append_log else "w", newline="", encoding="utf-8")
        if cfg.actor_gradient_logging
        else nullcontext()
    )
    group_credit_log_context = (
        group_credit_log_path.open("a" if cfg.append_log else "w", newline="", encoding="utf-8")
        if cfg.group_credit_telemetry
        else nullcontext()
    )
    group_credit_conflict_log_context = (
        group_credit_conflict_log_path.open("a" if cfg.append_log else "w", newline="", encoding="utf-8")
        if cfg.group_credit_telemetry
        else nullcontext()
    )
    with log_path.open(mode, newline="", encoding="utf-8") as f, (
        telemetry_path.open(mode, newline="", encoding="utf-8") if cfg.role_gate_telemetry else nullcontext()
    ) as telemetry_file, curriculum_log_context as curriculum_file, mixture_log_context as mixture_file, drtp_log_context as drtp_file, pp_probe_log_context as pp_probe_file, actor_gradient_log_context as actor_gradient_file, group_credit_log_context as group_credit_file, group_credit_conflict_log_context as group_credit_conflict_file:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        role_gate_writer = None
        if cfg.role_gate_telemetry:
            telemetry_fields = ["update", "relation", "receiver_role", "sender_role", "edge_count", "attention_mean", "gate_mean", "effective_payload_mean"]
            role_gate_writer = csv.DictWriter(telemetry_file, fieldnames=telemetry_fields)
            if not cfg.append_log or not telemetry_path.exists() or telemetry_path.stat().st_size == 0:
                role_gate_writer.writeheader()
        curriculum_writer = None
        curriculum_logged_count = 0
        if curriculum_file is not None:
            curriculum_fields = list(curriculum_rows[0]) if curriculum_rows else [
                "update", "progress", "env_index", "episode_index", "condition",
                "failed_blue_agent", "failure_start_step", "failure_duration_steps",
                "nominal_probability", "f0_probability", "ftrain_probability",
                "schedule", "schedule_hash",
            ]
            curriculum_writer = csv.DictWriter(curriculum_file, fieldnames=curriculum_fields)
            curriculum_writer.writeheader()
            for curriculum_row in curriculum_rows:
                curriculum_writer.writerow(curriculum_row)
            curriculum_file.flush()
            curriculum_logged_count = len(curriculum_rows)
        mixture_writer = None
        mixture_logged_count = 0
        if mixture_file is not None:
            mixture_fields = [
                "update", "env_index", "episode_index", "condition", "failed_blue_agent",
                "failure_start_step", "failure_duration_steps", "nominal_probability", "f0_probability",
            ]
            mixture_writer = csv.DictWriter(mixture_file, fieldnames=mixture_fields)
            mixture_writer.writeheader()
            for mixture_row in curriculum_rows:
                mixture_writer.writerow(mixture_row)
            mixture_file.flush()
            mixture_logged_count = len(curriculum_rows)
        drtp_writer = None
        drtp_logged_count = 0
        if drtp_file is not None:
            drtp_writer = csv.DictWriter(drtp_file, fieldnames=drtp_sampler.log_fields())
            if not cfg.append_log or not drtp_log_path.exists() or drtp_log_path.stat().st_size == 0:
                drtp_writer.writeheader()
            for drtp_row in drtp_rows:
                drtp_writer.writerow(drtp_row)
            drtp_file.flush()
            drtp_logged_count = len(drtp_rows)
        pp_probe_writer = None
        pp_probe_logged_count = 0
        if pp_probe_file is not None:
            pp_probe_fields = [
                "update", "base_id", "group", "condition", "failed_blue_agent",
                "failure_start_step", "failure_duration_steps", "initial_state_hash", "episode_return", "steps",
            ]
            pp_probe_writer = csv.DictWriter(pp_probe_file, fieldnames=pp_probe_fields)
            if not cfg.append_log or not pp_probe_log_path.exists() or pp_probe_log_path.stat().st_size == 0:
                pp_probe_writer.writeheader()
        group_credit_writer = None
        group_credit_conflict_writer = None
        if group_credit_file is not None:
            group_credit_writer = csv.DictWriter(group_credit_file, fieldnames=GROUP_CREDIT_FIELDS)
            group_credit_conflict_writer = csv.DictWriter(
                group_credit_conflict_file, fieldnames=GROUP_CREDIT_CONFLICT_FIELDS
            )
            if not cfg.append_log or group_credit_log_path.stat().st_size == 0:
                group_credit_writer.writeheader()
            if not cfg.append_log or group_credit_conflict_log_path.stat().st_size == 0:
                group_credit_conflict_writer.writeheader()
        f.flush()
        best_eval_key = (
            tuple(float(value) for value in runtime_payload["best_eval_key"])
            if runtime_payload is not None
            else (-1.0, float("-inf"), float("-inf"), float("-inf"))
        )
        for local_update in range(1, cfg.updates + 1):
            update = cfg.update_offset + local_update
            batch = collect_rollout(
                agent, envs, obs, share_obs, graph_obs, cfg, device,
                curriculum=curriculum if curriculum.enabled else None,
                episode_counts=episode_counts, current_update=update,
                curriculum_rows=curriculum_rows,
                fixed_mixture=mixture,
                drtp_sampler=drtp_sampler,
                drtp_episode_returns=drtp_episode_returns,
                drtp_selections=drtp_selections,
                drtp_rows=drtp_rows,
                action_generator=action_generator,
                env_rngs=env_rngs,
                telemetry_writer=telemetry_writer,
            )
            obs, share_obs, graph_obs = batch["next_obs"], batch["next_share_obs"], batch["next_graph_obs"]
            if isinstance(drtp_sampler, PairedProbeTopologySampler) and update % ADAPT_INTERVAL == 0 and update > WARMUP_UPDATES:
                records = run_pp_drtp_probe_rollouts(
                    agent,
                    cfg,
                    device,
                    update=update,
                    probe_seed=(cfg.pp_drtp_probe_seed if cfg.pp_drtp_probe_seed is not None else cfg.seed),
                    probe_count=cfg.pp_drtp_probe_count,
                )
                drtp_sampler.record_probe_batch(update, records)
                pp_probe_rows.extend(records)
            if drtp_sampler is not None:
                drtp_update_row = drtp_sampler.maybe_update(update)
                if drtp_update_row is not None:
                    drtp_rows.append(drtp_update_row)
            credit_group_rows: list[dict] = []
            credit_conflict_rows: list[dict] = []
            if cfg.group_credit_telemetry:
                if cfg.group_credit_telemetry_interval <= 0:
                    raise ValueError("group_credit_telemetry_interval must be positive")
                if update % cfg.group_credit_telemetry_interval == 0:
                    credit_group_rows, credit_conflict_rows = summarize_group_credit_assignment(
                        agent, batch, cfg, device, update=update
                    )
            train_info = update_policy(agent, optimizer, batch, cfg, device, update, minibatch_rng=minibatch_rng)
            policy_guard_cumulative_triggers += int(train_info["policy_guard_triggered"])
            policy_guard_cumulative_attempts += int(train_info["policy_steps_attempted"])
            row = {"update": update, **train_info, "train_avg_reward": float(batch["rewards"].mean())}
            row.update({
                "actor_gradient_norm": "NOT_AVAILABLE",
                "critic_gradient_norm": "NOT_AVAILABLE",
                "actor_update_norm": "NOT_AVAILABLE",
                "critic_update_norm": "NOT_AVAILABLE",
                "advantage_mean": float(np.asarray(batch["advantages"]).mean()),
                "advantage_std": float(np.asarray(batch["advantages"]).std()),
                "value_target_mean": float(np.asarray(batch["returns"]).mean()),
                "value_target_std": float(np.asarray(batch["returns"]).std()),
                "learning_rate": float(optimizer.param_groups[0]["lr"]),
                "policy_guard_cumulative_triggers": policy_guard_cumulative_triggers,
                "policy_guard_cumulative_attempts": policy_guard_cumulative_attempts,
                "policy_guard_cumulative_intervention_rate": (
                    float(policy_guard_cumulative_triggers / policy_guard_cumulative_attempts)
                    if policy_guard_cumulative_attempts
                    else 0.0
                ),
            })
            if role_gate_writer is not None:
                for telemetry_row in summarize_role_gate_telemetry(agent, batch, device):
                    role_gate_writer.writerow({"update": update, **telemetry_row})
                telemetry_file.flush()
            if actor_gradient_file is not None:
                gradient_fields = [
                    "update", "mode", "nominal_sample_count", "failure_sample_count",
                    "gradient_dot", "gradient_cosine", "projection_applied",
                    "g_nominal_norm", "g_failure_norm", "post_projection_cosine",
                    "projected_gradient_norm", "projection_magnitude", "final_gradient_norm",
                    "sam_enabled", "sam_first_gradient_norm", "sam_perturbation_norm", "sam_second_gradient_norm",
                    "sam_first_minibatch_hash", "sam_second_minibatch_hash",
                ]
                gradient_writer = csv.DictWriter(actor_gradient_file, fieldnames=gradient_fields)
                if not cfg.append_log or actor_gradient_log_path.stat().st_size == 0:
                    gradient_writer.writeheader()
                for gradient_row in train_info.pop("actor_gradient_rows", []):
                    gradient_writer.writerow({"update": update, "mode": actor_gradient_mode, **gradient_row})
                actor_gradient_file.flush()
            row.pop("actor_gradient_rows", None)
            if group_credit_writer is not None:
                group_credit_writer.writerows(credit_group_rows)
                group_credit_conflict_writer.writerows(credit_conflict_rows)
                group_credit_file.flush()
                group_credit_conflict_file.flush()
            if curriculum_writer is not None:
                for curriculum_row in curriculum_rows[curriculum_logged_count:]:
                    curriculum_writer.writerow(curriculum_row)
                curriculum_file.flush()
                curriculum_logged_count = len(curriculum_rows)
            if mixture_writer is not None:
                for mixture_row in curriculum_rows[mixture_logged_count:]:
                    mixture_writer.writerow(mixture_row)
                mixture_file.flush()
                mixture_logged_count = len(curriculum_rows)
            if drtp_writer is not None:
                for drtp_row in drtp_rows[drtp_logged_count:]:
                    drtp_writer.writerow(drtp_row)
                drtp_file.flush()
                drtp_logged_count = len(drtp_rows)
            if pp_probe_writer is not None:
                for probe_row in pp_probe_rows[pp_probe_logged_count:]:
                    pp_probe_writer.writerow(probe_row)
                pp_probe_file.flush()
                pp_probe_logged_count = len(pp_probe_rows)
            if cfg.evaluation_enabled and (update % cfg.eval_interval == 0 or update == 1):
                eval_base_seed = cfg.eval_base_seed if cfg.eval_base_seed is not None else 10_000 + update * 100
                row.update(eval_policy(agent, cfg, base_seed=eval_base_seed))
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
                if cfg.runtime_state_checkpointing:
                    runtime_interval = cfg.runtime_state_save_interval or cfg.save_interval
                    if update % runtime_interval == 0 or local_update == cfg.updates:
                        save_runtime_training_checkpoint(
                            out_dir / "actor_critic_runtime_state_latest.pt",
                         agent, optimizer, update, best_eval_key, envs, obs, share_obs, graph_obs,
                         episode_counts, drtp_episode_returns, drtp_selections, drtp_sampler,
                         rng_streams=rng_streams, action_generator=action_generator,
                         minibatch_rng=minibatch_rng, env_rngs=env_rngs,
                         failure_telemetry_state=None if telemetry_writer is None else telemetry_writer.state_dict(),
                        )
            milestone_label = (cfg.milestone_updates or {}).get(update)
            if milestone_label is not None:
                torch.save(agent.state_dict(), out_dir / f"actor_critic_milestone_{milestone_label}.pt")
                save_training_checkpoint(
                    out_dir / f"actor_critic_milestone_{milestone_label}_training_state.pt",
                    agent,
                    optimizer,
                    update,
                    best_eval_key,
                )
                if cfg.runtime_state_checkpointing:
                    save_runtime_training_checkpoint(
                        out_dir / f"actor_critic_runtime_state_milestone_{milestone_label}.pt",
                         agent, optimizer, update, best_eval_key, envs, obs, share_obs, graph_obs,
                         episode_counts, drtp_episode_returns, drtp_selections, drtp_sampler,
                         rng_streams=rng_streams, action_generator=action_generator,
                         minibatch_rng=minibatch_rng, env_rngs=env_rngs,
                         failure_telemetry_state=None if telemetry_writer is None else telemetry_writer.state_dict(),
                    )
    if telemetry_writer is not None:
        telemetry_writer.close()
    return log_path


def collect_rollout(
    agent: RIGMAPPOAgent,
    envs: List[UAVPursuitEnv | UAVIntercept3DEnv],
    obs: np.ndarray,
    share_obs: np.ndarray,
    graph_obs: dict,
    cfg: RIGMAPPOConfig,
    device: torch.device,
    curriculum: TopologyCurriculum | None = None,
    episode_counts: list[int] | None = None,
    current_update: int = 0,
    curriculum_rows: list[dict] | None = None,
    fixed_mixture: FixedConditionMixture | None = None,
    drtp_sampler: DRTPTopologySampler | None = None,
    drtp_episode_returns: list[float] | None = None,
    drtp_selections: list[DRTPSelection | None] | None = None,
    drtp_rows: list[dict] | None = None,
    action_generator: torch.Generator | None = None,
    env_rngs: list[random.Random] | None = None,
    telemetry_writer: FailureAwareTelemetryWriter | None = None,
) -> dict:
    obs_buf, share_buf, node_buf, edge_buf, role_buf, adj_buf, intent_buf = [], [], [], [], [], [], []
    relation_adj_buf = []
    action_buf, logp_buf, reward_buf, done_buf, value_buf = [], [], [], [], []
    condition_nominal_buf, condition_group_buf = [], []

    for _ in range(cfg.rollout_steps):
        if drtp_sampler is None:
            condition_nominal = np.ones(len(envs), dtype=bool)
            condition_group = np.full(len(envs), NOMINAL_GROUP, dtype="<U3")
        else:
            if drtp_selections is None or any(selection is None for selection in drtp_selections):
                raise AssertionError("topology condition selection missing for rollout sample")
            condition_nominal = np.asarray(
                [selection.group == "N" for selection in drtp_selections], dtype=bool
            )
            condition_group = np.asarray(
                [selection.group for selection in drtp_selections], dtype="<U3"
            )
        with torch.no_grad():
            actions, logp, entropy, values, _, _, _ = agent.get_action_and_value(
                torch.as_tensor(obs, dtype=torch.float32, device=device),
                torch.as_tensor(graph_obs["node_feat"], dtype=torch.float32, device=device),
                torch.as_tensor(graph_obs["edge_feat"], dtype=torch.float32, device=device),
                torch.as_tensor(graph_obs["role"], dtype=torch.long, device=device),
                torch.as_tensor(graph_obs["adj"], dtype=torch.float32, device=device),
                torch.as_tensor(share_obs, dtype=torch.float32, device=device),
                relation_adj=torch.as_tensor(graph_obs["relation_adj"], dtype=torch.float32, device=device),
                action_generator=action_generator,
                intent_label=torch.as_tensor(graph_obs["intent_label"], dtype=torch.long, device=device),
                detach_intent=cfg.detach_intent,
                oracle_intent=cfg.oracle_intent,
            )

        actions_np = actions.cpu().numpy()
        entropy_np = entropy.mean(dim=1).cpu().numpy()
        values_np = values.cpu().numpy()
        logp_np = logp.cpu().numpy()
        next_obs, next_share, next_graphs, rewards, dones = [], [], [], [], []
        for e, env in enumerate(envs):
            pre_step = int(getattr(env, "step_count", 0))
            graph_before = {key: value[e] for key, value in graph_obs.items()}
            o, s, g, r, d, info = env.step(actions_np[e])
            if telemetry_writer is not None:
                telemetry_writer.record_step(
                    update=current_update,
                    env_index=e,
                    episode_index=0 if episode_counts is None else episode_counts[e],
                    env_step=int(info.get("step", pre_step + 1)),
                    pre_step=pre_step,
                    env=env,
                    graph_before=graph_before,
                    action=actions_np[e],
                    reward=r[:, 0],
                    policy_entropy=float(entropy_np[e]),
                    info=info,
                    selection=None if drtp_selections is None else drtp_selections[e],
                )
            if drtp_sampler is not None and getattr(drtp_sampler, "uses_completed_return_feedback", False):
                if drtp_episode_returns is None:
                    raise ValueError("DRTP episode-return bookkeeping is required")
                drtp_episode_returns[e] += float(np.sum(r))
            if np.all(d):
                if curriculum is not None:
                    if episode_counts is None or curriculum_rows is None:
                        raise ValueError("curriculum reset bookkeeping is required")
                    episode_counts[e] += 1
                    selection = curriculum.select(
                        update=current_update, env_index=e, episode_index=episode_counts[e]
                    )
                    curriculum.apply(env, selection)
                    curriculum_rows.append(
                        curriculum.row(current_update, e, episode_counts[e], selection)
                    )
                elif fixed_mixture is not None:
                    if episode_counts is None or curriculum_rows is None:
                        raise ValueError("fixed-mixture reset bookkeeping is required")
                    episode_counts[e] += 1
                    selection = fixed_mixture.select(env_index=e, episode_index=episode_counts[e])
                    fixed_mixture.apply(env, selection)
                    curriculum_rows.append(
                        fixed_mixture.row(current_update, e, episode_counts[e], selection)
                    )
                elif drtp_sampler is not None:
                    if (episode_counts is None or drtp_episode_returns is None
                            or drtp_selections is None or drtp_rows is None):
                        raise ValueError("DRTP reset bookkeeping is required")
                    previous_selection = drtp_selections[e]
                    if previous_selection is None:
                        raise AssertionError("DRTP selection missing for completed episode")
                    if getattr(drtp_sampler, "uses_completed_return_feedback", False):
                        drtp_sampler.record_completed_return(previous_selection, drtp_episode_returns[e])
                        drtp_episode_returns[e] = 0.0
                    episode_counts[e] += 1
                    selection = drtp_sampler.select(
                        update=current_update, env_index=e, episode_index=episode_counts[e]
                    )
                    drtp_sampler.apply(env, selection)
                    drtp_selections[e] = selection
                    drtp_rows.append(
                        drtp_sampler.selection_row(current_update, e, episode_counts[e], selection)
                    )
                elif cfg.env_name == "2d_pursuit":
                    env.config.communication_radius = sample_comm_radius(cfg, rng=None if env_rngs is None else env_rngs[e])
                elif cfg.env_name == "3d_intercept":
                    rng = None if env_rngs is None else env_rngs[e]
                    env.config.communication_range_scale = sample_communication_range_scale(cfg, rng=rng)
                    env.config.communication_dropout_prob = sample_float_curriculum(
                        cfg.communication_dropout_prob,
                        cfg.communication_dropout_random_min,
                        cfg.communication_dropout_random_max,
                        rng=rng,
                    )
                    env.config.message_delay_steps = sample_int_curriculum(
                        cfg.message_delay_steps,
                        cfg.message_delay_random_min,
                        cfg.message_delay_random_max,
                        rng=rng,
                    )
                    env.config.radar_dropout_prob = sample_float_curriculum(
                        cfg.radar_dropout_prob,
                        cfg.radar_dropout_random_min,
                        cfg.radar_dropout_random_max,
                        rng=rng,
                    )
                    env.config.failed_blue_agent = sample_failed_blue_agent(cfg, rng=rng)
                    env.config.node_failure_start_step = sample_int_curriculum(
                        cfg.node_failure_start_step,
                        cfg.node_failure_start_random_min,
                        cfg.node_failure_start_random_max,
                        rng=rng,
                    )
                    env.config.node_failure_duration_steps = sample_int_curriculum(
                        cfg.node_failure_duration_steps,
                        cfg.node_failure_duration_random_min,
                        cfg.node_failure_duration_random_max,
                        rng=rng,
                    )
                if telemetry_writer is not None:
                    telemetry_writer.finalize_episode(e)
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
        condition_nominal_buf.append(condition_nominal)
        condition_group_buf.append(condition_group)

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
    next_value_sequence = np.concatenate([values_np[1:], next_values[None, ...]], axis=0)
    td_residuals = rewards_np + cfg.gamma * next_value_sequence * (1.0 - dones_np) - values_np
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
        "td_residuals": td_residuals.astype(np.float32),
        # Training-only condition class.  It is excluded from obs, graph
        # tensors, actor/critic calls, and all evaluation interfaces.
        "condition_is_nominal": np.asarray(condition_nominal_buf, dtype=bool),
        "condition_group": np.asarray(condition_group_buf, dtype="<U3"),
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


def effective_chain_aux_coef(cfg: RIGMAPPOConfig, update: int) -> float:
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


def summarize_role_gate_telemetry(agent: RIGMAPPOAgent, batch: dict, device: torch.device) -> list[dict[str, float | int]]:
    """Summarize final-layer legal-edge attention, gate, and their product.

    This is development telemetry only.  It runs after an update under no-grad and
    never contributes to the optimization graph or action selection.
    """
    if agent.actor.graph_encoder != "multi_relation":
        return []
    num_graphs = min(256, batch["obs"].shape[0] * batch["obs"].shape[1])
    obs = torch.as_tensor(batch["obs"].reshape(-1, agent.num_agents, batch["obs"].shape[-1])[:num_graphs], dtype=torch.float32, device=device)
    node_feat = torch.as_tensor(batch["node_feat"].reshape(-1, *batch["node_feat"].shape[2:])[:num_graphs], dtype=torch.float32, device=device)
    edge_feat = torch.as_tensor(batch["edge_feat"].reshape(-1, *batch["edge_feat"].shape[2:])[:num_graphs], dtype=torch.float32, device=device)
    role = torch.as_tensor(batch["role"].reshape(-1, batch["role"].shape[-1])[:num_graphs], dtype=torch.long, device=device)
    adj = torch.as_tensor(batch["adj"].reshape(-1, *batch["adj"].shape[2:])[:num_graphs], dtype=torch.float32, device=device)
    relation_adj = torch.as_tensor(batch["relation_adj"].reshape(-1, *batch["relation_adj"].shape[2:])[:num_graphs], dtype=torch.float32, device=device)
    with torch.no_grad():
        _, attention, _, _ = agent.actor(
            obs, node_feat, edge_feat, role, adj, agent.num_agents,
            relation_adj=relation_adj, return_chain_aux=True,
        )
    encoder = agent.actor.multi_relation_graph
    rows: list[dict[str, float | int]] = []
    for relation_id, layer in enumerate(encoder.layer2):
        active = relation_adj[:, relation_id] > 0.0
        for receiver_role in range(agent.num_roles):
            for sender_role in range(agent.num_roles):
                pair_mask = active & (role.unsqueeze(2) == receiver_role) & (role.unsqueeze(1) == sender_role)
                count = int(pair_mask.sum().item())
                if count == 0:
                    continue
                if layer.role_pair_gate is None:
                    gate_scalar = torch.ones((), device=device)
                else:
                    pair_index = receiver_role * agent.num_roles + sender_role
                    gate_scalar = torch.sigmoid(layer.role_pair_gate.weight[pair_index]).mean()
                alpha = attention[:, relation_id][pair_mask]
                rows.append({
                    "relation": relation_id,
                    "receiver_role": receiver_role,
                    "sender_role": sender_role,
                    "edge_count": count,
                    "attention_mean": float(alpha.mean().cpu()),
                    "gate_mean": float(gate_scalar.cpu()),
                    "effective_payload_mean": float((alpha * gate_scalar).mean().cpu()),
                })
    return rows


def _gradient_l2_norm(gradients: list[torch.Tensor]) -> torch.Tensor:
    return torch.sqrt(sum(gradient.square().sum() for gradient in gradients))


def _actor_gradients(loss: torch.Tensor, parameters: list[nn.Parameter]) -> list[torch.Tensor]:
    raw = torch.autograd.grad(loss, parameters, retain_graph=True, allow_unused=True)
    return [torch.zeros_like(parameter) if gradient is None else gradient.detach() for parameter, gradient in zip(parameters, raw)]


def _conditioned_actor_gradient(
    mode: str,
    nominal: list[torch.Tensor],
    failure: list[torch.Tensor],
    delta: float = 1e-12,
) -> tuple[list[torch.Tensor], dict[str, float | bool]]:
    """Combine two actor gradients using the frozen UTR/SPC/TCR equations."""
    dot = sum((g_n * g_f).sum() for g_n, g_f in zip(nominal, failure))
    nominal_norm = _gradient_l2_norm(nominal)
    failure_norm = _gradient_l2_norm(failure)
    cosine = dot / (nominal_norm * failure_norm + delta)
    conflict = bool(dot.detach().cpu() < 0.0)
    projected_failure = failure
    projected_nominal = nominal
    if mode not in {"utr", "spc", "tcr"}:
        raise ValueError(f"unsupported conditioned actor mode: {mode}")
    if conflict and mode == "tcr":
        projected_failure = [g_f - dot / (nominal_norm.square() + delta) * g_n for g_n, g_f in zip(nominal, failure)]
    elif conflict and mode == "spc":
        projected_nominal = [g_n - dot / (failure_norm.square() + delta) * g_f for g_n, g_f in zip(nominal, failure)]
        projected_failure = [g_f - dot / (nominal_norm.square() + delta) * g_n for g_n, g_f in zip(nominal, failure)]
    combined = [0.5 * (g_n + g_f) for g_n, g_f in zip(projected_nominal, projected_failure)]
    projected_failure_norm = _gradient_l2_norm(projected_failure)
    projected_nominal_norm = _gradient_l2_norm(projected_nominal)
    post_dot = sum((g_n * g_f).sum() for g_n, g_f in zip(projected_nominal, projected_failure))
    projection_magnitude = _gradient_l2_norm([g_f - projected for g_f, projected in zip(failure, projected_failure)])
    return combined, {
        "gradient_dot": float(dot.detach().cpu()),
        "gradient_cosine": float(cosine.detach().cpu()),
        "projection_applied": conflict and mode != "utr",
        "g_nominal_norm": float(nominal_norm.detach().cpu()),
        "g_failure_norm": float(failure_norm.detach().cpu()),
        "post_projection_cosine": float((post_dot / (projected_nominal_norm * projected_failure_norm + delta)).detach().cpu()),
        "projected_gradient_norm": float(projected_failure_norm.detach().cpu()),
        "projection_magnitude": float(projection_magnitude.detach().cpu()),
        "final_gradient_norm": float(_gradient_l2_norm(combined).detach().cpu()),
    }


def _sam_perturbations(
    gradients: list[torch.Tensor], rho: float, epsilon: float,
) -> tuple[list[torch.Tensor], torch.Tensor, torch.Tensor]:
    """Return standard Euclidean-SAM perturbations without mutating parameters.

    The first-pass PPO actor gradients are deliberately *not* clipped.  SAM's
    definition uses this raw direction.  Only the restored, final combined PPO
    gradient is clipped immediately before the optimiser step.
    """
    gradient_norm = _gradient_l2_norm(gradients)
    scale = float(rho) / (gradient_norm + float(epsilon))
    perturbations = [gradient.detach() * scale for gradient in gradients]
    perturbation_norm = _gradient_l2_norm(perturbations)
    return perturbations, gradient_norm, perturbation_norm


def _restore_parameter_copies(parameters: list[torch.nn.Parameter], copies: list[torch.Tensor]) -> None:
    """Restore base tensors by copy, avoiding round-off from add/subtract."""
    with torch.no_grad():
        for parameter, original in zip(parameters, copies):
            parameter.copy_(original)


def _update_policy_conditioned_actor(
    agent: RIGMAPPOAgent,
    optimizer: optim.Optimizer,
    batch: dict,
    cfg: RIGMAPPOConfig,
    device,
    update: int,
    minibatch_rng: np.random.Generator | None = None,
) -> dict:
    """Frozen Phase-B split actor update; critic remains ordinary PPO."""
    mode = str(cfg.actor_gradient_mode).lower()
    t_steps, n_envs, num_agents = batch["actions"].shape
    num_graphs = t_steps * n_envs
    if num_graphs != cfg.minibatch_graphs:
        raise ValueError("conditioned actor update requires one complete stratified PPO minibatch")
    condition_is_nominal = torch.as_tensor(
        batch["condition_is_nominal"].reshape(num_graphs), dtype=torch.bool, device=device
    )
    nominal_count, failure_count = int(condition_is_nominal.sum().item()), int((~condition_is_nominal).sum().item())
    if nominal_count <= 0 or failure_count <= 0:
        raise RuntimeError("projection minibatch contract violated: both nominal and failure samples are required")
    if nominal_count != failure_count or nominal_count * 2 != num_graphs:
        raise RuntimeError("fixed 50% nominal / 50% failure exposure contract violated")

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
    advantages = torch.as_tensor(batch["advantages"].reshape(num_graphs, num_agents), dtype=torch.float32, device=device)
    returns = torch.as_tensor(batch["returns"].reshape(num_graphs, num_agents), dtype=torch.float32, device=device)
    advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
    chain_aux_coef = effective_chain_aux_coef(cfg, update)
    if update <= cfg.critic_warmup_updates:
        raise RuntimeError("conditioned actor update does not permit critic-only warmup updates")

    actor_parameters = [parameter for parameter in agent.actor.parameters() if parameter.requires_grad]
    sam_enabled = bool(cfg.sam_enabled)
    if sam_enabled and mode != "utr":
        raise RuntimeError("TC-SAM is defined only for the frozen UTR actor update")
    losses, policy_losses, value_losses, entropies, intent_losses, intent_accs = [], [], [], [], [], []
    chain_aux_losses, chain_aux_accs, approx_kls, clip_fractions, grad_norms, explained_variances = [], [], [], [], [], []
    gradient_rows: list[dict[str, float | bool | int]] = []
    epochs_ran = 0
    stop_ppo = False
    # The current frozen contract has one 256-graph minibatch.  Separate
    # shuffles are retained only to make condition membership explicit.
    for _ in range(cfg.ppo_epochs):
        epochs_ran += 1
        if minibatch_rng is None:
            nominal_indices = torch.randperm(nominal_count, device=device)
            failure_indices = torch.randperm(failure_count, device=device)
        else:
            nominal_indices = torch.as_tensor(minibatch_rng.permutation(nominal_count), dtype=torch.long, device=device)
            failure_indices = torch.as_tensor(minibatch_rng.permutation(failure_count), dtype=torch.long, device=device)
        nominal_pool = torch.nonzero(condition_is_nominal, as_tuple=False).reshape(-1)[nominal_indices]
        failure_pool = torch.nonzero(~condition_is_nominal, as_tuple=False).reshape(-1)[failure_indices]
        mb = torch.cat([nominal_pool, failure_pool], dim=0)
        if int(condition_is_nominal[mb].sum().item()) <= 0 or int((~condition_is_nominal[mb]).sum().item()) <= 0:
            raise RuntimeError("stratified actor minibatch builder emitted an invalid projection minibatch")
        _, new_logp, entropy, values, _, intent_logits, chain_aux_logits = agent.get_action_and_value(
            obs[mb], node_feat[mb], edge_feat[mb], role[mb], adj[mb], share_obs[mb],
            relation_adj=relation_adj[mb], action=actions[mb], intent_label=intent_label[mb],
            detach_intent=cfg.detach_intent, oracle_intent=cfg.oracle_intent,
        )
        log_ratio = new_logp - old_logp[mb]
        ratio = log_ratio.exp()
        pg_loss1 = -advantages[mb] * ratio
        pg_loss2 = -advantages[mb] * torch.clamp(ratio, 1.0 - cfg.clip_coef, 1.0 + cfg.clip_coef)
        policy_per_graph = torch.max(pg_loss1, pg_loss2).mean(dim=1)
        entropy_per_graph = entropy.mean(dim=1)
        value_loss = 0.5 * (returns[mb] - values).pow(2).mean()
        if batch["has_intent_label"]:
            intent_per_graph = F.cross_entropy(
                intent_logits.reshape(-1, NUM_INTENTS), intent_label[mb].reshape(-1), reduction="none"
            ).reshape(num_graphs, -1).mean(dim=1)
            intent_acc = (intent_logits.argmax(dim=-1) == intent_label[mb]).float().mean()
        else:
            intent_per_graph = torch.zeros(num_graphs, device=device)
            intent_acc = torch.zeros((), device=device)
        if chain_aux_coef > 0.0:
            chain_target = build_chain_aux_targets(node_feat[mb], edge_feat[mb], relation_adj[mb], num_agents)
            chain_per_graph = F.binary_cross_entropy_with_logits(chain_aux_logits, chain_target, reduction="none").mean(dim=1)
            chain_acc = ((torch.sigmoid(chain_aux_logits) >= 0.5) == (chain_target >= 0.5)).float().mean()
        else:
            chain_per_graph = torch.zeros(num_graphs, device=device)
            chain_acc = torch.zeros((), device=device)
        actor_per_graph = policy_per_graph - cfg.entropy_coef * entropy_per_graph + effective_intent_coef(cfg) * intent_per_graph + chain_aux_coef * chain_per_graph
        actor_loss = actor_per_graph.mean()
        actor_loss_nominal = actor_per_graph[:nominal_count].mean()
        actor_loss_failure = actor_per_graph[nominal_count:].mean()
        if sam_enabled:
            # First pass: raw, full UTR actor loss.  No optimiser state is
            # touched and no clipping is applied before SAM constructs epsilon.
            first_gradients = _actor_gradients(actor_loss, actor_parameters)
            # Audit-only fingerprint: both SAM passes must operate on exactly
            # the same stratified actor minibatch, not merely an equal-size one.
            sam_minibatch_hash = hashlib.sha256(
                mb.detach().cpu().numpy().tobytes()
            ).hexdigest()
            perturbations, first_gradient_norm, perturbation_norm = _sam_perturbations(
                first_gradients, cfg.sam_rho, cfg.sam_epsilon,
            )
            base_parameters = [parameter.detach().clone() for parameter in actor_parameters]
            with torch.no_grad():
                for parameter, perturbation in zip(actor_parameters, perturbations):
                    parameter.add_(perturbation)
            try:
                # The second pass reuses exactly the same minibatch, old policy
                # log-probabilities, returns, and advantages.  The critic is
                # intentionally not part of SAM and remains ordinary PPO.
                _, perturbed_logp, perturbed_entropy, _, _, perturbed_intent_logits, perturbed_chain_aux_logits = agent.get_action_and_value(
                    obs[mb], node_feat[mb], edge_feat[mb], role[mb], adj[mb], share_obs[mb],
                    relation_adj=relation_adj[mb], action=actions[mb], intent_label=intent_label[mb],
                    detach_intent=cfg.detach_intent, oracle_intent=cfg.oracle_intent,
                )
                perturbed_ratio = (perturbed_logp - old_logp[mb]).exp()
                perturbed_pg = torch.max(
                    -advantages[mb] * perturbed_ratio,
                    -advantages[mb] * torch.clamp(perturbed_ratio, 1.0 - cfg.clip_coef, 1.0 + cfg.clip_coef),
                ).mean()
                perturbed_entropy_loss = perturbed_entropy.mean()
                if batch["has_intent_label"]:
                    flat_labels = intent_label[mb].reshape(-1)
                    perturbed_intent_loss = F.cross_entropy(
                        perturbed_intent_logits.reshape(-1, NUM_INTENTS), flat_labels,
                    )
                else:
                    perturbed_intent_loss = torch.zeros((), device=device)
                if chain_aux_coef > 0.0:
                    perturbed_chain_loss = F.binary_cross_entropy_with_logits(perturbed_chain_aux_logits, chain_aux_target)
                else:
                    perturbed_chain_loss = torch.zeros((), device=device)
                perturbed_actor_loss = (
                    perturbed_pg - cfg.entropy_coef * perturbed_entropy_loss
                    + effective_intent_coef(cfg) * perturbed_intent_loss
                    + chain_aux_coef * perturbed_chain_loss
                )
                combined_gradients = _actor_gradients(perturbed_actor_loss, actor_parameters)
                second_gradient_norm = _gradient_l2_norm(combined_gradients)
            finally:
                _restore_parameter_copies(actor_parameters, base_parameters)
            # These entries retain the existing UTR gradient telemetry schema
            # while making explicit that no nominal/failure projection occurred.
            gradient_info = {
                "gradient_dot": 0.0, "gradient_cosine": 0.0, "projection_applied": False,
                "g_nominal_norm": float(first_gradient_norm.detach().cpu()),
                "g_failure_norm": 0.0, "post_projection_cosine": 0.0,
                "projected_gradient_norm": float(second_gradient_norm.detach().cpu()),
                "projection_magnitude": 0.0,
                "final_gradient_norm": float(second_gradient_norm.detach().cpu()),
                "sam_enabled": True,
                "sam_first_gradient_norm": float(first_gradient_norm.detach().cpu()),
                "sam_perturbation_norm": float(perturbation_norm.detach().cpu()),
                "sam_second_gradient_norm": float(second_gradient_norm.detach().cpu()),
                "sam_first_minibatch_hash": sam_minibatch_hash,
                "sam_second_minibatch_hash": sam_minibatch_hash,
            }
        else:
            nominal_gradients = _actor_gradients(actor_loss_nominal, actor_parameters)
            failure_gradients = _actor_gradients(actor_loss_failure, actor_parameters)
            combined_gradients, gradient_info = _conditioned_actor_gradient(mode, nominal_gradients, failure_gradients)
            gradient_info.update({
                "sam_enabled": False, "sam_first_gradient_norm": 0.0,
                "sam_perturbation_norm": 0.0, "sam_second_gradient_norm": 0.0,
                "sam_first_minibatch_hash": "", "sam_second_minibatch_hash": "",
            })
        optimizer.zero_grad(set_to_none=True)
        (cfg.value_coef * value_loss).backward()
        for parameter, gradient in zip(actor_parameters, combined_gradients):
            parameter.grad = gradient
        grad_norm = nn.utils.clip_grad_norm_(agent.parameters(), cfg.max_grad_norm)
        optimizer.step()
        with torch.no_grad():
            approx_kl = ((ratio - 1.0) - log_ratio).mean()
            clip_fraction = ((ratio - 1.0).abs() > cfg.clip_coef).float().mean()
            value_error_var = torch.var(returns[mb] - values)
            returns_var = torch.var(returns[mb])
            explained_variance = 1.0 - value_error_var / (returns_var + 1e-8)
        losses.append(float((actor_loss + cfg.value_coef * value_loss).detach().cpu()))
        policy_losses.append(float(policy_per_graph.mean().detach().cpu()))
        value_losses.append(float(value_loss.detach().cpu()))
        entropies.append(float(entropy_per_graph.mean().detach().cpu()))
        intent_losses.append(float(intent_per_graph.mean().detach().cpu()))
        intent_accs.append(float(intent_acc.detach().cpu()))
        chain_aux_losses.append(float(chain_per_graph.mean().detach().cpu()))
        chain_aux_accs.append(float(chain_acc.detach().cpu()))
        approx_kls.append(float(approx_kl.detach().cpu()))
        clip_fractions.append(float(clip_fraction.detach().cpu()))
        grad_norms.append(float(grad_norm.detach().cpu()))
        explained_variances.append(float(explained_variance.detach().cpu()))
        gradient_rows.append({"nominal_sample_count": nominal_count, "failure_sample_count": failure_count, **gradient_info})
        if cfg.target_kl is not None and float(approx_kl.detach().cpu()) > cfg.target_kl:
            stop_ppo = True
        if stop_ppo:
            break
    def mean_row(name: str) -> float:
        return float(np.mean([float(row[name]) for row in gradient_rows]))
    return {
        "loss": float(np.mean(losses)), "policy_loss": float(np.mean(policy_losses)),
        "value_loss": float(np.mean(value_losses)), "entropy": float(np.mean(entropies)),
        "intent_loss": float(np.mean(intent_losses)), "intent_acc": float(np.mean(intent_accs)),
        "chain_aux_loss": float(np.mean(chain_aux_losses)), "chain_aux_acc": float(np.mean(chain_aux_accs)),
        "chain_aux_effective_coef": chain_aux_coef, "approx_kl": float(np.mean(approx_kls)),
        "clip_fraction": float(np.mean(clip_fractions)), "grad_norm": float(np.mean(grad_norms)),
        "explained_variance": float(np.mean(explained_variances)), "ppo_epochs_ran": epochs_ran,
        "critic_warmup_active": 0.0, "role_gate_grad_norm": 0.0, "role_gate_mean": 1.0,
        "role_gate_std": 0.0, "role_gate_min": 1.0, "role_gate_max": 1.0,
        "role_gate_displacement_l2": 0.0, "actor_nominal_sample_count": mean_row("nominal_sample_count"),
        "actor_failure_sample_count": mean_row("failure_sample_count"), "actor_gradient_dot": mean_row("gradient_dot"),
        "actor_gradient_cosine": mean_row("gradient_cosine"),
        "actor_post_projection_cosine": mean_row("post_projection_cosine"),
        "actor_projection_applied_fraction": float(np.mean([float(row["projection_applied"]) for row in gradient_rows])),
        "actor_g_nominal_norm": mean_row("g_nominal_norm"), "actor_g_failure_norm": mean_row("g_failure_norm"),
        "actor_projected_gradient_norm": mean_row("projected_gradient_norm"),
        "actor_projection_magnitude": mean_row("projection_magnitude"),
        "actor_final_gradient_norm": mean_row("final_gradient_norm"),
        "sam_enabled": float(np.mean([float(row["sam_enabled"]) for row in gradient_rows])),
        "sam_first_gradient_norm": mean_row("sam_first_gradient_norm"),
        "sam_perturbation_norm": mean_row("sam_perturbation_norm"),
        "sam_second_gradient_norm": mean_row("sam_second_gradient_norm"),
        "actor_gradient_rows": gradient_rows,
    }


def _snapshot_optimizer_parameter_states(
    optimizer: optim.Optimizer,
    parameters: list[torch.nn.Parameter],
) -> dict[torch.nn.Parameter, dict | None]:
    """Copy Adam state slots for an exact parameter-local rollback."""
    return {
        parameter: copy.deepcopy(optimizer.state[parameter]) if parameter in optimizer.state else None
        for parameter in parameters
    }


def _restore_optimizer_parameter_states(
    optimizer: optim.Optimizer,
    snapshots: dict[torch.nn.Parameter, dict | None],
) -> None:
    for parameter, state in snapshots.items():
        if state is None:
            optimizer.state.pop(parameter, None)
        else:
            optimizer.state[parameter] = copy.deepcopy(state)


def _parameter_displacement_l2(
    parameters: list[torch.nn.Parameter],
    originals: list[torch.Tensor],
) -> float:
    with torch.no_grad():
        total = sum((parameter.detach() - original).square().sum() for parameter, original in zip(parameters, originals))
        return float(torch.sqrt(total).cpu())


def _set_parameter_interpolation_(
    parameters: list[torch.nn.Parameter],
    originals: list[torch.Tensor],
    attempted: list[torch.Tensor],
    alpha: float,
) -> None:
    """Set parameters to original + alpha * (attempted - original)."""
    with torch.no_grad():
        for parameter, original, target in zip(parameters, originals, attempted):
            parameter.copy_(original + float(alpha) * (target - original))


def _nested_tensors_are_finite(value) -> bool:
    if isinstance(value, torch.Tensor):
        return bool(torch.isfinite(value).all().item())
    if isinstance(value, dict):
        return all(_nested_tensors_are_finite(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_nested_tensors_are_finite(item) for item in value)
    return True


def update_policy(
    agent: RIGMAPPOAgent,
    optimizer: optim.Optimizer,
    batch: dict,
    cfg: RIGMAPPOConfig,
    device,
    update: int,
    minibatch_rng: np.random.Generator | None = None,
):
    if str(cfg.actor_gradient_mode).lower() != "standard":
        return _update_policy_conditioned_actor(agent, optimizer, batch, cfg, device, update, minibatch_rng=minibatch_rng)
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
    chain_aux_coef = effective_chain_aux_coef(cfg, update)
    critic_warmup_active = update <= cfg.critic_warmup_updates

    losses, policy_losses, value_losses, entropies, intent_losses, intent_accs = [], [], [], [], [], []
    chain_aux_losses, chain_aux_accs = [], []
    approx_kls, clip_fractions, grad_norms, explained_variances = [], [], [], []
    gate_grad_norms, gate_means, gate_stds, gate_mins, gate_maxs, gate_displacements = [], [], [], [], [], []
    policy_guard_mode = str(cfg.policy_update_guard_mode).lower()
    rollback_guard_enabled = policy_guard_mode == "post_step_actor_rollback"
    backtrack_guard_enabled = policy_guard_mode == "post_step_actor_backtrack"
    policy_guard_enabled = rollback_guard_enabled or backtrack_guard_enabled
    if policy_guard_enabled and num_graphs != cfg.minibatch_graphs:
        raise RuntimeError("post-step actor guards require one complete rollout minibatch per PPO epoch")
    actor_parameters = [parameter for parameter in agent.actor.parameters() if parameter.requires_grad]
    policy_post_step_kls: list[float] = []
    actor_attempted_update_norms: list[float] = []
    actor_accepted_update_norms: list[float] = []
    policy_steps_attempted = 0
    policy_steps_accepted = 0
    policy_guard_triggered = False
    policy_guard_reason = ""
    policy_guard_epoch = 0
    actor_rollback_l2 = 0.0
    actor_projection_l2 = 0.0
    policy_backtrack_alpha = 1.0
    policy_backtrack_iterations = 0
    actor_optimizer_state_restored = False
    actor_optimizer_state_retained_after_projection = False
    critic_step_retained_after_actor_rollback = False
    critic_step_retained_after_policy_guard = False
    final_accepted_policy_kl = 0.0

    def current_policy_kl() -> float:
        with torch.no_grad():
            _, current_logp, _, _, _, _, _ = agent.get_action_and_value(
                obs, node_feat, edge_feat, role, adj, share_obs,
                relation_adj=relation_adj, action=actions, intent_label=intent_label,
                detach_intent=cfg.detach_intent, oracle_intent=cfg.oracle_intent,
            )
            current_log_ratio = current_logp - old_logp
            current_ratio = current_log_ratio.exp()
            current_kl = ((current_ratio - 1.0) - current_log_ratio).mean()
        return float(current_kl.detach().cpu())
    indices = np.arange(num_graphs)
    epochs_ran = 0
    stop_ppo = False
    for _ in range(cfg.ppo_epochs):
        epochs_ran += 1
        if minibatch_rng is None:
            np.random.shuffle(indices)
        else:
            indices = minibatch_rng.permutation(num_graphs)
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
            gate_grads = [
                parameter.grad.detach()
                for name, parameter in agent.named_parameters()
                if "role_pair_gate" in name and parameter.grad is not None
            ]
            gate_grad_norms.append(
                float(torch.sqrt(sum(gradient.square().sum() for gradient in gate_grads)).cpu()) if gate_grads else 0.0
            )
            grad_norm = nn.utils.clip_grad_norm_(agent.parameters(), cfg.max_grad_norm)
            if policy_guard_enabled:
                actor_state_before = copy.deepcopy(agent.actor.state_dict())
                actor_parameters_before = [parameter.detach().clone() for parameter in actor_parameters]
                actor_optimizer_state_before = _snapshot_optimizer_parameter_states(optimizer, actor_parameters)
                transaction_model_state_before = copy.deepcopy(agent.state_dict())
                transaction_optimizer_state_before = copy.deepcopy(optimizer.state_dict())
            optimizer.step()

            if policy_guard_enabled:
                policy_steps_attempted += 1
                attempted_update_l2 = _parameter_displacement_l2(actor_parameters, actor_parameters_before)
                actor_attempted_update_norms.append(attempted_update_l2)
                finite_precheck = (
                    math.isfinite(float(grad_norm.detach().cpu()))
                    and _nested_tensors_are_finite(agent.state_dict())
                    and _nested_tensors_are_finite(optimizer.state_dict())
                )
                if not finite_precheck:
                    agent.load_state_dict(transaction_model_state_before, strict=True)
                    optimizer.load_state_dict(transaction_optimizer_state_before)
                    raise FloatingPointError("non-finite Stable-v2 policy update transaction")
                post_step_kl_value = current_policy_kl()
                policy_post_step_kls.append(post_step_kl_value)
                finite_transaction = (
                    math.isfinite(post_step_kl_value)
                    and _nested_tensors_are_finite(agent.state_dict())
                    and _nested_tensors_are_finite(optimizer.state_dict())
                )
                if not finite_transaction:
                    agent.load_state_dict(transaction_model_state_before, strict=True)
                    optimizer.load_state_dict(transaction_optimizer_state_before)
                    raise FloatingPointError("non-finite Stable-v2 policy update transaction")
                if post_step_kl_value > float(cfg.target_kl):
                    policy_guard_triggered = True
                    policy_guard_epoch = epochs_ran
                    critic_step_retained_after_policy_guard = True
                    if rollback_guard_enabled:
                        agent.actor.load_state_dict(actor_state_before, strict=True)
                        _restore_optimizer_parameter_states(optimizer, actor_optimizer_state_before)
                        policy_guard_reason = "post_step_kl_exceeded"
                        actor_rollback_l2 = attempted_update_l2
                        actor_optimizer_state_restored = True
                        critic_step_retained_after_actor_rollback = True
                        actor_accepted_update_norms.append(0.0)
                        final_accepted_policy_kl = float(approx_kl.detach().cpu())
                    else:
                        actor_parameters_attempted = [parameter.detach().clone() for parameter in actor_parameters]
                        _set_parameter_interpolation_(
                            actor_parameters, actor_parameters_before, actor_parameters_attempted, 0.0
                        )
                        pre_step_kl_value = current_policy_kl()
                        if not math.isfinite(pre_step_kl_value) or pre_step_kl_value > float(cfg.target_kl):
                            agent.load_state_dict(transaction_model_state_before, strict=True)
                            optimizer.load_state_dict(transaction_optimizer_state_before)
                            raise FloatingPointError("invalid pre-step policy KL for Stable-v2 backtracking")
                        lower, upper = 0.0, 1.0
                        for _ in range(POLICY_KL_BACKTRACK_BISECTION_STEPS):
                            midpoint = 0.5 * (lower + upper)
                            _set_parameter_interpolation_(
                                actor_parameters, actor_parameters_before, actor_parameters_attempted, midpoint
                            )
                            midpoint_kl = current_policy_kl()
                            if not math.isfinite(midpoint_kl):
                                agent.load_state_dict(transaction_model_state_before, strict=True)
                                optimizer.load_state_dict(transaction_optimizer_state_before)
                                raise FloatingPointError("non-finite Stable-v2 backtracking transaction")
                            if midpoint_kl <= float(cfg.target_kl):
                                lower = midpoint
                            else:
                                upper = midpoint
                        _set_parameter_interpolation_(
                            actor_parameters, actor_parameters_before, actor_parameters_attempted, lower
                        )
                        final_accepted_policy_kl = current_policy_kl()
                        if not math.isfinite(final_accepted_policy_kl) or final_accepted_policy_kl > float(cfg.target_kl):
                            agent.load_state_dict(transaction_model_state_before, strict=True)
                            optimizer.load_state_dict(transaction_optimizer_state_before)
                            raise FloatingPointError("Stable-v2 backtracking failed its final KL assertion")
                        accepted_update_l2 = _parameter_displacement_l2(actor_parameters, actor_parameters_before)
                        actor_projection_l2 = _parameter_displacement_l2(actor_parameters, actor_parameters_attempted)
                        policy_backtrack_alpha = lower
                        policy_backtrack_iterations = POLICY_KL_BACKTRACK_BISECTION_STEPS
                        actor_optimizer_state_retained_after_projection = True
                        policy_guard_reason = "post_step_kl_backtracked"
                        if accepted_update_l2 > 0.0:
                            policy_steps_accepted += 1
                        actor_accepted_update_norms.append(accepted_update_l2)
                    stop_ppo = True
                else:
                    policy_steps_accepted += 1
                    actor_accepted_update_norms.append(attempted_update_l2)
                    final_accepted_policy_kl = post_step_kl_value

            gates = [
                torch.sigmoid(parameter.detach())
                for name, parameter in agent.named_parameters()
                if "role_pair_gate" in name
            ]
            if gates:
                gate_values = torch.cat([gate.reshape(-1) for gate in gates])
                gate_means.append(float(gate_values.mean().cpu()))
                gate_stds.append(float(gate_values.std(unbiased=False).cpu()))
                gate_mins.append(float(gate_values.min().cpu()))
                gate_maxs.append(float(gate_values.max().cpu()))
                displacement_sq = sum(
                    (parameter.detach() - agent._role_gate_initial_state[name].to(parameter.device)).square().sum()
                    for name, parameter in agent.named_parameters()
                    if name in agent._role_gate_initial_state
                )
                gate_displacements.append(float(torch.sqrt(displacement_sq).cpu()))

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
            if stop_ppo:
                break
        if not policy_guard_enabled and cfg.target_kl is not None and approx_kls and float(np.mean(approx_kls[-max(1, num_graphs // cfg.minibatch_graphs) :])) > cfg.target_kl:
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
        "role_gate_grad_norm": float(np.mean(gate_grad_norms)) if gate_grad_norms else 0.0,
        "role_gate_mean": float(np.mean(gate_means)) if gate_means else 1.0,
        "role_gate_std": float(np.mean(gate_stds)) if gate_stds else 0.0,
        "role_gate_min": float(np.mean(gate_mins)) if gate_mins else 1.0,
        "role_gate_max": float(np.mean(gate_maxs)) if gate_maxs else 1.0,
        "role_gate_displacement_l2": float(np.mean(gate_displacements)) if gate_displacements else 0.0,
        "policy_kl_post_step": final_accepted_policy_kl if policy_guard_enabled else 0.0,
        "policy_kl_attempted_max": float(max(policy_post_step_kls)) if policy_post_step_kls else 0.0,
        "policy_kl_threshold": float(cfg.target_kl) if policy_guard_enabled else 0.0,
        "policy_guard_triggered": float(policy_guard_triggered),
        "policy_guard_reason": policy_guard_reason,
        "policy_guard_epoch": policy_guard_epoch,
        "policy_steps_attempted": policy_steps_attempted,
        "policy_steps_accepted": policy_steps_accepted,
        "actor_attempted_update_l2": float(np.mean(actor_attempted_update_norms)) if actor_attempted_update_norms else 0.0,
        "actor_accepted_update_l2": float(np.mean(actor_accepted_update_norms)) if actor_accepted_update_norms else 0.0,
        "actor_rollback_l2": actor_rollback_l2,
        "actor_projection_l2": actor_projection_l2,
        "policy_backtrack_alpha": policy_backtrack_alpha,
        "policy_backtrack_iterations": policy_backtrack_iterations,
        "actor_optimizer_state_restored": float(actor_optimizer_state_restored),
        "actor_optimizer_state_retained_after_projection": float(actor_optimizer_state_retained_after_projection),
        "critic_step_retained_after_actor_rollback": float(critic_step_retained_after_actor_rollback),
        "critic_step_retained_after_policy_guard": float(critic_step_retained_after_policy_guard),
    }
