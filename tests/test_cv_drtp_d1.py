"""Rollout-free D1 checks for the opt-in CV-DRTP critic branch."""
from __future__ import annotations

import copy

import numpy as np
import torch

from algorithms.ri_gmappo.simple_ri_gmappo import (
    RIGMAPPOAgent,
    RIGMAPPOConfig,
    load_training_checkpoint,
    make_optimizer,
    save_training_checkpoint,
    update_policy,
)
from tests.test_tc_sam import batch


def model(enabled: bool) -> RIGMAPPOAgent:
    return RIGMAPPOAgent(
        obs_dim=34, node_feat_dim=20, edge_feat_dim=17, share_obs_dim=47,
        action_dim=27, num_agents=3, num_roles=5, hidden_dim=115,
        role_dim=8, intent_dim=8, graph_encoder="single", role_gate_mode="none",
        use_intent_context=False, counterfactual_critic_enabled=enabled,
    )


def cfg(enabled: bool) -> RIGMAPPOConfig:
    return RIGMAPPOConfig(
        env_name="3d_intercept", num_envs=4, rollout_steps=64, minibatch_graphs=256,
        ppo_epochs=1, graph_encoder="single", hidden_dim=115, role_dim=8, intent_dim=8,
        role_gate_mode="none", actor_gradient_mode="standard", critic_warmup_updates=0,
        evaluation_enabled=False, device="cpu", counterfactual_critic_enabled=enabled,
    )


def on_policy_batch(agent: RIGMAPPOAgent) -> dict:
    state = batch()
    steps, envs, agents = state["actions"].shape
    graphs = steps * envs
    with torch.no_grad():
        _, logp, _, _, _, _, _ = agent.get_action_and_value(
            torch.as_tensor(state["obs"].reshape(graphs, agents, -1)),
            torch.as_tensor(state["node_feat"].reshape(graphs, *state["node_feat"].shape[2:])),
            torch.as_tensor(state["edge_feat"].reshape(graphs, *state["edge_feat"].shape[2:])),
            torch.as_tensor(state["role"].reshape(graphs, *state["role"].shape[2:])),
            torch.as_tensor(state["adj"].reshape(graphs, *state["adj"].shape[2:])),
            torch.as_tensor(state["share_obs"].reshape(graphs, agents, -1)),
            relation_adj=torch.as_tensor(state["relation_adj"].reshape(graphs, *state["relation_adj"].shape[2:])),
            action=torch.as_tensor(state["actions"].reshape(graphs, agents)),
            intent_label=torch.as_tensor(state["intent_label"].reshape(graphs, -1)),
        )
    state["logp"] = logp.reshape(steps, envs, agents).numpy()
    return state


def test_counterfactual_baseline_is_finite_action_expectation():
    torch.manual_seed(6101)
    agent = model(True)
    state = batch()
    graphs, agents = 7, 3
    share = torch.as_tensor(state["share_obs"].reshape(-1, agents, 47)[:graphs])
    role = torch.as_tensor(state["role"].reshape(-1, 4)[:graphs])
    actions = torch.as_tensor(state["actions"].reshape(-1, agents)[:graphs])
    probabilities = torch.softmax(torch.randn(graphs, agents, 27), dim=-1)
    advantage = agent.counterfactual_advantage(share, role, actions, probabilities)
    q_taken = agent.counterfactual_q(share, role, actions)
    expected = torch.empty_like(advantage)
    for focal_agent in range(agents):
        alternatives = []
        for action in range(27):
            alternative = actions.clone()
            alternative[:, focal_agent] = action
            alternatives.append(agent.counterfactual_q(share, role, alternative)[:, focal_agent])
        q_values = torch.stack(alternatives, dim=-1)
        expected[:, focal_agent] = q_taken[:, focal_agent] - (probabilities[:, focal_agent] * q_values).sum(dim=-1)
    assert advantage.shape == (graphs, agents)
    assert torch.isfinite(advantage).all()
    assert torch.allclose(advantage, expected, atol=1e-6, rtol=1e-6)


def test_default_off_keeps_original_update_exact():
    torch.manual_seed(6102)
    left, right = model(False), model(False)
    right.load_state_dict(left.state_dict())
    state = on_policy_batch(left)
    left_optimizer, right_optimizer = make_optimizer(left, cfg(False)), make_optimizer(right, cfg(False))
    np.random.seed(6103)
    update_policy(left, left_optimizer, copy.deepcopy(state), cfg(False), torch.device("cpu"), 1)
    np.random.seed(6103)
    update_policy(right, right_optimizer, copy.deepcopy(state), cfg(False), torch.device("cpu"), 1)
    assert all(torch.equal(a, b) for a, b in zip(left.parameters(), right.parameters()))


def test_enabled_branch_updates_q_critic_and_reports_telemetry():
    torch.manual_seed(6104)
    agent = model(True)
    state = on_policy_batch(agent)
    optimizer = make_optimizer(agent, cfg(True))
    before = [parameter.detach().clone() for parameter in agent.counterfactual_critic.parameters()]
    result = update_policy(agent, optimizer, state, cfg(True), torch.device("cpu"), 1)
    assert result["counterfactual_q_loss"] >= 0.0
    assert result["counterfactual_advantage_std"] > 0.0
    assert result["counterfactual_q_spread"] > 0.0
    assert any(not torch.equal(a, b) for a, b in zip(before, agent.counterfactual_critic.parameters()))


def test_enabled_checkpoint_resume_preserves_the_next_update(tmp_path):
    torch.manual_seed(6105)
    uninterrupted, resumed = model(True), model(True)
    resumed.load_state_dict(uninterrupted.state_dict())
    full_optimizer = make_optimizer(uninterrupted, cfg(True))
    resumed_optimizer = make_optimizer(resumed, cfg(True))
    state = on_policy_batch(uninterrupted)
    full_rng, resumed_rng = np.random.default_rng(6106), np.random.default_rng(6106)

    update_policy(uninterrupted, full_optimizer, copy.deepcopy(state), cfg(True), torch.device("cpu"), 1, full_rng)
    update_policy(uninterrupted, full_optimizer, copy.deepcopy(state), cfg(True), torch.device("cpu"), 2, full_rng)

    update_policy(resumed, resumed_optimizer, copy.deepcopy(state), cfg(True), torch.device("cpu"), 1, resumed_rng)
    checkpoint = tmp_path / "cv_training_state.pt"
    save_training_checkpoint(checkpoint, resumed, resumed_optimizer, 1)
    loaded = model(True)
    # Build the optimizer against the same model that will be restored.
    loaded_optimizer = make_optimizer(loaded, cfg(True))
    load_training_checkpoint(loaded, loaded_optimizer, checkpoint, torch.device("cpu"))
    update_policy(loaded, loaded_optimizer, copy.deepcopy(state), cfg(True), torch.device("cpu"), 2, resumed_rng)

    assert all(torch.equal(a, b) for a, b in zip(uninterrupted.parameters(), loaded.parameters()))
