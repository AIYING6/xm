"""G1 input-boundary smoke test for commitment-level plain MAPPO."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOAgent, RIGMAPPOConfig, make_env, stack_graphs


def main() -> None:
    cfg = RIGMAPPOConfig(
        env_name="commitment_handoff_3d",
        seed=173,
        graph_encoder="no_graph",
        role_gate_mode="none",
        intent_coef=0.0,
        chain_aux_coef=0.0,
        hidden_dim=48,
        timed_handoff_context_mode="balanced",
        device="cpu",
    )
    current = make_env(cfg, 100, training=False)
    future = make_env(cfg, 101, training=False)
    obs, share, graph = current.reset()
    future_obs, _, _ = future.reset()
    assert current.action_dim == 2 and future.action_dim == 2
    assert tuple(obs[0, 34:36]) == (1.0, 0.0)
    assert tuple(future_obs[0, 34:36]) == (0.0, 1.0)
    agent = RIGMAPPOAgent(
        obs_dim=obs.shape[-1], node_feat_dim=graph["node_feat"].shape[-1], edge_feat_dim=graph["edge_feat"].shape[-1],
        share_obs_dim=share.shape[-1], action_dim=current.action_dim, num_agents=current.num_agents,
        num_roles=max(4, int(np.max(graph["role"])) + 1), hidden_dim=cfg.hidden_dim, role_dim=cfg.role_dim,
        intent_dim=cfg.intent_dim, graph_encoder="no_graph", role_gate_mode="none", use_intent_context=False,
    ).eval()
    packed = stack_graphs([graph])
    actor_obs = torch.as_tensor(obs[None, ...], dtype=torch.float32)
    role = torch.as_tensor(packed["role"], dtype=torch.long)
    node = torch.as_tensor(packed["node_feat"], dtype=torch.float32)
    edge = torch.as_tensor(packed["edge_feat"], dtype=torch.float32)
    adj = torch.as_tensor(packed["adj"], dtype=torch.float32)
    relation = torch.as_tensor(packed["relation_adj"], dtype=torch.float32)
    with torch.no_grad():
        a, *_ = agent.actor(actor_obs, node, edge, role, adj, current.num_agents, relation_adj=relation, return_chain_aux=True)
        b, *_ = agent.actor(actor_obs, node + 11.0, edge + 17.0, torch.zeros_like(role), torch.zeros_like(adj), current.num_agents, relation_adj=torch.zeros_like(relation), return_chain_aux=True)
    assert a.shape[-1] == 2
    assert torch.allclose(a, b, atol=0.0, rtol=0.0)
    print("PASS: commitment plain MAPPO has two relay commitments and ignores graph-only tensors")


if __name__ == "__main__":
    main()
