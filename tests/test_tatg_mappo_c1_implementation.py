from __future__ import annotations

import torch

from algorithms.ri_gmappo.tatg_topology_memory import CETMTopologyMemory, SnapshotTopologyGRU, TopologyMemoryState
from scripts.audit_tatg_mappo_c1_implementation import _legal_graph, collect_checks


def test_c1_implementation_audit_passes_all_frozen_guards() -> None:
    checks, counts = collect_checks()
    assert all(checks.values())
    assert counts["cetm_added_parameters"] == counts["generic_added_parameters"]


def test_cetm_zero_residual_keeps_memory_bit_exact() -> None:
    module = CETMTopologyMemory(num_blue=3, action_dim=27, memory_dim=5)
    relations, edge = _legal_graph(1, 3, changed=False)
    state = module.reset(relations, edge)
    memory, second = module.step(relations, edge, state)
    assert torch.equal(memory, state.memory)
    assert torch.equal(second.memory, state.memory)


def test_runtime_state_round_trip_is_exact() -> None:
    module = CETMTopologyMemory(num_blue=3, action_dim=27, memory_dim=5)
    relations, edge = _legal_graph(1, 3, changed=True)
    state = module.reset(relations, edge)
    _, state = module.step(relations, edge, state)
    state = module.record_actions(state, torch.tensor([[3, 4, 5]]))
    restored = TopologyMemoryState.from_runtime_state_dict(state.runtime_state_dict())
    assert torch.equal(restored.memory, state.memory)
    assert torch.equal(restored.previous_topology, state.previous_topology)
    assert torch.equal(restored.previous_action, state.previous_action)


def test_generic_control_has_equal_added_capacity() -> None:
    cetm = CETMTopologyMemory(num_blue=3, action_dim=27, memory_dim=5)
    generic = SnapshotTopologyGRU(num_blue=3, action_dim=27, memory_dim=5)
    assert sum(p.numel() for p in cetm.parameters()) == sum(p.numel() for p in generic.parameters())
