"""Deterministic P0-B regression for the frozen PCRF-R2 C-source contract."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import RIActor  # noqa: E402
from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv  # noqa: E402


def make_env() -> UAVIntercept3DEnv:
    env = UAVIntercept3DEnv(UAVIntercept3DConfig(
        seed=59,
        strict_target_sensing=True,
        agent_target_info_bottleneck=True,
        communication_dropout_prob=0.0,
        radar_dropout_prob=1.0,
        max_target_message_age_steps=2,
    ))
    env.reset()
    return env


def graph_from_target_packet(*, age: int, target_pos: np.ndarray, confidence: float = 1.0) -> dict:
    env = make_env()
    receiver, sender = 0, 1
    packet = copy.deepcopy(env.sender_packet_cache[receiver][sender])
    packet.update({
        "validity": 1.0,
        "target_pos": np.asarray(target_pos, dtype=np.float32),
        "target_vel": np.asarray([10.0, -5.0, 1.0], dtype=np.float32),
        "target_confidence": float(confidence),
        "target_generation_step": 0,
        "send_step": 0,
        "delivery_step": 0,
    })
    env.sender_packet_cache[receiver][sender] = packet
    env.step_count = age
    return env._get_graph_obs()


def c_target_index(graph: dict) -> int:
    return graph["pcrf_r2_c_node_feat"].shape[1] - 1


def source_for_receiver(graph: dict, receiver: int = 0) -> dict[str, torch.Tensor]:
    return {
        "p_node_feat": torch.tensor(graph["pcrf_r2_p_node_feat"][None, receiver]),
        "c_node_feat": torch.tensor(graph["pcrf_r2_c_node_feat"][None, receiver]),
        "p_edge_feat": torch.tensor(graph["pcrf_r2_p_edge_feat"][None, receiver]),
        "c_edge_feat": torch.tensor(graph["pcrf_r2_c_edge_feat"][None, receiver]),
        "p_adj": torch.tensor(graph["pcrf_r2_p_adj"][None, receiver]),
        "c_adj": torch.tensor(graph["pcrf_r2_c_adj"][None, receiver]),
        "context": torch.tensor(graph["pcrf_r2_context"][None, receiver]),
        "role": torch.tensor(graph["pcrf_r2_role"][None, receiver]),
    }


def actor_logits(graph: dict) -> torch.Tensor:
    torch.manual_seed(71)
    actor = RIActor(
        obs_dim=34, node_feat_dim=21, edge_feat_dim=18, num_roles=5, role_dim=4,
        intent_dim=4, hidden_dim=16, action_dim=27, graph_encoder="pcrf_r2",
        use_intent_context=False,
    ).eval()
    source = source_for_receiver(graph)
    n = source["p_node_feat"].shape[1]
    return actor(
        torch.zeros(1, 1, 34), torch.zeros(1, n, 21), torch.zeros(1, n, n, 18),
        source["role"], source["p_adj"], 1, pcrf_r2=source,
    )[0]


def test_age_at_max_is_legal() -> None:
    graph = graph_from_target_packet(age=2, target_pos=np.asarray([1_234.0, -567.0, 4_321.0]))
    target = c_target_index(graph)
    assert graph["pcrf_r2_c_adj"][0, 0, target] == 1.0
    assert graph["pcrf_r2_c_node_feat"][0, target, -1] == 1.0


def test_age_above_max_is_invalid() -> None:
    graph = graph_from_target_packet(age=3, target_pos=np.asarray([1_234.0, -567.0, 4_321.0]))
    target = c_target_index(graph)
    assert graph["pcrf_r2_c_adj"][0, 0, target] == 0.0
    assert np.all(graph["pcrf_r2_c_node_feat"][0, target] == 0.0)


def test_expired_packet_has_no_c_node_or_adjacency() -> None:
    graph = graph_from_target_packet(age=3, target_pos=np.asarray([1_234.0, -567.0, 4_321.0]))
    target = c_target_index(graph)
    assert np.all(graph["pcrf_r2_c_node_feat"][0, 1:] == 0.0)
    assert np.all(graph["pcrf_r2_c_adj"][0, 0, 1:] == 0.0)
    assert graph["pcrf_r2_c_adj"][0, 0, target] == 0.0


def test_expired_packet_payload_cannot_change_actor() -> None:
    first = graph_from_target_packet(age=3, target_pos=np.asarray([1_234.0, -567.0, 4_321.0]), confidence=1.0)
    second = graph_from_target_packet(age=3, target_pos=np.asarray([-9_876.0, 4_321.0, 1_111.0]), confidence=0.3)
    assert torch.equal(actor_logits(first), actor_logits(second))


def test_fresh_cache_valid_packet_remains_visible() -> None:
    target_pos = np.asarray([1_234.0, -567.0, 4_321.0])
    graph = graph_from_target_packet(age=1, target_pos=target_pos)
    target = c_target_index(graph)
    assert graph["pcrf_r2_c_adj"][0, 0, target] == 1.0
    assert np.isclose(
        graph["pcrf_r2_c_node_feat"][0, target, 0],
        target_pos[0] / 50_000.0,
    )


def main() -> None:
    tests = [
        test_age_at_max_is_legal,
        test_age_above_max_is_invalid,
        test_expired_packet_has_no_c_node_or_adjacency,
        test_expired_packet_payload_cannot_change_actor,
        test_fresh_cache_valid_packet_remains_visible,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"P0_B_FEATURE_PROVENANCE_AUDIT_V1_9: PASS ({len(tests)} tests)")


if __name__ == "__main__":
    main()
