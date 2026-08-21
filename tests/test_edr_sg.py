"""Regression tests for the frozen EDR aggregation replacement."""

from __future__ import annotations

import torch

from algorithms.ri_gmappo.simple_ri_gmappo import (
    EdgeDeletionResilientGraphAttentionLayer,
    RIGMAPPOAgent,
)
from scripts.telemetry_native_t0 import NOMINAL, make_env


def _dimensions():
    env = make_env(920000, NOMINAL)
    _, share_obs, graph = env.reset()
    return env, share_obs, graph


def _agent(graph_encoder: str) -> RIGMAPPOAgent:
    env, share_obs, graph = _dimensions()
    return RIGMAPPOAgent(
        obs_dim=env.obs_dim,
        node_feat_dim=graph["node_feat"].shape[-1],
        edge_feat_dim=graph["edge_feat"].shape[-1],
        share_obs_dim=share_obs.shape[-1],
        action_dim=env.action_dim,
        num_agents=env.num_agents,
        num_roles=max(4, int(graph["role"].max()) + 1),
        hidden_dim=115,
        role_dim=8,
        intent_dim=8,
        graph_encoder=graph_encoder,
        role_gate_mode="none",
        use_intent_context=False,
    )


def test_edr_has_exact_matched_parameter_count():
    assert sum(parameter.numel() for parameter in _agent("single").parameters()) == 116_728
    assert sum(parameter.numel() for parameter in _agent("edr").parameters()) == 116_728


def test_edr_deletion_keeps_surviving_contributions_exactly_local():
    torch.manual_seed(7)
    layer = EdgeDeletionResilientGraphAttentionLayer(3, 3, edge_dim=2)
    x = torch.randn(1, 4, 3)
    edge = torch.randn(1, 4, 4, 2)
    adj = torch.ones(1, 4, 4)
    deleted = adj.clone()
    deleted[0, 2, 1] = 0.0

    def contributions(current_adj: torch.Tensor) -> torch.Tensor:
        h = layer.proj(x)
        nodes = h.shape[1]
        hi = h.unsqueeze(2).expand(-1, nodes, nodes, -1)
        hj = h.unsqueeze(1).expand(-1, nodes, nodes, -1)
        scores = layer.attn(torch.cat([hi, hj], dim=-1)).squeeze(-1)
        scores = layer.leaky_relu(scores + layer.edge_score(edge).squeeze(-1))
        mask = torch.clamp(current_adj + torch.eye(nodes).unsqueeze(0), 0.0, 1.0)
        return (torch.sigmoid(scores) * mask).unsqueeze(-1) * h.unsqueeze(1)

    before, after = contributions(adj), contributions(deleted)
    survivors = [0, 2, 3]
    assert torch.equal(before[0, 2, survivors], after[0, 2, survivors])


def test_edr_actor_forward_is_finite_and_deterministic():
    env, share_obs, graph = _dimensions()
    agent = _agent("edr").eval()
    args = (
        torch.as_tensor(env.reset()[0][None], dtype=torch.float32),
        torch.as_tensor(graph["node_feat"][None], dtype=torch.float32),
        torch.as_tensor(graph["edge_feat"][None], dtype=torch.float32),
        torch.as_tensor(graph["role"][None], dtype=torch.long),
        torch.as_tensor(graph["adj"][None], dtype=torch.float32),
        torch.as_tensor(share_obs[None], dtype=torch.float32),
    )
    with torch.no_grad():
        left = agent.get_action_and_value(*args, deterministic=True)[0]
        right = agent.get_action_and_value(*args, deterministic=True)[0]
    assert torch.equal(left, right)
    assert torch.isfinite(left.float()).all()
