"""Static smoke test for the role-specific actor-head interface."""
from __future__ import annotations

import numpy as np

from scripts.run_l1_role_specific_development import cfg, OUT
from scripts import run_new_project_l0_single_interceptor as l0
from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOAgent


def main() -> None:
    test_cfg = cfg(8301, OUT / "_interface_test", updates=1)
    env = l0.make_env(test_cfg, 830_000, training=False)
    obs, share, graph = env.reset()
    agent = RIGMAPPOAgent(
        obs_dim=env.obs_dim, node_feat_dim=graph["node_feat"].shape[-1],
        edge_feat_dim=graph["edge_feat"].shape[-1], share_obs_dim=env.share_obs_dim,
        action_dim=env.action_dim, num_agents=env.num_agents, num_roles=5,
        hidden_dim=test_cfg.hidden_dim, role_dim=test_cfg.role_dim,
        intent_dim=test_cfg.intent_dim, graph_encoder=test_cfg.graph_encoder,
        use_intent_context=False, hybrid_action=True, role_specific_actor_heads=True,
    )
    assert agent.actor.role_specific_actor_heads
    assert len(agent.actor.policy_heads) >= 3
    actions = np.asarray(l0.agent_actions(agent, obs, share, graph), dtype=np.float32)
    assert actions.shape == (env.config.num_blue, 3)
    assert np.isfinite(actions).all()
    print("ROLE_SPECIFIC_ACTOR_HEADS_SMOKE_PASS")


if __name__ == "__main__":
    main()
