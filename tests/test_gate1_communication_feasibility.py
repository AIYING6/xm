from __future__ import annotations

import argparse
import unittest
from pathlib import Path
import sys

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import GraphAttentionLayer, RIGMAPPOAgent
from envs import RELATION_TASK_SUPPORT, UAVIntercept3DConfig, UAVIntercept3DEnv
from scripts.evaluate_ri_gmappo_3d import post_failure_recovery_metrics


class Gate1CommunicationFeasibilityTest(unittest.TestCase):
    def test_graph_attention_uses_receiver_sender_direction(self) -> None:
        layer = GraphAttentionLayer(in_dim=2, out_dim=2, edge_dim=0)
        with torch.no_grad():
            layer.proj.weight.copy_(torch.eye(2))
            layer.attn.weight.zero_()

        x = torch.tensor([[[1.0, 0.0], [0.0, 1.0]]])
        adj = torch.tensor([[[1.0, 0.0], [1.0, 1.0]]])
        _, weights = layer(x, adj)

        self.assertGreater(float(weights[0, 1, 0]), 0.0)
        self.assertEqual(float(weights[0, 0, 1]), 0.0)

    def test_task_support_relation_requires_delivered_communication(self) -> None:
        env = UAVIntercept3DEnv(
            UAVIntercept3DConfig(
                strict_target_sensing=True,
                agent_target_info_bottleneck=True,
                seed=7,
            )
        )
        env.reset()
        env.detected_by[:] = 0.0
        env.detected_by[0] = 1.0
        env.comm_adj[:] = np.eye(env.config.num_blue, dtype=np.float32)
        env.message_age[:] = env.config.max_steps
        np.fill_diagonal(env.message_age, 0.0)

        graph = env._get_graph_obs()
        task_adj = graph["relation_adj"][RELATION_TASK_SUPPORT]
        self.assertEqual(float(np.sum(task_adj - np.diag(np.diag(task_adj)))), 0.0)

        env.comm_adj[2, 0] = 1.0
        env.message_age[2, 0] = 0.0
        graph = env._get_graph_obs()
        self.assertEqual(float(graph["relation_adj"][RELATION_TASK_SUPPORT, 2, 0]), 1.0)
        self.assertEqual(float(graph["relation_adj"][RELATION_TASK_SUPPORT, 0, 2]), 0.0)

    def test_disconnected_attacker_logits_do_not_change_with_hidden_target(self) -> None:
        torch.manual_seed(11)
        env = UAVIntercept3DEnv(
            UAVIntercept3DConfig(
                strict_target_sensing=True,
                agent_target_info_bottleneck=True,
                seed=11,
            )
        )
        obs, share_obs, graph = env.reset()
        agent = RIGMAPPOAgent(
            obs_dim=env.obs_dim,
            node_feat_dim=graph["node_feat"].shape[-1],
            edge_feat_dim=graph["edge_feat"].shape[-1],
            share_obs_dim=share_obs.shape[-1],
            action_dim=env.action_dim,
            num_agents=env.num_agents,
            num_roles=max(4, int(np.max(graph["role"])) + 1),
            hidden_dim=32,
            role_dim=4,
            intent_dim=4,
            graph_encoder="multi_relation",
            use_intent_context=False,
        )
        agent.eval()

        logits_a = self._attacker_logits_for_hidden_target(env, agent, np.array([8000.0, -1000.0, 5100.0]))
        logits_b = self._attacker_logits_for_hidden_target(env, agent, np.array([18000.0, 6000.0, 7000.0]))

        np.testing.assert_allclose(logits_a, logits_b, atol=1e-6, rtol=0.0)

    def test_actor_observation_does_not_include_global_aggregate_shortcuts(self) -> None:
        env = UAVIntercept3DEnv(
            UAVIntercept3DConfig(
                strict_target_sensing=True,
                agent_target_info_bottleneck=True,
                seed=13,
            )
        )
        env.reset()
        attacker = 2
        env.comm_adj[:] = np.eye(env.config.num_blue, dtype=np.float32)
        env.message_age[:] = env.config.max_steps
        np.fill_diagonal(env.message_age, 0.0)
        env._write_target_cache(
            attacker,
            pos=np.array([1000.0, 200.0, 5200.0], dtype=np.float32),
            vel=np.array([180.0, 0.0, 0.0], dtype=np.float32),
            source=0,
            generation_step=3,
            delivery_step=5,
            hop_count=1,
            confidence=0.7,
            path=[0, attacker],
        )
        env.step_count = 9
        env.last_detection_step = 4
        env.attack_hold = 0
        obs_before = env._get_obs()[attacker].copy()

        # Change only team-level aggregates that a decentralized attacker should
        # not receive directly through its actor observation.
        env.comm_adj[0, 1] = 1.0
        env.comm_adj[1, 0] = 1.0
        env.message_age[0, 1] = 0.0
        env.message_age[1, 0] = 0.0
        env.last_detection_step = 9
        env.attack_hold = env.config.attack_hold_steps
        obs_after = env._get_obs()[attacker].copy()

        np.testing.assert_allclose(obs_before, obs_after, atol=1e-6, rtol=0.0)

    def test_strict_bottleneck_graph_hides_stale_global_target_state(self) -> None:
        env = UAVIntercept3DEnv(
            UAVIntercept3DConfig(
                strict_target_sensing=True,
                agent_target_info_bottleneck=True,
                seed=47,
            )
        )
        env.reset()
        env.detected_by[:] = 0.0
        env.last_detected_target_pos = np.array([8000.0, -1000.0, 5100.0], dtype=np.float32)
        env.last_detected_target_vel = np.array([200.0, 0.0, 0.0], dtype=np.float32)
        graph_a = env._get_graph_obs()

        env.last_detected_target_pos = np.array([18000.0, 6000.0, 7000.0], dtype=np.float32)
        env.last_detected_target_vel = np.array([120.0, 80.0, 20.0], dtype=np.float32)
        graph_b = env._get_graph_obs()

        np.testing.assert_allclose(graph_a["node_feat"], graph_b["node_feat"], atol=1e-6, rtol=0.0)
        np.testing.assert_allclose(graph_a["edge_feat"], graph_b["edge_feat"], atol=1e-6, rtol=0.0)
        prior = np.asarray(env.config.target_prior_position, dtype=np.float32)
        target_node = env.config.num_blue
        np.testing.assert_allclose(
            graph_a["node_feat"][target_node, :3],
            np.array(
                [
                    prior[0] / env.config.world_radius,
                    prior[1] / env.config.world_radius,
                    prior[2] / env.config.max_altitude,
                ],
                dtype=np.float32,
            ),
            atol=1e-6,
            rtol=0.0,
        )

        env.detected_by[:] = 0.0
        env.detected_by[0] = 1.0
        env.red_pos[0] = np.array([12000.0, 3000.0, 5300.0], dtype=np.float32)
        graph_detected = env._get_graph_obs()
        self.assertNotAlmostEqual(
            float(graph_detected["node_feat"][target_node, 0]),
            float(graph_a["node_feat"][target_node, 0]),
            places=5,
        )

    def test_message_delay_requires_future_delivery_step(self) -> None:
        env = UAVIntercept3DEnv(
            UAVIntercept3DConfig(
                seed=17,
                target_policy="straight",
                communication_range_scale=10.0,
                communication_dropout_prob=0.0,
                message_delay_steps=2,
            )
        )
        env.reset()
        off_diag = ~np.eye(env.config.num_blue, dtype=bool)
        self.assertEqual(float(np.sum(env.comm_adj[off_diag])), 0.0)
        self.assertGreater(len(env.pending_messages), 0)

        actions = np.full(env.config.num_blue, 13, dtype=np.int64)
        env.step(actions)
        self.assertEqual(float(np.sum(env.comm_adj[off_diag])), 0.0)

        env.step(actions)
        self.assertGreater(float(np.sum(env.comm_adj[off_diag])), 0.0)

    def test_step_info_and_failure_window_use_post_step_timing(self) -> None:
        env = UAVIntercept3DEnv(
            UAVIntercept3DConfig(
                seed=43,
                failed_blue_agent=1,
                node_failure_start_step=1,
                node_failure_duration_steps=2,
            )
        )
        env.reset()
        self.assertEqual(env.step_count, 0)
        self.assertFalse(env._is_comm_failed(1))

        actions = np.full(env.config.num_blue, 13, dtype=np.int64)
        _, _, _, _, _, info1 = env.step(actions)
        self.assertEqual(float(info1["step"]), 1.0)
        self.assertEqual(float(info1["node_failure_active"]), 1.0)
        self.assertTrue(env._is_comm_failed(1))

        _, _, _, _, _, info2 = env.step(actions)
        self.assertEqual(float(info2["step"]), 2.0)
        self.assertEqual(float(info2["node_failure_active"]), 1.0)

        _, _, _, _, _, info3 = env.step(actions)
        self.assertEqual(float(info3["step"]), 3.0)
        self.assertEqual(float(info3["node_failure_active"]), 0.0)
        self.assertFalse(env._is_comm_failed(1))

    def test_post_failure_metrics_split_maintained_recovered_and_unrecovered(self) -> None:
        args = argparse.Namespace(
            failed_blue_agent=1,
            node_failure_start_step=2,
            node_failure_duration_steps=2,
        )
        base_infos = [
            {"step": 1.0, "node_failure_active": 0.0, "chain_closed": 0.0, "tracking_rate": 1.0, "comm_connectivity": 1.0},
            {"step": 2.0, "node_failure_active": 1.0, "chain_closed": 1.0, "tracking_rate": 1.0, "comm_connectivity": 1.0},
            {"step": 3.0, "node_failure_active": 1.0, "chain_closed": 1.0, "tracking_rate": 1.0, "comm_connectivity": 1.0},
        ]
        maintained = post_failure_recovery_metrics(base_infos, args)
        self.assertEqual(float(maintained["post_failure_chain_maintained"]), 1.0)
        self.assertEqual(float(maintained["post_failure_chain_recovered_after_loss"]), 0.0)
        self.assertEqual(float(maintained["post_failure_chain_unrecovered"]), 0.0)

        recovered_infos = [dict(info) for info in base_infos]
        recovered_infos[1]["chain_closed"] = 0.0
        recovered = post_failure_recovery_metrics(recovered_infos, args)
        self.assertEqual(float(recovered["post_failure_chain_maintained"]), 0.0)
        self.assertEqual(float(recovered["post_failure_chain_recovered_after_loss"]), 1.0)
        self.assertEqual(float(recovered["post_failure_chain_unrecovered"]), 0.0)
        self.assertEqual(float(recovered["post_failure_chain_recovery_steps"]), 1.0)

        unrecovered_infos = [dict(info) for info in base_infos]
        unrecovered_infos[1]["chain_closed"] = 0.0
        unrecovered_infos[2]["chain_closed"] = 0.0
        unrecovered = post_failure_recovery_metrics(unrecovered_infos, args)
        self.assertEqual(float(unrecovered["post_failure_chain_maintained"]), 0.0)
        self.assertEqual(float(unrecovered["post_failure_chain_recovered_after_loss"]), 0.0)
        self.assertEqual(float(unrecovered["post_failure_chain_unrecovered"]), 1.0)

    def test_packet_dropout_prevents_delayed_delivery(self) -> None:
        env = UAVIntercept3DEnv(
            UAVIntercept3DConfig(
                seed=19,
                communication_range_scale=10.0,
                communication_dropout_prob=1.0,
                message_delay_steps=2,
            )
        )
        env.reset()
        off_diag = ~np.eye(env.config.num_blue, dtype=bool)
        self.assertEqual(len(env.pending_messages), 0)

        actions = np.full(env.config.num_blue, 13, dtype=np.int64)
        for _ in range(4):
            env.step(actions)
        self.assertEqual(float(np.sum(env.comm_adj[off_diag])), 0.0)
        self.assertEqual(len(env.pending_messages), 0)

    def test_comm_failure_drops_queued_delivery(self) -> None:
        env = UAVIntercept3DEnv(
            UAVIntercept3DConfig(
                seed=23,
                communication_range_scale=10.0,
                communication_dropout_prob=0.0,
                message_delay_steps=2,
                failed_blue_agent=1,
                node_failure_start_step=1,
                node_failure_duration_steps=10,
            )
        )
        env.reset()
        self.assertGreater(len(env.pending_messages), 0)

        actions = np.full(env.config.num_blue, 13, dtype=np.int64)
        for _ in range(3):
            env.step(actions)

        self.assertEqual(float(env.comm_adj[1, 0]), 0.0)
        self.assertEqual(float(env.comm_adj[0, 1]), 0.0)
        self.assertEqual(float(env.comm_adj[2, 1]), 0.0)
        self.assertEqual(float(env.comm_adj[1, 2]), 0.0)

    def test_target_message_cache_propagates_one_hop_per_delay_cycle(self) -> None:
        env = UAVIntercept3DEnv(
            UAVIntercept3DConfig(
                seed=29,
                communication_range_scale=1.0,
                communication_dropout_prob=0.0,
                message_delay_steps=1,
                radar_dropout_prob=1.0,
            )
        )
        env.reset()
        env.blue_pos[:] = np.asarray(
            [
                [0.0, 0.0, 5000.0],
                [7000.0, 0.0, 5000.0],
                [14000.0, 0.0, 5000.0],
            ],
            dtype=np.float32,
        )
        env.pending_messages.clear()
        env.pending_target_messages.clear()
        env.comm_adj[:] = np.eye(env.config.num_blue, dtype=np.float32)
        env.target_cache_valid[:] = 0.0
        env.target_cache_path = [[] for _ in range(env.config.num_blue)]
        env.step_count = 0
        env._write_target_cache(
            0,
            pos=np.array([1000.0, 500.0, 5200.0], dtype=np.float32),
            vel=np.array([200.0, 0.0, 0.0], dtype=np.float32),
            source=0,
            generation_step=0,
            delivery_step=0,
            hop_count=0,
            confidence=1.0,
            path=[0],
        )

        env._update_sensing_and_comm()
        self.assertEqual(float(env.target_cache_valid[1]), 0.0)
        self.assertEqual(float(env.target_cache_valid[2]), 0.0)
        self.assertTrue(
            any(int(msg["receiver"]) == 1 and int(msg["sender"]) == 0 for msg in env.pending_target_messages)
        )
        self.assertFalse(
            any(int(msg["receiver"]) == 2 and int(msg["sender"]) == 0 for msg in env.pending_target_messages)
        )

        env.step_count = 1
        env._update_sensing_and_comm()
        self.assertEqual(float(env.target_cache_valid[1]), 1.0)
        self.assertEqual(float(env.target_cache_valid[2]), 0.0)
        self.assertFalse(env._comm_has_chain_to_attacker())
        self.assertEqual(int(env.target_cache_hop_count[1]), 1)
        self.assertEqual(env.target_cache_path[1], [0, 1])

        env.step_count = 2
        env._update_sensing_and_comm()
        self.assertEqual(float(env.target_cache_valid[2]), 0.0)
        self.assertFalse(env._comm_has_chain_to_attacker())

        env.step_count = 3
        env._update_sensing_and_comm()
        self.assertEqual(float(env.target_cache_valid[2]), 1.0)
        self.assertTrue(env._comm_has_chain_to_attacker())
        self.assertEqual(int(env.target_cache_hop_count[2]), 2)
        self.assertEqual(env.target_cache_path[2], [0, 1, 2])

    def test_stale_target_cache_does_not_close_chain(self) -> None:
        env = UAVIntercept3DEnv(
            UAVIntercept3DConfig(
                strict_target_sensing=True,
                agent_target_info_bottleneck=True,
                max_target_message_age_steps=5,
                min_target_confidence=0.2,
                seed=31,
            )
        )
        env.reset()
        attacker = 2
        env.detected_by[:] = 0.0
        env.comm_adj[:] = np.eye(env.config.num_blue, dtype=np.float32)
        env._write_target_cache(
            attacker,
            pos=np.array([1000.0, 500.0, 5200.0], dtype=np.float32),
            vel=np.array([200.0, 0.0, 0.0], dtype=np.float32),
            source=0,
            generation_step=0,
            delivery_step=0,
            hop_count=1,
            confidence=1.0,
            path=[0, attacker],
        )

        env.step_count = 10
        self.assertFalse(env._has_fresh_target_cache(attacker))
        self.assertFalse(env._has_target_information(attacker))
        self.assertFalse(env._comm_has_chain_to_attacker())
        self.assertEqual(float(env._get_obs()[attacker, 31]), 0.0)
        self.assertGreater(float(env._info(False)["target_cache_stale_rate"]), 0.0)

    def test_low_confidence_target_cache_does_not_close_chain(self) -> None:
        env = UAVIntercept3DEnv(
            UAVIntercept3DConfig(
                strict_target_sensing=True,
                agent_target_info_bottleneck=True,
                max_target_message_age_steps=80,
                min_target_confidence=0.2,
                seed=37,
            )
        )
        env.reset()
        attacker = 2
        env.detected_by[:] = 0.0
        env.comm_adj[:] = np.eye(env.config.num_blue, dtype=np.float32)
        env._write_target_cache(
            attacker,
            pos=np.array([1000.0, 500.0, 5200.0], dtype=np.float32),
            vel=np.array([200.0, 0.0, 0.0], dtype=np.float32),
            source=0,
            generation_step=env.step_count,
            delivery_step=env.step_count,
            hop_count=1,
            confidence=0.1,
            path=[0, attacker],
        )

        self.assertFalse(env._has_fresh_target_cache(attacker))
        self.assertFalse(env._has_target_information(attacker))
        self.assertFalse(env._comm_has_chain_to_attacker())
        self.assertEqual(float(env._get_obs()[attacker, 31]), 0.0)

    def test_fresh_target_cache_can_close_chain(self) -> None:
        env = UAVIntercept3DEnv(
            UAVIntercept3DConfig(
                strict_target_sensing=True,
                agent_target_info_bottleneck=True,
                max_target_message_age_steps=80,
                min_target_confidence=0.2,
                seed=41,
            )
        )
        env.reset()
        attacker = 2
        env.detected_by[:] = 0.0
        env.comm_adj[:] = np.eye(env.config.num_blue, dtype=np.float32)
        env._write_target_cache(
            attacker,
            pos=np.array([1000.0, 500.0, 5200.0], dtype=np.float32),
            vel=np.array([200.0, 0.0, 0.0], dtype=np.float32),
            source=0,
            generation_step=env.step_count,
            delivery_step=env.step_count,
            hop_count=1,
            confidence=0.7,
            path=[0, attacker],
        )

        self.assertTrue(env._has_fresh_target_cache(attacker))
        self.assertTrue(env._has_target_information(attacker))
        self.assertTrue(env._comm_has_chain_to_attacker())
        self.assertAlmostEqual(float(env._get_obs()[attacker, 31]), 0.7, places=6)

    def _attacker_logits_for_hidden_target(
        self,
        env: UAVIntercept3DEnv,
        agent: RIGMAPPOAgent,
        target_pos: np.ndarray,
    ) -> np.ndarray:
        env.detected_by[:] = 0.0
        env.detected_by[0] = 1.0
        env.last_detected_target_pos = target_pos.astype(np.float32)
        env.last_detected_target_vel = np.array([200.0, 0.0, 0.0], dtype=np.float32)
        env.last_detection_step = env.step_count
        env.comm_adj[:] = np.eye(env.config.num_blue, dtype=np.float32)
        env.message_age[:] = env.config.max_steps
        np.fill_diagonal(env.message_age, 0.0)

        obs = env._get_obs()
        graph = env._get_graph_obs()
        with torch.no_grad():
            logits, _, _ = agent.actor(
                torch.as_tensor(obs[None, ...], dtype=torch.float32),
                torch.as_tensor(graph["node_feat"][None, ...], dtype=torch.float32),
                torch.as_tensor(graph["edge_feat"][None, ...], dtype=torch.float32),
                torch.as_tensor(graph["role"][None, ...], dtype=torch.long),
                torch.as_tensor(graph["adj"][None, ...], dtype=torch.float32),
                env.num_agents,
                relation_adj=torch.as_tensor(graph["relation_adj"][None, ...], dtype=torch.float32),
            )
        return logits[0, 2].numpy()


if __name__ == "__main__":
    unittest.main()
