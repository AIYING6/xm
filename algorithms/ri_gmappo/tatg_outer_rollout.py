"""Isolated UTR-only outer rollout and runtime checkpoint path for TATG.

This module reuses the existing 3D environment, graph stacking convention and
centralized critic while keeping TATG's temporal actor lifecycle separate from
the frozen snapshot runner.  It is intentionally limited to collection and
strict continuation.  PPO updates and evaluation remain outside its scope.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOAgent, stack_graphs
from algorithms.ri_gmappo.tatg_actor import TATGMemoryActor
from algorithms.ri_gmappo.tatg_sequence_runner import TATGSequenceActorRunner


TATG_OUTER_RUNTIME_FORMAT = "tatg_outer_rollout_runtime_v1"


class TATGActorCriticSystem(nn.Module):
    """A temporal actor paired with an architecturally unchanged critic."""

    def __init__(self, snapshot: RIGMAPPOAgent, *, memory_kind: str):
        super().__init__()
        self.num_agents = int(snapshot.num_agents)
        self.num_roles = int(snapshot.num_roles)
        self.temporal_actor = TATGMemoryActor(
            snapshot.actor,
            num_blue=self.num_agents,
            action_dim=snapshot.action_dim,
            memory_kind=memory_kind,
        )
        self.critic = copy.deepcopy(snapshot.critic)

    def critic_value(self, share_obs: torch.Tensor, role: torch.Tensor) -> torch.Tensor:
        agent_role = role[:, : self.num_agents].long().clamp(min=0, max=self.num_roles - 1)
        role_one_hot = F.one_hot(agent_role, num_classes=self.num_roles).to(
            dtype=share_obs.dtype, device=share_obs.device
        )
        return self.critic(torch.cat([share_obs, role_one_hot], dim=-1)).squeeze(-1)

    def trainable_parameters(self):
        """Exclude only the copied, inactive legacy policy head.

        The old head is retained by the audit wrapper solely to capture the
        legacy policy-input boundary.  CETM's replacement policy head and the
        entire snapshot actor body remain trainable, as does the unchanged
        centralized critic.
        """

        for name, parameter in self.temporal_actor.named_parameters():
            if not name.startswith("snapshot_actor.policy_head."):
                yield parameter
        yield from self.critic.parameters()


def make_tatg_optimizer(system: TATGActorCriticSystem, lr: float) -> optim.Optimizer:
    """Construct the ordinary Adam optimizer over the legal TATG parameters."""

    return optim.Adam(list(system.trainable_parameters()), lr=float(lr))


def collect_tatg_utr_rollout(
    system: TATGActorCriticSystem,
    runner: TATGSequenceActorRunner,
    envs: Sequence[Any],
    obs: np.ndarray,
    share_obs: np.ndarray,
    graph_obs: dict[str, np.ndarray],
    *,
    rollout_steps: int,
    device: torch.device,
    action_generator: torch.Generator | None,
) -> dict[str, Any]:
    """Collect one fixed-UTR rollout without PPO updates or evaluation.

    Every environment starts from its already provided state.  Finished
    episodes are reset immediately, and only their corresponding CETM state is
    reset from the newly returned legal graph.
    """

    if rollout_steps <= 0:
        raise ValueError("rollout_steps must be positive")
    start_state = runner.rollout_start_state_dict()
    obs_rows, share_rows, node_rows, edge_rows, role_rows, adj_rows, relation_rows = [], [], [], [], [], [], []
    action_rows, logp_rows, value_rows, reward_rows, done_rows, state_rows = [], [], [], [], [], []
    for _ in range(rollout_steps):
        obs_t = torch.as_tensor(obs, dtype=torch.float32, device=device)
        node_t = torch.as_tensor(graph_obs["node_feat"], dtype=torch.float32, device=device)
        edge_t = torch.as_tensor(graph_obs["edge_feat"], dtype=torch.float32, device=device)
        role_t = torch.as_tensor(graph_obs["role"], dtype=torch.long, device=device)
        adj_t = torch.as_tensor(graph_obs["adj"], dtype=torch.float32, device=device)
        relation_t = torch.as_tensor(graph_obs["relation_adj"], dtype=torch.float32, device=device)
        share_t = torch.as_tensor(share_obs, dtype=torch.float32, device=device)
        with torch.no_grad():
            actor_step = runner.act(
                obs_t, node_t, edge_t, role_t, adj_t, relation_t, action_generator=action_generator
            )
            values = system.critic_value(share_t, role_t)

        next_obs, next_share, next_graphs, rewards, completed = [], [], [], [], []
        for env_index, env in enumerate(envs):
            next_o, next_s, next_g, reward, done, _ = env.step(actor_step.actions[env_index].cpu().numpy())
            is_completed = bool(np.all(done))
            if is_completed:
                next_o, next_s, next_g = env.reset()
            next_obs.append(next_o)
            next_share.append(next_s)
            next_graphs.append(next_g)
            rewards.append(reward[:, 0])
            completed.append(is_completed)

        obs_rows.append(obs.copy())
        share_rows.append(share_obs.copy())
        node_rows.append(graph_obs["node_feat"].copy())
        edge_rows.append(graph_obs["edge_feat"].copy())
        role_rows.append(graph_obs["role"].copy())
        adj_rows.append(graph_obs["adj"].copy())
        relation_rows.append(graph_obs["relation_adj"].copy())
        action_rows.append(actor_step.actions.cpu().numpy().copy())
        logp_rows.append(actor_step.log_prob.cpu().numpy().copy())
        value_rows.append(values.cpu().numpy().copy())
        reward_rows.append(np.asarray(rewards, dtype=np.float32))
        done_rows.append(np.asarray(completed, dtype=bool))

        obs, share_obs, graph_obs = np.stack(next_obs), np.stack(next_share), stack_graphs(next_graphs)
        runner.reset_completed(
            torch.as_tensor(completed, dtype=torch.bool, device=device),
            torch.as_tensor(graph_obs["relation_adj"], dtype=torch.float32, device=device),
            torch.as_tensor(graph_obs["edge_feat"], dtype=torch.float32, device=device),
        )
        state_rows.append(runner.rollout_start_state_dict())

    return {
        "obs": np.asarray(obs_rows, dtype=np.float32),
        "share_obs": np.asarray(share_rows, dtype=np.float32),
        "node_feat": np.asarray(node_rows, dtype=np.float32),
        "edge_feat": np.asarray(edge_rows, dtype=np.float32),
        "role": np.asarray(role_rows, dtype=np.int64),
        "adj": np.asarray(adj_rows, dtype=np.float32),
        "relation_adj": np.asarray(relation_rows, dtype=np.float32),
        "actions": np.asarray(action_rows, dtype=np.int64),
        "logp": np.asarray(logp_rows, dtype=np.float32),
        "values": np.asarray(value_rows, dtype=np.float32),
        "rewards": np.asarray(reward_rows, dtype=np.float32),
        "dones": np.asarray(done_rows, dtype=bool),
        "tatg_state_before_rollout": start_state,
        "tatg_state_after_transition": state_rows,
        "next_obs": obs,
        "next_share_obs": share_obs,
        "next_graph_obs": graph_obs,
    }


def save_tatg_outer_runtime_checkpoint(
    path: str | Path,
    system: TATGActorCriticSystem,
    optimizer: optim.Optimizer,
    runner: TATGSequenceActorRunner,
    envs: Sequence[Any],
    obs: np.ndarray,
    share_obs: np.ndarray,
    graph_obs: dict[str, np.ndarray],
    action_generator: torch.Generator,
) -> None:
    """Persist all mutable state needed for strict TATG collection continuation."""

    states = []
    for env in envs:
        getter = getattr(env, "runtime_state_dict", None)
        if getter is None:
            raise TypeError(f"{type(env).__name__} lacks strict runtime-state persistence")
        states.append(getter())
    torch.save(
        {
            "format": TATG_OUTER_RUNTIME_FORMAT,
            "system_state": system.state_dict(),
            "optimizer_state": optimizer.state_dict(),
            "tatg_actor_runtime_state": runner.rollout_start_state_dict(),
            "environment_states": states,
            "obs": copy.deepcopy(obs),
            "share_obs": copy.deepcopy(share_obs),
            "graph_obs": copy.deepcopy(graph_obs),
            "action_generator_state": action_generator.get_state(),
        },
        path,
    )


def load_tatg_outer_runtime_checkpoint(
    path: str | Path,
    system: TATGActorCriticSystem,
    optimizer: optim.Optimizer,
    runner: TATGSequenceActorRunner,
    envs: Sequence[Any],
    action_generator: torch.Generator,
) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray]]:
    """Restore a strict TATG collection state without an outcome-dependent choice."""

    payload = torch.load(path, map_location="cpu", weights_only=False)
    if not isinstance(payload, dict) or payload.get("format") != TATG_OUTER_RUNTIME_FORMAT:
        raise ValueError("unsupported TATG outer runtime checkpoint")
    required = {
        "system_state", "optimizer_state", "tatg_actor_runtime_state", "environment_states",
        "obs", "share_obs", "graph_obs", "action_generator_state",
    }
    missing = required.difference(payload)
    if missing:
        raise ValueError(f"incomplete TATG outer runtime checkpoint: {sorted(missing)}")
    if len(envs) != len(payload["environment_states"]):
        raise ValueError("environment count does not match TATG runtime checkpoint")
    system.load_state_dict(payload["system_state"], strict=True)
    optimizer.load_state_dict(payload["optimizer_state"])
    for env, environment_state in zip(envs, payload["environment_states"]):
        loader = getattr(env, "load_runtime_state_dict", None)
        if loader is None:
            raise TypeError(f"{type(env).__name__} lacks strict runtime-state restoration")
        loader(environment_state)
    runner.load_rollout_start_state_dict(payload["tatg_actor_runtime_state"])
    action_generator.set_state(payload["action_generator_state"])
    return copy.deepcopy(payload["obs"]), copy.deepcopy(payload["share_obs"]), copy.deepcopy(payload["graph_obs"])
