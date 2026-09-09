import copy

import numpy as np
import torch

from algorithms.active_diagnosis.recurrent_sg_mappo import (
    RecurrentSGMAPPO,
    RecurrentSequenceReplay,
    load_recurrent_training_checkpoint,
    masked_clipped_actor_objective,
    recurrent_training_checkpoint,
    replay_recurrent_sequence,
)


def _batch(time_steps=8, environments=2, agents=3):
    torch.manual_seed(8)
    obs = torch.randn(time_steps, environments, agents, 7)
    share = torch.randn(time_steps, environments, agents, 9)
    roles = torch.tensor([0, 1, 2]).view(1, 1, agents).expand(time_steps, environments, agents)
    adj = torch.ones(time_steps, environments, agents, agents)
    masks = torch.ones(time_steps, environments, agents, 29)
    actions = torch.randint(0, 27, (time_steps, environments, agents))
    starts = torch.zeros(time_steps, environments, dtype=torch.bool)
    if time_steps > 4:
        starts[4, 1] = True
    return obs, share, roles, adj, masks, actions, starts


def test_chronological_replay_is_exact_and_reaches_gru() -> None:
    agent = RecurrentSGMAPPO(7, 9, 29, hidden_dim=16, role_dim=4)
    obs, share, roles, adj, masks, actions, starts = _batch()
    hidden = agent.actor.initial_state(2, 3, device="cpu")
    first = replay_recurrent_sequence(
        agent, obs=obs, share=share, roles=roles, adj=adj, masks=masks,
        sampled_actions=actions, episode_starts=starts, initial_hidden=hidden, bptt_horizon=4,
    )
    second = replay_recurrent_sequence(
        agent, obs=obs, share=share, roles=roles, adj=adj, masks=masks,
        sampled_actions=actions, episode_starts=starts, initial_hidden=hidden, bptt_horizon=4,
    )
    assert torch.equal(first.log_prob, second.log_prob)
    loss = masked_clipped_actor_objective(
        first, first.log_prob.detach(), torch.ones_like(first.log_prob),
        torch.ones_like(first.log_prob), 0.2, 0.01,
    )
    loss.backward()
    assert agent.actor.memory.weight_hh.grad is not None
    assert torch.isfinite(agent.actor.memory.weight_hh.grad).all()


def test_episode_start_resets_only_completed_environment() -> None:
    agent = RecurrentSGMAPPO(7, 9, 29, hidden_dim=12, role_dim=4)
    obs, share, roles, adj, masks, actions, starts = _batch(time_steps=1)
    starts[0, 1] = True
    hidden_a = torch.randn(2, 3, 12)
    hidden_b = hidden_a.clone()
    hidden_b[1] += 100.0
    a = replay_recurrent_sequence(agent, obs=obs, share=share, roles=roles, adj=adj, masks=masks,
        sampled_actions=actions, episode_starts=starts, initial_hidden=hidden_a, bptt_horizon=4)
    b = replay_recurrent_sequence(agent, obs=obs, share=share, roles=roles, adj=adj, masks=masks,
        sampled_actions=actions, episode_starts=starts, initial_hidden=hidden_b, bptt_horizon=4)
    assert torch.equal(a.log_prob[:, 1], b.log_prob[:, 1])
    assert torch.equal(a.final_hidden[:, 0], b.final_hidden[:, 0])


def test_external_gate_samples_have_zero_actor_gradient() -> None:
    log_prob = torch.zeros(1, 1, 3, requires_grad=True)
    replay = RecurrentSequenceReplay(
        logits=torch.zeros(1, 1, 3, 29), log_prob=log_prob,
        entropy=torch.zeros_like(log_prob), values=torch.zeros(1, 1, 3),
        final_hidden=torch.zeros(1, 3, 2),
    )
    loss = masked_clipped_actor_objective(
        replay, torch.zeros_like(log_prob), torch.tensor([[[0.0, 1000.0, 0.0]]]),
        torch.tensor([[[1.0, 0.0, 1.0]]]), 0.2, 0.0,
    )
    loss.backward()
    assert log_prob.grad[0, 0, 1].item() == 0.0


def test_recurrent_checkpoint_restores_model_hidden_and_auxiliary() -> None:
    torch.manual_seed(3); np.random.seed(3)
    agent = RecurrentSGMAPPO(7, 9, 29, hidden_dim=10, role_dim=3)
    optimizer = torch.optim.Adam(agent.parameters(), lr=1e-3)
    hidden = torch.randn(2, 3, 10)
    payload = copy.deepcopy(recurrent_training_checkpoint(agent, optimizer, hidden, update=7, auxiliary={"gate": "state"}))
    restored = RecurrentSGMAPPO(7, 9, 29, hidden_dim=10, role_dim=3)
    restored_optimizer = torch.optim.Adam(restored.parameters(), lr=1e-3)
    update, restored_hidden, auxiliary = load_recurrent_training_checkpoint(payload, restored, restored_optimizer)
    assert update == 7 and auxiliary == {"gate": "state"}
    assert torch.equal(hidden, restored_hidden)
    assert all(torch.equal(a, b) for a, b in zip(agent.state_dict().values(), restored.state_dict().values()))
