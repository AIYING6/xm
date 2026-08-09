"""Static P0-C audit: R2 comparators must differ only by representation."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import RIActor  # noqa: E402
from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv  # noqa: E402


R2_KEYS = (
    "p_node_feat", "c_node_feat", "p_edge_feat", "c_edge_feat", "p_adj", "c_adj", "context", "role",
)


def env_source() -> dict[str, torch.Tensor]:
    env = UAVIntercept3DEnv(UAVIntercept3DConfig(
        seed=83, strict_target_sensing=True, agent_target_info_bottleneck=True,
        communication_dropout_prob=0.25, message_delay_steps=2, radar_dropout_prob=0.1,
    ))
    _, _, graph = env.reset()
    receiver = 0
    return {
        key: torch.as_tensor(graph[f"pcrf_r2_{key}"][None, receiver])
        for key in R2_KEYS
    }


def digest(source: dict[str, torch.Tensor]) -> str:
    result = hashlib.sha256()
    for key in R2_KEYS:
        value = source[key].detach().cpu().contiguous().numpy()
        result.update(key.encode("utf-8"))
        result.update(value.tobytes())
    return result.hexdigest()


def make_actor(encoder: str, hidden: int) -> RIActor:
    torch.manual_seed(89)
    return RIActor(
        obs_dim=34, node_feat_dim=21, edge_feat_dim=18, num_roles=5, role_dim=8,
        intent_dim=8, hidden_dim=hidden, action_dim=27, graph_encoder=encoder,
        use_intent_context=False,
    ).eval()


def logits(actor: RIActor, source: dict[str, torch.Tensor], legacy: float) -> torch.Tensor:
    n = source["p_node_feat"].shape[1]
    return actor(
        torch.full((1, 1, 34), legacy), torch.full((1, n, 21), legacy),
        torch.full((1, n, n, 18), legacy), source["role"], source["p_adj"], 1,
        pcrf_r2=source,
    )[0]


def test_all_r2_comparators_consume_one_identical_source_contract() -> None:
    source = env_source()
    expected = digest(source)
    for encoder, hidden in (("pcrf_r2", 128), ("single_r2", 147), ("matched_nongraph_r2", 152)):
        actor = make_actor(encoder, hidden)
        assert digest(source) == expected
        assert logits(actor, source, 0.0).shape == (1, 1, 27)


def test_single_is_source_aware_but_has_one_shared_graph_path() -> None:
    single = make_actor("single_r2", 147).r2_unified_graph
    assert single.graph
    assert single.input[0].in_features == 21 * 2 + 8
    assert single.layer1.edge_score[0].in_features == 18 * 2
    assert not hasattr(single, "p_input") and not hasattr(single, "c_input")
    assert not hasattr(single, "baseline_gate_logits") and not hasattr(single, "gate_correction")


def test_pcrf_only_adds_factorization_and_fusion() -> None:
    pcrf = make_actor("pcrf_r2", 128).pcrf_r2_graph
    assert hasattr(pcrf, "p_input") and hasattr(pcrf, "c_input")
    assert hasattr(pcrf, "baseline_gate_logits") and hasattr(pcrf, "gate_correction")
    assert not any("union" in name or "role_pair" in name or "task" in name for name, _ in pcrf.named_modules())


def test_r2_comparators_cannot_bypass_contract_through_legacy_inputs() -> None:
    source = env_source()
    for encoder, hidden in (("pcrf_r2", 128), ("single_r2", 147), ("matched_nongraph_r2", 152)):
        actor = make_actor(encoder, hidden)
        assert torch.equal(logits(actor, source, 0.0), logits(actor, source, 777.0))


def test_primary_capacity_is_near_matched() -> None:
    pcrf = make_actor("pcrf_r2", 128)
    single = make_actor("single_r2", 147)
    pcrf_params = sum(parameter.numel() for parameter in pcrf.parameters())
    single_params = sum(parameter.numel() for parameter in single.parameters())
    gap = abs(single_params - pcrf_params) / pcrf_params
    assert pcrf_params == 169_977
    assert single_params == 170_784
    assert gap < 0.01


def main() -> None:
    tests = [
        test_all_r2_comparators_consume_one_identical_source_contract,
        test_single_is_source_aware_but_has_one_shared_graph_path,
        test_pcrf_only_adds_factorization_and_fusion,
        test_r2_comparators_cannot_bypass_contract_through_legacy_inputs,
        test_primary_capacity_is_near_matched,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"P0_C_COMPARATOR_IDENTIFIABILITY_AUDIT_V1_9: PASS ({len(tests)} tests)")


if __name__ == "__main__":
    main()
