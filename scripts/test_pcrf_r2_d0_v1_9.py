"""D0-R2 deterministic integrity tests; no training or evaluation is performed."""
from __future__ import annotations

import copy
import hashlib
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import (  # noqa: E402
    RIActor,
    RIGMAPPOAgent,
    RIGMAPPOConfig,
    TwoSourcePCRFR2Encoder,
    effective_chain_aux_coef,
    pcrf_r2_tensors,
    stack_graphs,
)
from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv  # noqa: E402


def source_tensors(
    *, p_available: bool = True, c_available: bool = True,
    p_value: float = 0.25, c_value: float = 0.25,
    age: float = 0.0, confidence: float = 1.0,
) -> dict[str, torch.Tensor]:
    """Create legal two-source raw tensors with one receiver and one target."""
    n, node_dim, edge_dim = 4, 21, 18
    p_node = torch.zeros(1, n, node_dim)
    c_node = torch.zeros(1, n, node_dim)
    p_edge = torch.zeros(1, n, n, edge_dim)
    c_edge = torch.zeros(1, n, n, edge_dim)
    p_adj = torch.eye(n).unsqueeze(0)
    c_adj = torch.eye(n).unsqueeze(0)
    p_node[:, 0, -1] = 1.0
    c_node[:, 0, -1] = 1.0
    if p_available:
        p_node[:, -1, 0] = p_value
        p_node[:, -1, 15] = 1.0
        p_node[:, -1, 16] = 1.0
        p_node[:, -1, -1] = 1.0
        p_edge[:, 0, -1, 11] = 1.0
        p_edge[:, 0, -1, 16] = 1.0
        p_edge[:, 0, -1, 17] = 1.0
        p_adj[:, 0, -1] = 1.0
    if c_available:
        c_node[:, -1, 0] = c_value
        c_node[:, -1, 15] = 1.0
        c_node[:, -1, 16] = 1.0
        c_node[:, -1, -1] = 1.0
        c_edge[:, 0, -1, 12] = 1.0
        c_edge[:, 0, -1, 15] = age
        c_edge[:, 0, -1, 16] = confidence
        c_edge[:, 0, -1, 17] = 1.0
        c_adj[:, 0, -1] = 1.0
    return {
        "p_node_feat": p_node,
        "c_node_feat": c_node,
        "p_edge_feat": p_edge,
        "c_edge_feat": c_edge,
        "p_adj": p_adj,
        "c_adj": c_adj,
        "context": torch.zeros(1, 34),
        "role": torch.zeros(1, n, dtype=torch.long),
    }


def make_encoder() -> TwoSourcePCRFR2Encoder:
    torch.manual_seed(19)
    return TwoSourcePCRFR2Encoder(node_feat_dim=21, role_dim=4, edge_dim=18, hidden_dim=12).eval()


def run_encoder(encoder: TwoSourcePCRFR2Encoder, source: dict[str, torch.Tensor]):
    # Role labels are fixed legal context.  This static source-intervention
    # test uses a deterministic zero role embedding so it never mistakes a
    # freshly initialized fixture for cross-source influence.
    role_feat = torch.zeros(
        *source["role"].shape, 4, dtype=source["p_node_feat"].dtype
    )
    return encoder(
        source["p_node_feat"], source["c_node_feat"], source["p_edge_feat"], source["c_edge_feat"],
        source["p_adj"], source["c_adj"], role_feat,
    )


def configure_conflict_response(encoder: TwoSourcePCRFR2Encoder) -> None:
    with torch.no_grad():
        first, last = encoder.gate_correction[0], encoder.gate_correction[-1]
        first.weight.zero_()
        first.bias.zero_()
        first.weight[0, 1] = 1.0  # content disagreement
        first.weight[1, 2] = 1.0  # age
        last.weight.zero_()
        last.bias.zero_()
        last.weight[1, 0] = 2.0
        last.weight[1, 1] = -2.0


