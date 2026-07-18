from __future__ import annotations

import unittest
from pathlib import Path
import sys

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import GraphAttentionLayer, RIGMAPPOAgent
from envs import RELATION_TASK_SUPPORT, UAVIntercept3DConfig, UAVIntercept3DEnv


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
        self.assertEqual(float(np.sum(env.comm_adj[off_diag])), 0.0)

        env.step(actions)
        self.assertGreater(float(np.sum(env.comm_adj[off_diag])), 0.0)

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
