from __future__ import annotations

import copy

import numpy as np
import torch

from algorithms.ri_gmappo.drtp_topology_sampler import ALL_GROUPS
from algorithms.ri_gmappo.group_credit_telemetry import summarize_group_credit_assignment
from algorithms.ri_gmappo.simple_ri_gmappo import (
    RIGMAPPOAgent,
    RIGMAPPOConfig,
    make_optimizer,
    update_policy,
)


def fixture() -> tuple[RIGMAPPOAgent, RIGMAPPOConfig, dict, torch.device]:
    torch.manual_seed(1234)
    rng = np.random.default_rng(4321)
    device = torch.device("cpu")
    t_steps, n_envs, num_agents, nodes = len(ALL_GROUPS), 1, 3, 4
    obs_dim, share_dim, node_dim, edge_dim = 9, 7, 6, 5
    agent = RIGMAPPOAgent(
        obs_dim=obs_dim,
        node_feat_dim=node_dim,
        edge_feat_dim=edge_dim,
        share_obs_dim=share_dim,
        action_dim=4,
        num_agents=num_agents,
        num_roles=5,
        hidden_dim=16,
        role_dim=4,
        intent_dim=4,
        graph_encoder="single",
        role_gate_mode="none",
        use_intent_context=False,
    ).to(device)
    agent._role_gate_initial_state = {}
    cfg = RIGMAPPOConfig(
        num_envs=n_envs,
        rollout_steps=t_steps,
        minibatch_graphs=t_steps,
        ppo_epochs=1,
        graph_encoder="single",
        role_gate_mode="none",
        hidden_dim=16,
        role_dim=4,
        intent_dim=4,
        evaluation_enabled=False,
    )
    obs = rng.normal(size=(t_steps, n_envs, num_agents, obs_dim)).astype(np.float32)
    share_obs = rng.normal(size=(t_steps, n_envs, num_agents, share_dim)).astype(np.float32)
    node_feat = rng.normal(size=(t_steps, n_envs, nodes, node_dim)).astype(np.float32)
    edge_feat = rng.normal(size=(t_steps, n_envs, nodes, nodes, edge_dim)).astype(np.float32)
    role = np.tile(np.asarray([0, 1, 2, 4], dtype=np.int64), (t_steps, n_envs, 1))
    adj = np.ones((t_steps, n_envs, nodes, nodes), dtype=np.float32)
    relation_adj = np.repeat(adj[:, :, None, :, :], 3, axis=2)
    intent_label = np.zeros((t_steps, n_envs, 1), dtype=np.int64)
    actions = np.asarray(rng.integers(0, 4, size=(t_steps, n_envs, num_agents)), dtype=np.int64)
    flat = t_steps * n_envs
    with torch.no_grad():
        _, logp, _, values, _, _, _ = agent.get_action_and_value(
            torch.as_tensor(obs.reshape(flat, num_agents, obs_dim)),
            torch.as_tensor(node_feat.reshape(flat, nodes, node_dim)),
            torch.as_tensor(edge_feat.reshape(flat, nodes, nodes, edge_dim)),
            torch.as_tensor(role.reshape(flat, nodes)),
            torch.as_tensor(adj.reshape(flat, nodes, nodes)),
            torch.as_tensor(share_obs.reshape(flat, num_agents, share_dim)),
            relation_adj=torch.as_tensor(relation_adj.reshape(flat, 3, nodes, nodes)),
            action=torch.as_tensor(actions.reshape(flat, num_agents)),
            intent_label=torch.as_tensor(intent_label.reshape(flat, 1)),
        )
    values_np = values.numpy().reshape(t_steps, n_envs, num_agents).astype(np.float32)
    advantages = rng.normal(size=values_np.shape).astype(np.float32)
    returns = values_np + advantages
    batch = {
        "obs": obs,
        "share_obs": share_obs,
        "node_feat": node_feat,
        "edge_feat": edge_feat,
        "role": role,
        "adj": adj,
        "relation_adj": relation_adj,
        "intent_label": intent_label,
        "has_intent_label": False,
        "actions": actions,
        "logp": logp.numpy().reshape(t_steps, n_envs, num_agents).astype(np.float32),
        "values": values_np,
        "advantages": advantages,
        "returns": returns.astype(np.float32),
        "td_residuals": (advantages * 0.75).astype(np.float32),
        "rewards": rng.normal(size=values_np.shape).astype(np.float32),
        "dones": np.zeros_like(values_np, dtype=np.float32),
        "condition_is_nominal": np.asarray([[group == "N"] for group in ALL_GROUPS], dtype=bool),
        "condition_group": np.asarray([[group] for group in ALL_GROUPS], dtype="<U3"),
    }
    return agent, cfg, batch, device


