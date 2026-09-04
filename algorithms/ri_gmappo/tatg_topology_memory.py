"""Frozen C1 implementation of TATG's causal event-triggered topology memory.

This module is deliberately separate from :mod:`simple_ri_gmappo`.  It gives
the C1 audit a concrete, serializable implementation of the P1.5 formula
without changing the legacy actor, centralized critic, environment, sampler,
or PPO loop.  Wiring it into a policy is a later, separately authorized step.

The local topology vector follows the existing graph convention
``relation_adj[relation, receiver, sender]`` and contains only the receiver's
blue-to-blue communication row, task-support row, and message-age row.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn as nn
import torch.nn.functional as F

from envs import RELATION_COMMUNICATION, RELATION_TASK_SUPPORT


# This is the established message-age channel in the 3DOF graph edge feature.
EDGE_MESSAGE_AGE_INDEX = 15


@dataclass(frozen=True)
class TopologyMemoryState:
    """Per-rollout-environment actor state required by the frozen contract."""

    memory: torch.Tensor
    previous_topology: torch.Tensor
    previous_action: torch.Tensor

    def runtime_state_dict(self) -> dict[str, torch.Tensor]:
        """Return cloned tensors suitable for an exact runtime checkpoint."""

        return {
            "memory": self.memory.detach().clone(),
            "previous_topology": self.previous_topology.detach().clone(),
            "previous_action": self.previous_action.detach().clone(),
        }

    @classmethod
    def from_runtime_state_dict(cls, payload: dict[str, torch.Tensor]) -> "TopologyMemoryState":
        required = {"memory", "previous_topology", "previous_action"}
        missing = required.difference(payload)
        if missing:
            raise KeyError(f"Missing topology-memory runtime fields: {sorted(missing)}")
        return cls(
            memory=payload["memory"].detach().clone(),
            previous_topology=payload["previous_topology"].detach().clone(),
            previous_action=payload["previous_action"].detach().clone(),
        )


class _TopologyMemoryBase(nn.Module):
    """Shared capacity-matched implementation machinery for the C1 controls."""

    def __init__(self, num_blue: int, action_dim: int, memory_dim: int, neutral_action: int = 13):
        super().__init__()
        if num_blue <= 0 or action_dim <= 0 or memory_dim <= 0:
            raise ValueError("num_blue, action_dim and memory_dim must be positive")
        if not 0 <= neutral_action < action_dim:
            raise ValueError("neutral_action must be a valid actor action index")
        self.num_blue = int(num_blue)
        self.action_dim = int(action_dim)
        self.memory_dim = int(memory_dim)
        self.neutral_action = int(neutral_action)
        self.topology_dim = 3 * self.num_blue
        self.cell = nn.GRUCell(self.topology_dim + self.action_dim, self.memory_dim)

    def extract_local_topology(self, relation_adj: torch.Tensor, edge_feat: torch.Tensor) -> torch.Tensor:
        """Extract ``x_i,t`` for each blue actor from its own receiver row only."""

        if relation_adj.ndim != 4:
            raise ValueError("relation_adj must have shape [batch, relation, receiver, sender]")
        if edge_feat.ndim != 4:
            raise ValueError("edge_feat must have shape [batch, receiver, sender, feature]")
        if relation_adj.shape[0] != edge_feat.shape[0] or relation_adj.shape[2] != edge_feat.shape[1]:
            raise ValueError("relation_adj and edge_feat graph dimensions must agree")
        if relation_adj.shape[1] <= max(RELATION_COMMUNICATION, RELATION_TASK_SUPPORT):
            raise ValueError("relation_adj does not contain the frozen topology relations")
        if edge_feat.shape[-1] <= EDGE_MESSAGE_AGE_INDEX:
            raise ValueError("edge_feat does not contain the frozen message-age channel")
        if relation_adj.shape[2] < self.num_blue or relation_adj.shape[3] < self.num_blue:
            raise ValueError("graph does not contain the configured blue-agent block")

        comm = relation_adj[:, RELATION_COMMUNICATION, : self.num_blue, : self.num_blue]
        support = relation_adj[:, RELATION_TASK_SUPPORT, : self.num_blue, : self.num_blue]
        age = edge_feat[:, : self.num_blue, : self.num_blue, EDGE_MESSAGE_AGE_INDEX]
        return torch.cat((comm, support, age), dim=-1)

    def initial_state(
        self, batch_size: int, *, device: torch.device | str, dtype: torch.dtype = torch.float32
    ) -> TopologyMemoryState:
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        memory = torch.zeros(batch_size, self.num_blue, self.memory_dim, device=device, dtype=dtype)
        topology = torch.zeros(batch_size, self.num_blue, self.topology_dim, device=device, dtype=dtype)
        actions = torch.full(
            (batch_size, self.num_blue), self.neutral_action, device=device, dtype=torch.long
        )
        return TopologyMemoryState(memory=memory, previous_topology=topology, previous_action=actions)

    def reset(self, relation_adj: torch.Tensor, edge_feat: torch.Tensor) -> TopologyMemoryState:
        """Reset the frozen state using the legal topology visible at reset.

        In particular, ``previous_topology`` is ``x_i,reset`` rather than a
        synthetic all-zero vector.  Thus a graph that has not changed after
        reset produces the exact zero-residual identity required by P1.5.
        """

        topology = self.extract_local_topology(relation_adj, edge_feat)
        return TopologyMemoryState(
            memory=torch.zeros(
                topology.shape[0], self.num_blue, self.memory_dim, device=topology.device, dtype=topology.dtype
            ),
            previous_topology=topology.detach().clone(),
            previous_action=torch.full(
                (topology.shape[0], self.num_blue), self.neutral_action, device=topology.device, dtype=torch.long
            ),
        )

    def _proposal(self, signal: torch.Tensor, state: TopologyMemoryState) -> torch.Tensor:
        previous_action = state.previous_action.long().clamp(min=0, max=self.action_dim - 1)
        action_one_hot = F.one_hot(previous_action, num_classes=self.action_dim).to(dtype=signal.dtype)
        cell_input = torch.cat((signal, action_one_hot), dim=-1)
        return self.cell(
            cell_input.reshape(-1, cell_input.shape[-1]),
            state.memory.reshape(-1, state.memory.shape[-1]),
        ).reshape_as(state.memory)

    def record_actions(self, state: TopologyMemoryState, actions: torch.Tensor) -> TopologyMemoryState:
        """Advance only ``a_i,t-1`` after the caller has sampled an actor action."""

        if tuple(actions.shape) != tuple(state.previous_action.shape):
            raise ValueError("actions must have shape [batch, num_blue]")
        return TopologyMemoryState(
            memory=state.memory,
            previous_topology=state.previous_topology,
            previous_action=actions.detach().clone().long(),
        )


class CETMTopologyMemory(_TopologyMemoryBase):
    """P1.5's causal event-triggered topology memory (CETM)."""

    def step(
        self, relation_adj: torch.Tensor, edge_feat: torch.Tensor, state: TopologyMemoryState
    ) -> tuple[torch.Tensor, TopologyMemoryState]:
        current = self.extract_local_topology(relation_adj, edge_feat)
        if current.shape != state.previous_topology.shape:
            raise ValueError("runtime state is incompatible with the current local topology shape")
        delta = current - state.previous_topology
        gate = 1.0 - torch.exp(-delta.abs().mean(dim=-1, keepdim=True))
        proposal = self._proposal(delta, state)
        memory = (1.0 - gate) * state.memory + gate * proposal
        return memory, TopologyMemoryState(memory, current, state.previous_action)