def test_source_intervention_keeps_other_branch_invariant() -> None:
    encoder = make_encoder()
    base = source_tensors()
    _, _, diag_a = run_encoder(encoder, base)
    c_changed = copy.deepcopy(base)
    c_changed["c_node_feat"][:, -1, 0] = 0.8
    _, _, diag_b = run_encoder(encoder, c_changed)
    assert torch.equal(diag_a["h_p"], diag_b["h_p"])
    p_changed = copy.deepcopy(base)
    p_changed["p_node_feat"][:, -1, 0] = 0.8
    _, _, diag_c = run_encoder(encoder, p_changed)
    assert torch.equal(diag_a["h_c"], diag_c["h_c"])


def test_delta_zero_is_exact_after_parameter_change() -> None:
    encoder = make_encoder()
    with torch.no_grad():
        for parameter in encoder.gate_correction.parameters():
            parameter.copy_(torch.randn_like(parameter))
    source = source_tensors(p_value=0.31, c_value=0.31, age=0.0, confidence=1.0)
    weights, diag = encoder.fusion_gate(
        source["p_node_feat"], source["c_node_feat"], source["p_adj"], source["c_adj"], source["c_edge_feat"]
    )
    assert torch.equal(diag["gate_delta"], torch.zeros_like(diag["gate_delta"]))
    assert torch.allclose(weights, encoder.baseline_gate().unsqueeze(0), atol=0.0, rtol=0.0)


def test_baseline_gate_does_not_read_conflict_variables() -> None:
    encoder = make_encoder()
    first = source_tensors()
    second = source_tensors(p_value=0.8, c_value=0.1, age=0.9, confidence=0.2)
    _, first_diag = encoder.fusion_gate(
        first["p_node_feat"], first["c_node_feat"], first["p_adj"], first["c_adj"], first["c_edge_feat"]
    )
    _, second_diag = encoder.fusion_gate(
        second["p_node_feat"], second["c_node_feat"], second["p_adj"], second["c_adj"], second["c_edge_feat"]
    )
    assert torch.equal(first_diag["baseline_gate"], second_diag["baseline_gate"])
    assert encoder.baseline_gate_logits.numel() == 2


def test_single_source_degenerates_to_unit_weight() -> None:
    encoder = make_encoder()
    only_p = source_tensors(c_available=False)
    only_c = source_tensors(p_available=False)
    p_weights, _ = encoder.fusion_gate(
        only_p["p_node_feat"], only_p["c_node_feat"], only_p["p_adj"], only_p["c_adj"], only_p["c_edge_feat"]
    )
    c_weights, _ = encoder.fusion_gate(
        only_c["p_node_feat"], only_c["c_node_feat"], only_c["p_adj"], only_c["c_adj"], only_c["c_edge_feat"]
    )
    assert torch.equal(p_weights, torch.tensor([[1.0, 0.0]]))
    assert torch.equal(c_weights, torch.tensor([[0.0, 1.0]]))


def test_conflict_interventions_change_delta_and_receive_gradient() -> None:
    encoder = make_encoder().train()
    configure_conflict_response(encoder)
    agreement = source_tensors()
    stale_conflict = source_tensors(p_value=0.8, c_value=0.1, age=0.8, confidence=0.3)
    _, agreement_diag = encoder.fusion_gate(
        agreement["p_node_feat"], agreement["c_node_feat"], agreement["p_adj"], agreement["c_adj"], agreement["c_edge_feat"]
    )
    weights, conflict_diag = encoder.fusion_gate(
        stale_conflict["p_node_feat"], stale_conflict["c_node_feat"], stale_conflict["p_adj"], stale_conflict["c_adj"], stale_conflict["c_edge_feat"]
    )
    assert not torch.equal(conflict_diag["gate_delta"], agreement_diag["gate_delta"])
    weights[:, 1].sum().backward()
    assert encoder.gate_correction[-1].weight.grad is not None
    assert float(encoder.gate_correction[-1].weight.grad.norm()) > 0.0


def make_actor() -> RIActor:
    torch.manual_seed(23)
    return RIActor(
        obs_dim=34, node_feat_dim=21, edge_feat_dim=18, num_roles=5, role_dim=4,
        intent_dim=4, hidden_dim=16, action_dim=27, graph_encoder="pcrf_r2", use_intent_context=False,
    ).eval()


