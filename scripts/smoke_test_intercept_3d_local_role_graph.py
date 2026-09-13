"""Verify that the 3DOF local-role graph actor cannot read hidden target state."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import (  # noqa: E402
    RIGMAPPOAgent,
    build_local_role_graph_from_observation,
)
from envs import UAVIntercept3DConfig, UAVIntercept3DEnv  # noqa: E402


def main() -> None:
    torch.manual_seed(17)
    env = UAVIntercept3DEnv(UAVIntercept3DConfig(seed=17))
    obs, share_obs, graph = env.reset()
    agent = RIGMAPPOAgent(
        obs_dim=env.obs_dim,
        node_feat_dim=graph["node_feat"].shape[-1],
        edge_feat_dim=graph["edge_feat"].shape[-1],
        share_obs_dim=share_obs.shape[-1],
        action_dim=env.action_dim,
        num_agents=env.num_agents,
        num_roles=5,
        hidden_dim=64,
        role_dim=8,
        intent_dim=8,
        graph_encoder="local_relation",
        use_intent_context=False,
    ).eval()

    local_obs = torch.as_tensor(obs[None], dtype=torch.float32)
    # Simulate an unobserved target and arbitrary placeholder values.
    local_obs[..., 18] = 0.0
    local_obs[..., 31] = 0.0
    altered_obs = local_obs.clone()
    altered_obs[..., 8:18] = torch.randn_like(altered_obs[..., 8:18]) * 100.0

    node = torch.as_tensor(graph["node_feat"][None], dtype=torch.float32)
    edge = torch.as_tensor(graph["edge_feat"][None], dtype=torch.float32)
    role = torch.as_tensor(graph["role"][None], dtype=torch.long)
    adj = torch.as_tensor(graph["adj"][None], dtype=torch.float32)
    relation = torch.as_tensor(graph["relation_adj"][None], dtype=torch.float32)
    altered_global_node = torch.randn_like(node)
    altered_global_edge = torch.randn_like(edge)
    altered_global_adj = torch.ones_like(adj)
    altered_global_relation = torch.ones_like(relation)

    with torch.no_grad():
        logits = agent.actor(local_obs, node, edge, role, adj, env.num_agents, relation_adj=relation)[0]
        altered_logits = agent.actor(
            altered_obs, altered_global_node, altered_global_edge, role, altered_global_adj,
            env.num_agents, relation_adj=altered_global_relation,
        )[0]
    assert torch.equal(logits, altered_logits), "hidden target placeholders or global graph changed local actor logits"

    _, _, relation_a, _, _ = build_local_role_graph_from_observation(local_obs)
    visible_obs = local_obs.clone()
    visible_obs[..., 18] = 1.0
    visible_obs[..., 8] = 0.4
    _, _, relation_b, _, _ = build_local_role_graph_from_observation(visible_obs)
    assert float(relation_a[:, 0, 0, 4].sum()) == 0.0
    assert float(relation_b[:, 0, 0, 4].sum()) == float(env.num_agents)
    print("PASS: local-role graph masks hidden targets and ignores global graph inputs")


if __name__ == "__main__":
    main()
