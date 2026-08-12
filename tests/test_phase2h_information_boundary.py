"""Pre-training information-boundary regression tests.

These tests deliberately hold actor-visible tensors fixed while mutating
environment-only state. They guard against accidental hidden-state reads in
the policy object; full environment tape/graph provenance remains a separate
Phase 2H gate.
"""

from __future__ import annotations

import numpy as np
import torch

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOAgent, stack_graphs
from envs import UAVIntercept3DConfig, UAVIntercept3DEnv


def _agent_and_inputs(seed: int = 7):
    env = UAVIntercept3DEnv(UAVIntercept3DConfig(seed=seed))
    obs, share, graph = env.reset()
    agent = RIGMAPPOAgent(
        obs_dim=env.obs_dim,
        node_feat_dim=graph["node_feat"].shape[-1],
        edge_feat_dim=graph["edge_feat"].shape[-1],
        share_obs_dim=env.share_obs_dim,
        action_dim=env.action_dim,
        num_agents=env.num_agents,
        hidden_dim=32,
        role_dim=8,
        intent_dim=8,
        graph_encoder="multi_relation",
        num_roles=5,
        use_intent_context=False,
    ).eval()
    return env, agent, obs, share, graph


def _logits(agent, obs, share, graph):
    with torch.no_grad():
        out = agent.get_action_and_value(
            torch.as_tensor(obs[None], dtype=torch.float32),
            torch.as_tensor(graph["node_feat"][None], dtype=torch.float32),
            torch.as_tensor(graph["edge_feat"][None], dtype=torch.float32),
            torch.as_tensor(graph["role"][None], dtype=torch.long),
            torch.as_tensor(graph["adj"][None], dtype=torch.float32),
            torch.as_tensor(share[None], dtype=torch.float32),
            relation_adj=torch.as_tensor(graph["relation_adj"][None], dtype=torch.float32),
            deterministic=True,
            intent_label=torch.as_tensor(graph["intent_label"][None], dtype=torch.long),
            detach_intent=False,
            oracle_intent=False,
        )
    return out[1].cpu()


def test_hidden_environment_state_does_not_change_fixed_actor_inputs():
    env, agent, obs, share, graph = _agent_and_inputs()
    before = _logits(agent, obs, share, graph)
    env.red_pos[:] = np.asarray([[123.0, 456.0, 789.0]], dtype=np.float32)
    env.blue_pos[:] = 0.0
    env.target_cache_pos[:] = 999.0
    env.target_cache_confidence[:] = 0.0
    after = _logits(agent, obs, share, graph)
    torch.testing.assert_close(before, after, rtol=0.0, atol=1e-7)


def test_undelivered_message_state_does_not_change_fixed_actor_inputs():
    env, agent, obs, share, graph = _agent_and_inputs(8)
    before = _logits(agent, obs, share, graph)
    env.pending_messages = [{"hidden": "changed"}]
    env.target_cache_pos[:] = -1234.0
    env.target_cache_valid[:] = 0.0
    after = _logits(agent, obs, share, graph)
    torch.testing.assert_close(before, after, rtol=0.0, atol=1e-7)


def test_failure_hidden_state_does_not_change_fixed_actor_inputs():
    env, agent, obs, share, graph = _agent_and_inputs(9)
    before = _logits(agent, obs, share, graph)
    env.failed_blue_agent = 1
    env.target_cache_path = [[2, 1], [0, 2], [1, 0]]
    env.target_cache_confidence[:] = 0.01
    after = _logits(agent, obs, share, graph)
    torch.testing.assert_close(before, after, rtol=0.0, atol=1e-7)