def actor_logits(actor: RIActor, source: dict[str, torch.Tensor], *, legacy_scale: float = 0.0) -> torch.Tensor:
    n = source["p_node_feat"].shape[1]
    return actor(
        torch.full((1, 1, 34), legacy_scale),
        torch.full((1, n, 21), legacy_scale),
        torch.full((1, n, n, 18), legacy_scale),
        source["role"], source["p_adj"], 1, pcrf_r2=source,
    )[0]


def test_historical_common_inputs_cannot_bypass_r2_contract() -> None:
    actor = make_actor()
    source = source_tensors()
    assert torch.equal(actor_logits(actor, source, legacy_scale=0.0), actor_logits(actor, source, legacy_scale=999.0))


def test_unavailable_source_truth_cannot_change_actor() -> None:
    actor = make_actor()
    no_c = source_tensors(c_available=False)
    changed_c = copy.deepcopy(no_c)
    changed_c["c_node_feat"][:, -1, :11] = 999.0
    changed_c["c_edge_feat"][:, 0, -1, :] = 999.0
    assert torch.equal(actor_logits(actor, no_c), actor_logits(actor, changed_c))
    no_p = source_tensors(p_available=False)
    changed_p = copy.deepcopy(no_p)
    changed_p["p_node_feat"][:, -1, :11] = 999.0
    changed_p["p_edge_feat"][:, 0, -1, :] = 999.0
    assert torch.equal(actor_logits(actor, no_p), actor_logits(actor, changed_p))


def test_global_truth_counterfactual_is_hidden_from_r2_actor() -> None:
    env = UAVIntercept3DEnv(UAVIntercept3DConfig(
        seed=31, strict_target_sensing=True, agent_target_info_bottleneck=True,
        communication_dropout_prob=1.0,
    ))
    _, _, graph = env.reset()
    source = {
        "p_node_feat": torch.tensor(graph["pcrf_r2_p_node_feat"][None, 0]),
        "c_node_feat": torch.tensor(graph["pcrf_r2_c_node_feat"][None, 0]),
        "p_edge_feat": torch.tensor(graph["pcrf_r2_p_edge_feat"][None, 0]),
        "c_edge_feat": torch.tensor(graph["pcrf_r2_c_edge_feat"][None, 0]),
        "p_adj": torch.tensor(graph["pcrf_r2_p_adj"][None, 0]),
        "c_adj": torch.tensor(graph["pcrf_r2_c_adj"][None, 0]),
        "context": torch.tensor(graph["pcrf_r2_context"][None, 0]),
        "role": torch.tensor(graph["pcrf_r2_role"][None, 0]),
    }
    actor = make_actor()
    before = actor_logits(actor, source)
    env.blue_pos[1] += np.asarray([700.0, -300.0, 50.0], dtype=np.float32)
    changed = env._get_graph_obs()
    after_source = {
        key: torch.tensor(changed[f"pcrf_r2_{prefix}"][None, 0])
        for key, prefix in {
            "p_node_feat": "p_node_feat", "c_node_feat": "c_node_feat", "p_edge_feat": "p_edge_feat",
            "c_edge_feat": "c_edge_feat", "p_adj": "p_adj", "c_adj": "c_adj", "context": "context", "role": "role",
        }.items()
    }
    assert torch.equal(before, actor_logits(actor, after_source))


def test_task_support_and_union_paths_are_absent() -> None:
    source = source_tensors()
    assert not any("task" in key or "union" in key for key in source)
    encoder = make_encoder()
    assert not any("task" in name or "union" in name or "role_pair" in name for name, _ in encoder.named_modules())
    assert effective_chain_aux_coef(RIGMAPPOConfig(env_name="3d_intercept", graph_encoder="pcrf_r2", chain_aux_coef=1.0), 99) == 0.0


