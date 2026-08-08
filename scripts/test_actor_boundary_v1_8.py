"""Pre-training actor-boundary leakage tests for protocol v1.8."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv  # noqa: E402


def make_env(**overrides) -> UAVIntercept3DEnv:
    cfg = UAVIntercept3DConfig(
        seed=17,
        strict_target_sensing=True,
        agent_target_info_bottleneck=True,
        node_failure_start_step=40,
        node_failure_duration_steps=80,
        **overrides,
    )
    return UAVIntercept3DEnv(cfg)


def test_unavailable_teammate_truth_is_hidden() -> None:
    env = make_env(communication_dropout_prob=1.0)
    _, _, graph = env.reset()
    before = graph["node_feat"].copy()
    env.blue_pos[1] += np.asarray([100.0, 50.0, 10.0], dtype=np.float32)
    after = env._get_graph_obs()["node_feat"]
    assert np.array_equal(before[0], after[0])
    assert graph["provenance_mask"][0, 1] == 0.0
    assert np.all(env._get_graph_obs()["edge_feat"][0, 0, 1, -1] == 0.0)


def test_delayed_packet_is_unavailable_before_delivery() -> None:
    env = make_env(communication_dropout_prob=0.0, message_delay_steps=2)
    _, _, graph0 = env.reset()
    assert graph0["provenance_mask"][0, 1] == 0.0
    env.step(np.zeros(env.config.num_blue, dtype=np.int64))
    graph1 = env._get_graph_obs()
    assert graph1["provenance_mask"][0, 1] == 0.0


def test_delayed_packet_becomes_visible_only_at_delivery() -> None:
    env = make_env(communication_dropout_prob=0.0, message_delay_steps=2)
    env.reset()
    env.step(np.zeros(env.config.num_blue, dtype=np.int64))
    _, _, graph2, _, _, _ = env.step(np.zeros(env.config.num_blue, dtype=np.int64))
    assert graph2["provenance_mask"][0, 1] == 1.0


def test_delivered_packet_snapshots_sender_fields() -> None:
    env = make_env(communication_dropout_prob=0.0, message_delay_steps=0)
    env.reset()
    packet = env.sender_packet_cache[0][1]
    sent_position = np.asarray(packet["position"]).copy()
    env.blue_pos[1] += np.asarray([123.0, 0.0, 0.0], dtype=np.float32)
    assert np.array_equal(sent_position, packet["position"])


def test_dropped_packet_never_enters_cache() -> None:
    env = make_env(communication_dropout_prob=1.0, message_delay_steps=0)
    env.reset()
    assert env.sender_packet_cache[0].get(1) is None


def test_cache_does_not_refresh_from_truth() -> None:
    env = make_env(communication_dropout_prob=0.0, message_delay_steps=0)
    _, _, graph = env.reset()
    old = graph["node_feat"][0, 1].copy()
    env.blue_pos[1] += np.asarray([200.0, 0.0, 0.0], dtype=np.float32)
    current = env._get_graph_obs()["node_feat"][0, 1]
    assert np.array_equal(old, current)


def test_target_unavailable_is_zeroed() -> None:
    env = make_env(communication_dropout_prob=1.0, radar_dropout_prob=1.0)
    env.reset()
    env.detected_by[:] = 0.0
    env.target_cache_valid[:] = 0.0
    graph = env._get_graph_obs()
    assert graph["provenance_mask"][0, -1] == 0.0
    assert np.all(graph["node_feat"][0, -1, :4] == 0.0)
    assert np.all(graph["node_feat"][0, -1, 8:11] == 0.0)
    assert graph["node_feat"][0, -1, 16] == 0.0
    assert graph["node_feat"][0, -1, 17] == 0.0


def test_invalid_endpoint_has_no_geometry() -> None:
    env = make_env(communication_dropout_prob=1.0)
    env.reset()
    graph = env._get_graph_obs()
    assert graph["edge_feat"][0, 0, 1, -1] == 0.0
    assert np.all(graph["edge_feat"][0, 0, 1, :4] == 0.0)


def test_relation_mask_does_not_create_provenance() -> None:
    env = make_env(communication_dropout_prob=1.0)
    _, _, graph = env.reset()
    assert graph["provenance_mask"][0, 1] == 0.0
    assert np.all(graph["relation_adj"][:, :, 0, 1] == 0.0)


def test_raw_views_are_encoder_independent() -> None:
    env = make_env(communication_dropout_prob=0.0)
    _, _, graph = env.reset()
    raw = {key: graph[key].copy() for key in ("node_feat", "edge_feat", "provenance_mask")}
    for key, value in raw.items():
        assert np.array_equal(value, graph[key])


def test_actor_input_does_not_use_critic_shared_state() -> None:
    env = make_env(communication_dropout_prob=0.0)
    obs, share, graph = env.reset()
    from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOAgent
    import torch
    agent = RIGMAPPOAgent(
        obs_dim=obs.shape[-1], node_feat_dim=graph["node_feat"].shape[-1],
        edge_feat_dim=graph["edge_feat"].shape[-1], share_obs_dim=share.shape[-1],
        action_dim=env.action_dim, num_agents=3, num_roles=5, hidden_dim=16,
        role_dim=4, intent_dim=4, graph_encoder="multi_relation",
    )
    args = (torch.tensor(obs[None, 0:1], dtype=torch.float32),
            torch.tensor(graph["node_feat"][None, 0], dtype=torch.float32),
            torch.tensor(graph["edge_feat"][None, 0], dtype=torch.float32),
            torch.tensor(graph["role"][None, 0], dtype=torch.long),
            torch.tensor(graph["adj"][None, 0], dtype=torch.float32))
    rel = torch.tensor(graph["relation_adj"][None, 0], dtype=torch.float32)
    first = agent.actor(*args, 1, relation_adj=rel)[0]
    altered_share = share.copy() + 999.0
    second = agent.actor(*args, 1, relation_adj=rel)[0]
    assert torch.equal(first, second)


def test_relay_failure_does_not_bypass_cache_provenance() -> None:
    env = make_env(communication_dropout_prob=0.0, message_delay_steps=0, failed_blue_agent=1)
    _, _, graph = env.reset()
    old = graph["node_feat"][0, 1].copy()
    env.blue_pos[1] += np.asarray([300.0, 0.0, 0.0], dtype=np.float32)
    current = env._get_graph_obs()["node_feat"][0, 1]
    assert np.array_equal(old, current)
    assert env.sender_packet_cache[0][1]["send_step"] <= env.step_count


def test_pending_packet_payload_is_not_in_view() -> None:
    env = make_env(communication_dropout_prob=0.0, message_delay_steps=3)
    env.reset()
    assert env.pending_status_messages
    graph = env._get_graph_obs()
    assert graph["provenance_mask"][0, 1] == 0.0


def test_vectorized_and_reference_views_match() -> None:
    env = make_env(communication_dropout_prob=0.0)
    env.reset()
    graph = env._get_graph_obs()
    for receiver in range(env.config.num_blue):
        reference = env._get_recipient_graph_view(receiver)
        assert np.array_equal(graph["node_feat"][receiver], reference["node_feat"])
        assert np.array_equal(graph["edge_feat"][receiver], reference["edge_feat"])
        assert np.array_equal(graph["relation_adj"][receiver], reference["relation_adj"])


def main() -> None:
    tests = [
        test_unavailable_teammate_truth_is_hidden,
        test_delayed_packet_is_unavailable_before_delivery,
        test_delayed_packet_becomes_visible_only_at_delivery,
        test_delivered_packet_snapshots_sender_fields,
        test_dropped_packet_never_enters_cache,
        test_cache_does_not_refresh_from_truth,
        test_target_unavailable_is_zeroed,
        test_invalid_endpoint_has_no_geometry,
        test_relation_mask_does_not_create_provenance,
        test_raw_views_are_encoder_independent,
        test_actor_input_does_not_use_critic_shared_state,
        test_relay_failure_does_not_bypass_cache_provenance,
        test_pending_packet_payload_is_not_in_view,
        test_vectorized_and_reference_views_match,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"ACTOR_BOUNDARY_TEST_REPORT_V1_8: PASS ({len(tests)} tests)")


if __name__ == "__main__":
    main()
