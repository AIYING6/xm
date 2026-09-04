"""Chronological actor replay for the frozen TATG sequence-PPO contract.

This module intentionally contains no environment creation, sampler, critic
loss or optimizer ownership.  It is a reusable actor-side sequence replay used
by C3 to verify that a recurrent policy can reconstruct its legal state from a
stored rollout-start payload and the rollout's graph/action/done tensors.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch.distributions import Categorical

from algorithms.ri_gmappo.tatg_actor import TATGMemoryActor
from algorithms.ri_gmappo.tatg_topology_memory import TopologyMemoryState


@dataclass(frozen=True)
class TATGSequenceReplay:
    logits: torch.Tensor
    log_prob: torch.Tensor
    entropy: torch.Tensor
    states_before: tuple[TopologyMemoryState, ...]
    final_state: TopologyMemoryState


def _select_reset_slots(
    actor: TATGMemoryActor,
    state: TopologyMemoryState,
    completed: torch.Tensor,
    relation_adj: torch.Tensor,
    edge_feat: torch.Tensor,
) -> TopologyMemoryState:
    mask = completed.to(dtype=torch.bool, device=state.memory.device)
    if mask.ndim != 1 or mask.shape[0] != state.memory.shape[0]:
        raise ValueError("completed must have shape [environment]")
    reset_state = actor.reset_memory(relation_adj, edge_feat)
    memory_mask, action_mask = mask[:, None, None], mask[:, None]
    return TopologyMemoryState(
        memory=torch.where(memory_mask, reset_state.memory, state.memory),
        previous_topology=torch.where(memory_mask, reset_state.previous_topology, state.previous_topology),
        previous_action=torch.where(action_mask, reset_state.previous_action, state.previous_action),
    )


def replay_tatg_actor_sequence(
    actor: TATGMemoryActor,
    *,
    obs: torch.Tensor,
    node_feat: torch.Tensor,
    edge_feat: torch.Tensor,
    role: torch.Tensor,
    adj: torch.Tensor,
    relation_adj: torch.Tensor,
    actions: torch.Tensor,
    dones: torch.Tensor,
    state_before_rollout: TopologyMemoryState,
) -> TATGSequenceReplay:
    """Replay every vectorized rollout sequence chronologically.

    All tensors have leading ``[time, environment]`` axes.  The state is reset
    after a stored terminal transition and before the following graph row.
    """

    if obs.ndim != 4 or actions.ndim != 3 or dones.ndim != 2:
        raise ValueError("expected obs [time, environment, agent, feature], actions [time, environment, agent], dones [time, environment]")
    time_steps, environments, agents = actions.shape
    if tuple(obs.shape[:3]) != (time_steps, environments, agents):
        raise ValueError("obs and action leading dimensions must agree")
    if tuple(dones.shape) != (time_steps, environments):
        raise ValueError("done dimensions must match the rollout time/environment axes")
    if state_before_rollout.memory.shape[0] != environments:
        raise ValueError("rollout-start TATG state has an incompatible environment count")
    if state_before_rollout.memory.shape[1] != agents:
        raise ValueError("rollout-start TATG state has an incompatible agent count")

    state = state_before_rollout
    logits_rows, log_prob_rows, entropy_rows, states_before = [], [], [], []
    for t in range(time_steps):
        states_before.append(state)
        logits, _, _, next_state = actor.forward_with_memory(
            obs[t], node_feat[t], edge_feat[t], role[t], adj[t], agents, relation_adj[t], state
        )
        distribution = Categorical(logits=logits)
        chosen_actions = actions[t].long()
        logits_rows.append(logits)
        log_prob_rows.append(distribution.log_prob(chosen_actions))
        entropy_rows.append(distribution.entropy())
        state = actor.record_actions(next_state, chosen_actions)
        if t + 1 < time_steps:
            state = _select_reset_slots(actor, state, dones[t], relation_adj[t + 1], edge_feat[t + 1])
    return TATGSequenceReplay(
        logits=torch.stack(logits_rows),
        log_prob=torch.stack(log_prob_rows),
        entropy=torch.stack(entropy_rows),
        states_before=tuple(states_before),
        final_state=state,
    )


def clipped_actor_objective(
    replay: TATGSequenceReplay,
    old_log_prob: torch.Tensor,
    advantages: torch.Tensor,
    clip_coef: float,
    entropy_coef: float,
) -> torch.Tensor:
    """Ordinary clipped PPO actor objective over the untouched sequence axes."""

    if replay.log_prob.shape != old_log_prob.shape or replay.log_prob.shape != advantages.shape:
        raise ValueError("old_log_prob and advantages must match chronological replay shape")
    ratio = (replay.log_prob - old_log_prob).exp()
    unclipped = -advantages * ratio
    clipped = -advantages * torch.clamp(ratio, 1.0 - clip_coef, 1.0 + clip_coef)
    return torch.maximum(unclipped, clipped).mean() - entropy_coef * replay.entropy.mean()