def test_r2_comparators_receive_identical_raw_source_hashes() -> None:
    source = source_tensors(p_value=0.7, c_value=0.2, age=0.4, confidence=0.6)
    digest = hashlib.sha256()
    for key in sorted(source):
        digest.update(key.encode("utf-8"))
        digest.update(source[key].detach().cpu().numpy().tobytes())
    expected = digest.hexdigest()
    actors = [
        make_actor(),
        RIActor(34, 21, 18, 5, 4, 4, 16, 27, graph_encoder="single_r2", use_intent_context=False).eval(),
        RIActor(34, 21, 18, 5, 4, 4, 16, 27, graph_encoder="matched_nongraph_r2", use_intent_context=False).eval(),
    ]
    for actor in actors:
        assert actor_logits(actor, source).shape == (1, 1, 27)
        current = hashlib.sha256()
        for key in sorted(source):
            current.update(key.encode("utf-8"))
            current.update(source[key].detach().cpu().numpy().tobytes())
        assert current.hexdigest() == expected


def test_wider_single_graph_capacity_can_be_matched() -> None:
    common = dict(
        obs_dim=34, node_feat_dim=21, edge_feat_dim=18, num_roles=5,
        role_dim=8, intent_dim=8, action_dim=27, use_intent_context=False,
    )
    pcrf_params = sum(parameter.numel() for parameter in RIActor(hidden_dim=128, graph_encoder="pcrf_r2", **common).parameters())
    candidates = []
    for hidden_dim in range(64, 385):
        single_params = sum(
            parameter.numel()
            for parameter in RIActor(hidden_dim=hidden_dim, graph_encoder="single_r2", **common).parameters()
        )
        candidates.append((abs(single_params - pcrf_params), hidden_dim, single_params))
    _, matched_hidden, matched_params = min(candidates)
    gap = abs(matched_params - pcrf_params) / pcrf_params
    assert gap <= 0.03
    print(f"R2_CAPACITY_AUDIT pcrf_hidden=128 pcrf_params={pcrf_params} single_hidden={matched_hidden} single_params={matched_params} relative_gap={gap:.4f}")


def test_batched_actor_path_uses_r2_contract() -> None:
    env = UAVIntercept3DEnv(UAVIntercept3DConfig(
        seed=37, strict_target_sensing=True, agent_target_info_bottleneck=True,
    ))
    obs, share, graph = env.reset()
    stacked = stack_graphs([graph])
    agent = RIGMAPPOAgent(
        obs_dim=obs.shape[-1], node_feat_dim=graph["node_feat"].shape[-1],
        edge_feat_dim=graph["edge_feat"].shape[-1], share_obs_dim=share.shape[-1],
        action_dim=env.action_dim, num_agents=env.num_agents, num_roles=5,
        role_dim=4, intent_dim=4, hidden_dim=16, graph_encoder="pcrf_r2",
        use_intent_context=False,
    ).eval()
    actions, *_ = agent.get_action_and_value(
        torch.tensor(obs[None], dtype=torch.float32),
        torch.tensor(stacked["node_feat"], dtype=torch.float32),
        torch.tensor(stacked["edge_feat"], dtype=torch.float32),
        torch.tensor(stacked["role"], dtype=torch.long),
        torch.tensor(stacked["adj"], dtype=torch.float32),
        torch.tensor(share[None], dtype=torch.float32),
        relation_adj=torch.tensor(stacked["relation_adj"], dtype=torch.float32),
        pcrf_r2=pcrf_r2_tensors(stacked, torch.device("cpu")),
        deterministic=True,
    )
    assert tuple(actions.shape) == (1, env.num_agents)


def main() -> None:
    tests = [
        test_source_intervention_keeps_other_branch_invariant,
        test_delta_zero_is_exact_after_parameter_change,
        test_baseline_gate_does_not_read_conflict_variables,
        test_single_source_degenerates_to_unit_weight,
        test_conflict_interventions_change_delta_and_receive_gradient,
        test_historical_common_inputs_cannot_bypass_r2_contract,
        test_unavailable_source_truth_cannot_change_actor,
        test_global_truth_counterfactual_is_hidden_from_r2_actor,
        test_task_support_and_union_paths_are_absent,
        test_r2_comparators_receive_identical_raw_source_hashes,
        test_wider_single_graph_capacity_can_be_matched,
        test_batched_actor_path_uses_r2_contract,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"PCRF_R2_D0_TEST_REPORT_V1_9: PASS ({len(tests)} tests)")


if __name__ == "__main__":
    main()