def test_group_schema_counts_and_pairwise_conflicts() -> None:
    agent, cfg, batch, device = fixture()
    rows, conflicts = summarize_group_credit_assignment(agent, batch, cfg, device, update=17)
    assert [row["group"] for row in rows] == list(ALL_GROUPS)
    assert all(row["status"] == "OK" and row["graph_count"] == 1 for row in rows)
    assert len(conflicts) == len(ALL_GROUPS) * (len(ALL_GROUPS) - 1) // 2
    assert all(-1.0000001 <= row["actor_gradient_cosine"] <= 1.0000001 for row in conflicts)
    assert all(-1.0000001 <= row["critic_gradient_cosine"] <= 1.0000001 for row in conflicts)
    assert all(row["independent_unit"] == "training_seed" for row in rows + conflicts)


def test_no_sample_group_is_explicit_not_nan() -> None:
    agent, cfg, batch, device = fixture()
    batch["condition_group"][:] = "N"
    batch["condition_is_nominal"][:] = True
    rows, conflicts = summarize_group_credit_assignment(agent, batch, cfg, device, update=1)
    absent = [row for row in rows if row["group"] != "N"]
    assert all(row["status"] == "NO_SAMPLES" and row["graph_count"] == 0 for row in absent)
    assert all(row["value_residual_mean"] is None for row in absent)
    assert conflicts == []


def test_telemetry_is_deterministic_and_does_not_mutate_model_grad_or_rng() -> None:
    agent, cfg, batch, device = fixture()
    state_before = {name: value.detach().clone() for name, value in agent.state_dict().items()}
    torch_rng_before = torch.get_rng_state().clone()
    numpy_rng_before = copy.deepcopy(np.random.get_state())
    rows_a, conflicts_a = summarize_group_credit_assignment(agent, batch, cfg, device, update=3)
    rows_b, conflicts_b = summarize_group_credit_assignment(agent, batch, cfg, device, update=3)
    assert rows_a == rows_b
    assert conflicts_a == conflicts_b
    assert torch.equal(torch_rng_before, torch.get_rng_state())
    after_numpy = np.random.get_state()
    assert numpy_rng_before[0] == after_numpy[0]
    assert np.array_equal(numpy_rng_before[1], after_numpy[1])
    assert numpy_rng_before[2:] == after_numpy[2:]
    assert all(torch.equal(state_before[name], value) for name, value in agent.state_dict().items())
    assert all(parameter.grad is None for parameter in agent.parameters())


def test_telemetry_on_off_produces_identical_ppo_update() -> None:
    base, cfg, batch, device = fixture()
    plain = copy.deepcopy(base)
    logged = copy.deepcopy(base)
    plain_optimizer = make_optimizer(plain, cfg)
    logged_optimizer = make_optimizer(logged, cfg)
    summarize_group_credit_assignment(logged, batch, cfg, device, update=1)
    plain_info = update_policy(
        plain, plain_optimizer, copy.deepcopy(batch), cfg, device, 1,
        minibatch_rng=np.random.default_rng(99),
    )
    logged_info = update_policy(
        logged, logged_optimizer, copy.deepcopy(batch), cfg, device, 1,
        minibatch_rng=np.random.default_rng(99),
    )
    assert plain_info == logged_info
    assert all(
        torch.equal(plain.state_dict()[name], logged.state_dict()[name])
        for name in plain.state_dict()
    )
