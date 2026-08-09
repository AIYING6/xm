"""D0 static tests for the v1.9 PCRF candidate; no training is performed."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import (  # noqa: E402
    ProvenanceConditionedRelationFactorEncoder,
    RIActor,
)
from envs import RELATION_COMMUNICATION  # noqa: E402
from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv  # noqa: E402


def make_env(**overrides) -> UAVIntercept3DEnv:
    return UAVIntercept3DEnv(UAVIntercept3DConfig(
        seed=41,
        strict_target_sensing=True,
        agent_target_info_bottleneck=True,
        node_failure_start_step=40,
        node_failure_duration_steps=80,
        **overrides,
    ))


def make_encoder() -> ProvenanceConditionedRelationFactorEncoder:
    torch.manual_seed(7)
    return ProvenanceConditionedRelationFactorEncoder(hidden_dim=12, edge_dim=18)


def agreement_relation() -> tuple[torch.Tensor, torch.Tensor]:
    relation = torch.zeros(1, 3, 4, 4)
    relation[:, :, 0, 1] = 1.0
    edge = torch.zeros(1, 4, 4, 18)
    edge[:, 0, 1, 16] = 1.0
    return relation, edge


def test_agreement_has_neutral_gate() -> None:
    encoder = make_encoder()
    relation, edge = agreement_relation()
    gate, diagnostics = encoder.fusion_gate(relation, edge)
    assert torch.allclose(gate, torch.full_like(gate, 1.0 / 3.0), atol=1e-6)
    assert torch.allclose(diagnostics["pairwise_disagreement"], torch.zeros_like(diagnostics["pairwise_disagreement"]))


def test_conflict_changes_gate_using_legal_fields_only() -> None:
    encoder = make_encoder()
    relation, edge = agreement_relation()
    agreement_gate, _ = encoder.fusion_gate(relation, edge)
    conflict = torch.zeros_like(relation)
    conflict[:, RELATION_COMMUNICATION, 0, 1] = 1.0
    fresh_gate, diagnostics = encoder.fusion_gate(conflict, edge)
    stale_edge = edge.clone()
    stale_edge[:, 0, 1, 15] = 0.9
    stale_gate, _ = encoder.fusion_gate(conflict, stale_edge)
    assert not torch.allclose(fresh_gate, agreement_gate)
    assert fresh_gate[0, RELATION_COMMUNICATION] == fresh_gate.max()
    assert stale_gate[0, RELATION_COMMUNICATION] < fresh_gate[0, RELATION_COMMUNICATION]
    assert diagnostics["pairwise_disagreement"].amax() > 0.0


def test_conflict_gate_receives_gradient() -> None:
    encoder = make_encoder()
    relation, edge = agreement_relation()
    relation[:, 0, 0, 2] = 1.0
    x = torch.randn(1, 4, 12, requires_grad=True)
    output, _, _ = encoder(x, relation, edge)
    output.square().mean().backward()
    gradient = encoder.gate_correction[-1].weight.grad
    assert gradient is not None and float(gradient.norm()) > 0.0


def test_pcrf_does_not_restore_unavailable_teammate_truth() -> None:
    torch.manual_seed(11)
    env = make_env(communication_dropout_prob=1.0)
    obs, share_obs, graph = env.reset()
    actor = RIActor(
        obs_dim=obs.shape[-1],
        node_feat_dim=graph["node_feat"].shape[-1],
        edge_feat_dim=graph["edge_feat"].shape[-1],
        num_roles=5, role_dim=4, intent_dim=4, hidden_dim=16,
        action_dim=env.action_dim, graph_encoder="pcrf", use_intent_context=False,
    ).eval()
    inputs = (
        torch.tensor(obs[None, 0:1], dtype=torch.float32),
        torch.tensor(graph["node_feat"][None, 0], dtype=torch.float32),
        torch.tensor(graph["edge_feat"][None, 0], dtype=torch.float32),
        torch.tensor(graph["role"][None, 0], dtype=torch.long),
        torch.tensor(graph["adj"][None, 0], dtype=torch.float32),
    )
    relation = torch.tensor(graph["relation_adj"][None, 0], dtype=torch.float32)
    before = actor(*inputs, 1, relation_adj=relation)[0]
    env.blue_pos[1] += np.asarray([900.0, 0.0, 0.0], dtype=np.float32)
    after_graph = env._get_graph_obs()
    assert np.array_equal(graph["node_feat"][0], after_graph["node_feat"][0])
    after_inputs = (inputs[0], torch.tensor(after_graph["node_feat"][None, 0]),
                    torch.tensor(after_graph["edge_feat"][None, 0]), inputs[3],
                    torch.tensor(after_graph["adj"][None, 0]))
    after_relation = torch.tensor(after_graph["relation_adj"][None, 0], dtype=torch.float32)
    after = actor(*after_inputs, 1, relation_adj=after_relation)[0]
    assert torch.equal(before, after)
    # share_obs is deliberately not an actor argument and cannot affect PCRF.
    assert share_obs.shape[0] == env.config.num_blue


def count_parameters(module: torch.nn.Module) -> int:
    return sum(parameter.numel() for parameter in module.parameters())


def test_single_graph_capacity_can_be_matched() -> None:
    env = make_env()
    obs, _, graph = env.reset()
    common = dict(
        obs_dim=obs.shape[-1], node_feat_dim=graph["node_feat"].shape[-1],
        edge_feat_dim=graph["edge_feat"].shape[-1], num_roles=5, role_dim=8,
        intent_dim=8, action_dim=env.action_dim, use_intent_context=False,
    )
    pcrf_parameters = count_parameters(RIActor(hidden_dim=128, graph_encoder="pcrf", **common))
    candidates = []
    for hidden_dim in range(64, 385):
        count = count_parameters(RIActor(hidden_dim=hidden_dim, graph_encoder="single", **common))
        candidates.append((abs(count - pcrf_parameters), hidden_dim, count))
    _, matched_hidden_dim, matched_parameters = min(candidates)
    relative_gap = abs(matched_parameters - pcrf_parameters) / pcrf_parameters
    assert relative_gap <= 0.03
    print(
        f"CAPACITY_AUDIT pcrf_hidden=128 pcrf_params={pcrf_parameters} "
        f"single_hidden={matched_hidden_dim} single_params={matched_parameters} relative_gap={relative_gap:.4f}"
    )


def main() -> None:
    tests = [
        test_agreement_has_neutral_gate,
        test_conflict_changes_gate_using_legal_fields_only,
        test_conflict_gate_receives_gradient,
        test_pcrf_does_not_restore_unavailable_teammate_truth,
        test_single_graph_capacity_can_be_matched,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"PCRF_D0_STATIC_TEST_REPORT_V1_9: PASS ({len(tests)} tests)")


if __name__ == "__main__":
    main()
