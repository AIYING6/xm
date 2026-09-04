from __future__ import annotations

import torch

from algorithms.ri_gmappo.tatg_actor import TATGMemoryActor
from scripts.audit_tatg_mappo_c15_actor_integration import base_actor, collect_checks, synthetic_actor_inputs


def test_c15_actor_integration_audit_passes_all_guards() -> None:
    checks, counts = collect_checks()
    assert all(checks.values())
    assert counts["candidate_added_actor_parameters"] == counts["generic_control_added_actor_parameters"]


def test_zero_memory_wrapper_reproduces_snapshot_logits_exactly() -> None:
    inputs = synthetic_actor_inputs(batch=1)
    actor = base_actor()
    wrapped = TATGMemoryActor(actor, num_blue=3, action_dim=27).eval()
    state = wrapped.reset_memory(inputs["relation_adj"], inputs["edge_feat"])
    with torch.no_grad():
        baseline, _, _ = actor(
            inputs["obs"], inputs["node_feat"], inputs["edge_feat"], inputs["role"], inputs["adj"], inputs["num_agents"],
            relation_adj=inputs["relation_adj"],
        )
        candidate, _, _, _ = wrapped.forward_with_memory(
            inputs["obs"], inputs["node_feat"], inputs["edge_feat"], inputs["role"], inputs["adj"], inputs["num_agents"],
            inputs["relation_adj"], state,
        )
    assert torch.equal(baseline, candidate)
