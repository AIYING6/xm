"""Audit-only TATG actor wrapper with a frozen CETM policy interface.

The wrapper composes an unchanged snapshot :class:`RIActor` and adds the
P1.5/C1 temporal state at the policy-input boundary.  It intentionally does
not alter the legacy actor, centralized critic, environment, sampler or PPO
runner.  Training-loop integration remains out of scope until a later gate.
"""

from __future__ import annotations

import copy
from typing import Type

import torch
import torch.nn as nn

from algorithms.ri_gmappo.simple_ri_gmappo import RIActor
from algorithms.ri_gmappo.tatg_topology_memory import (
    CETMTopologyMemory,
    SnapshotTopologyGRU,
    TopologyMemoryState,
    _TopologyMemoryBase,
)


class TATGMemoryActor(nn.Module):
    """Append a capacity-matched topology-memory state to an unchanged actor.

    ``memory_kind`` is either ``"cetm"`` (the candidate) or
    ``"snapshot_gru"`` (the generic current-snapshot control).  Both variants
    use the same copied snapshot actor and identically shaped temporal head.
    """

    _MEMORY_TYPES: dict[str, Type[_TopologyMemoryBase]] = {
        "cetm": CETMTopologyMemory,
        "snapshot_gru": SnapshotTopologyGRU,
    }

    def __init__(
        self,
        snapshot_actor: RIActor,
        *,
        num_blue: int,
        action_dim: int,
        memory_dim: int | None = None,
        memory_kind: str = "cetm",
        neutral_action: int = 13,
    ):
        super().__init__()
        if memory_kind not in self._MEMORY_TYPES:
            raise ValueError(f"Unsupported memory_kind: {memory_kind}")
        self.snapshot_actor = copy.deepcopy(snapshot_actor)
        original_linear = self.snapshot_actor.policy_head[0]
        original_output = self.snapshot_actor.policy_head[-1]
        if not isinstance(original_linear, nn.Linear) or not isinstance(original_output, nn.Linear):
            raise TypeError("RIActor policy_head must retain its frozen two-linear structure")
        if memory_dim is None:
            # Architecture rule, not a tuned hyperparameter: the transition
            # state has the current actor hidden width and the generic control
            # receives exactly the same added width.
            memory_dim = int(original_linear.out_features)
        self.memory_dim = int(memory_dim)
        self.memory_kind = memory_kind
        self.topology_memory = self._MEMORY_TYPES[memory_kind](
            num_blue=num_blue,
            action_dim=action_dim,
            memory_dim=self.memory_dim,
            neutral_action=neutral_action,
        )
        self.temporal_policy_head = nn.Sequential(
            nn.Linear(original_linear.in_features + self.memory_dim, original_linear.out_features),
            nn.Tanh(),
            nn.Linear(original_output.in_features, original_output.out_features),
        )
        self._initialize_snapshot_equivalent_head(original_linear, original_output)

    def _initialize_snapshot_equivalent_head(self, original_linear: nn.Linear, original_output: nn.Linear) -> None:
        """Preserve the base snapshot policy at a zero memory state exactly."""

        temporal_linear = self.temporal_policy_head[0]
        temporal_output = self.temporal_policy_head[-1]
        assert isinstance(temporal_linear, nn.Linear) and isinstance(temporal_output, nn.Linear)
        with torch.no_grad():
            temporal_linear.weight.zero_()
            temporal_linear.weight[:, : original_linear.in_features].copy_(original_linear.weight)
            temporal_linear.bias.copy_(original_linear.bias)
            temporal_output.weight.copy_(original_output.weight)
            temporal_output.bias.copy_(original_output.bias)

    def reset_memory(self, relation_adj: torch.Tensor, edge_feat: torch.Tensor) -> TopologyMemoryState:
        return self.topology_memory.reset(relation_adj, edge_feat)

    def record_actions(self, state: TopologyMemoryState, actions: torch.Tensor) -> TopologyMemoryState:
        return self.topology_memory.record_actions(state, actions)

    def forward_with_memory(
        self,
        obs: torch.Tensor,
        node_feat: torch.Tensor,
        edge_feat: torch.Tensor,
        role: torch.Tensor,
        adj: torch.Tensor,
        num_agents: int,
        relation_adj: torch.Tensor,
        memory_state: TopologyMemoryState,
        *,
        intent_label: torch.Tensor | None = None,
        detach_intent: bool = False,
        oracle_intent: bool = False,
        return_chain_aux: bool = False,
    ):
        """Compute logits from the existing snapshot features plus frozen memory."""

        captured: dict[str, torch.Tensor] = {}

        def capture_policy_input(_module: nn.Module, inputs: tuple[torch.Tensor, ...]) -> None:
            captured["policy_input"] = inputs[0]

        handle = self.snapshot_actor.policy_head[0].register_forward_pre_hook(capture_policy_input)
        try:
            _, attn, intent_logits, chain_aux_logits = self.snapshot_actor(
                obs,
                node_feat,
                edge_feat,
                role,
                adj,
                num_agents,
                relation_adj=relation_adj,
                intent_label=intent_label,
                detach_intent=detach_intent,
                oracle_intent=oracle_intent,
                return_chain_aux=True,
            )
        finally:
            handle.remove()
        policy_input = captured.get("policy_input")
        if policy_input is None:
            raise RuntimeError("Snapshot actor did not expose its policy-input boundary")
        memory, next_state = self.topology_memory.step(relation_adj, edge_feat, memory_state)
        if memory.shape[:2] != policy_input.shape[:2]:
            raise ValueError("topology memory and snapshot actor have incompatible agent dimensions")
        logits = self.temporal_policy_head(torch.cat((policy_input, memory), dim=-1))
        if return_chain_aux:
            return logits, attn, intent_logits, chain_aux_logits, next_state
        return logits, attn, intent_logits, next_state

    def added_actor_parameter_count(self) -> int:
        """Report only parameters beyond the copied legacy snapshot actor."""

        return sum(parameter.numel() for parameter in self.topology_memory.parameters()) + sum(
            parameter.numel() for parameter in self.temporal_policy_head.parameters()
        )