class ZeroResidualCETMTopologyMemory(CETMTopologyMemory):
    """P1.5's parameter-matched CETM ablation with transition residual removed."""

    def step(
        self, relation_adj: torch.Tensor, edge_feat: torch.Tensor, state: TopologyMemoryState
    ) -> tuple[torch.Tensor, TopologyMemoryState]:
        current = self.extract_local_topology(relation_adj, edge_feat)
        if current.shape != state.previous_topology.shape:
            raise ValueError("runtime state is incompatible with the current local topology shape")
        delta = torch.zeros_like(current)
        gate = 1.0 - torch.exp(-delta.abs().mean(dim=-1, keepdim=True))
        proposal = self._proposal(delta, state)
        memory = (1.0 - gate) * state.memory + gate * proposal
        return memory, TopologyMemoryState(memory, current, state.previous_action)


class SnapshotTopologyGRU(_TopologyMemoryBase):
    """Capacity-matched generic current-snapshot GNN+GRU control.

    It intentionally uses the same GRUCell dimensions as CETM but consumes the
    current local topology vector and updates at every step.
    """

    def step(
        self, relation_adj: torch.Tensor, edge_feat: torch.Tensor, state: TopologyMemoryState
    ) -> tuple[torch.Tensor, TopologyMemoryState]:
        current = self.extract_local_topology(relation_adj, edge_feat)
        if current.shape != state.previous_topology.shape:
            raise ValueError("runtime state is incompatible with the current local topology shape")
        memory = self._proposal(current, state)
        return memory, TopologyMemoryState(memory, current, state.previous_action)
