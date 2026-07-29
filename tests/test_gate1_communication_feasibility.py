from __future__ import annotations

import argparse
import unittest
from pathlib import Path
import sys

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import GraphAttentionLayer, RIGMAPPOAgent, RIGMAPPOConfig, make_env
from envs import (
    EDGE3D_FEAT_DIM,
    OBS3D_FIELD_NAMES,
    OBS3D_ROLE_IDENTITY_SLICE,
    RELATION_COMMUNICATION,
    RELATION_TASK_SUPPORT,
    UAVIntercept3DConfig,
    UAVIntercept3DEnv,
)
from scripts.evaluate_ri_gmappo_3d import post_failure_recovery_metrics


class Gate1CommunicationFeasibilityTest(unittest.TestCase):
    def test_actor_observation_schema_matches_role_identity_slice(self) -> None:
        env = UAVIntercept3DEnv(UAVIntercept3DConfig(seed=5))
        obs, _, _ = env.reset()

        self.assertEqual(len(OBS3D_FIELD_NAMES), env.obs_dim)
        self.assertEqual(tuple(OBS3D_FIELD_NAMES[OBS3D_ROLE_IDENTITY_SLICE]), (
            "role_scout",
            "role_relay",
            "role_attacker",
            "role_interceptor",
        ))
        np.testing.assert_allclose(obs[0, OBS3D_ROLE_IDENTITY_SLICE], np.array([1.0, 0.0, 0.0, 0.0]))
        np.testing.assert_allclose(obs[1, OBS3D_ROLE_IDENTITY_SLICE], np.array([0.0, 1.0, 0.0, 0.0]))
        np.testing.assert_allclose(obs[2, OBS3D_ROLE_IDENTITY_SLICE], np.array([0.0, 0.0, 1.0, 0.0]))

    def test_ri_config_passes_attack_hold_steps_to_3d_env(self) -> None:
        env = make_env(
            RIGMAPPOConfig(
                env_name="3d_intercept",
                attack_hold_steps=7,
                seed=7,
            ),
            seed=7,
            training=False,
        )

        self.assertIsInstance(env, UAVIntercept3DEnv)
        self.assertEqual(env.config.attack_hold_steps, 7)

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

    def test_multi_relation_global_residual_weight_controls_reported_global_channel(self) -> None:
        torch.manual_seed(31)
        env = UAVIntercept3DEnv(UAVIntercept3DConfig(seed=31))
        obs, share_obs, graph = env.reset()
        common_kwargs = dict(
            obs_dim=env.obs_dim,
            node_feat_dim=graph["node_feat"].shape[-1],
            edge_feat_dim=graph["edge_feat"].shape[-1],
            share_obs_dim=share_obs.shape[-1],
            action_dim=env.action_dim,
            num_agents=env.num_agents,
            num_roles=max(5, int(np.max(graph["role"])) + 1),
            hidden_dim=32,
            role_dim=4,
            intent_dim=4,
            graph_encoder="multi_relation",
            use_intent_context=False,
        )
        enabled = RIGMAPPOAgent(**common_kwargs, multi_relation_global_residual_weight=1.0)
        disabled = RIGMAPPOAgent(**common_kwargs, multi_relation_global_residual_weight=0.0)

        actor_inputs = (
            torch.as_tensor(obs[None, ...], dtype=torch.float32),
            torch.as_tensor(graph["node_feat"][None, ...], dtype=torch.float32),
            torch.as_tensor(graph["edge_feat"][None, ...], dtype=torch.float32),
            torch.as_tensor(graph["role"][None, ...], dtype=torch.long),
            torch.as_tensor(graph["adj"][None, ...], dtype=torch.float32),
            env.num_agents,
        )
        relation_adj = torch.as_tensor(graph["relation_adj"][None, ...], dtype=torch.float32)
        with torch.no_grad():
            logits_enabled, attn_enabled, _ = enabled.actor(*actor_inputs, relation_adj=relation_adj)
            logits_disabled, attn_disabled, _ = disabled.actor(*actor_inputs, relation_adj=relation_adj)

        self.assertEqual(tuple(logits_enabled.shape), tuple(logits_disabled.shape))
        self.assertEqual(tuple(attn_enabled.shape), tuple(attn_disabled.shape))
        self.assertGreater(float(attn_enabled[:, 3].sum()), 0.0)
        torch.testing.assert_close(attn_disabled[:, 3], torch.zeros_like(attn_disabled[:, 3]))

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

    def test_task_support_relation_does_not_depend_on_hidden_target_state(self) -> None:
        env = UAVIntercept3DEnv(
            UAVIntercept3DConfig(
                strict_target_sensing=True,
                agent_target_info_bottleneck=True,
                seed=71,
            )
        )
        env.reset()
        env.detected_by[:] = 0.0
        env.comm_adj[:] = np.eye(env.config.num_blue, dtype=np.float32)
        env.message_age[:] = env.config.max_steps
        np.fill_diagonal(env.message_age, 0.0)
        env.target_cache_valid[:] = 0.0
        env.target_cache_confidence[:] = 0.0
        env.attack_window[:] = 0.0

        env.last_detected_target_pos = np.array([8_000.0, -1_000.0, 5_100.0], dtype=np.float32)
        graph_a = env._get_graph_obs()
        env.last_detected_target_pos = np.array([18_000.0, 6_000.0, 7_000.0], dtype=np.float32)
        graph_b = env._get_graph_obs()

        np.testing.assert_allclose(
            graph_a["relation_adj"][RELATION_TASK_SUPPORT],
            graph_b["relation_adj"][RELATION_TASK_SUPPORT],
            atol=1e-6,
            rtol=0.0,
        )

    def test_local_attack_window_requires_actor_visible_target_information(self) -> None:
        env = UAVIntercept3DEnv(
            UAVIntercept3DConfig(
                strict_target_sensing=True,
                agent_target_info_bottleneck=True,
                radar_dropout_prob=1.0,
                seed=75,
            )
        )
        env.reset()
        attacker = 2
        typ = env.config.blue_types[attacker]
        env.blue_pos[attacker] = np.array([0.0, 0.0, 5_000.0], dtype=np.float32)
        env.blue_heading[attacker] = 0.0
        env.blue_gamma[attacker] = 0.0
        env.blue_speed[attacker] = 270.0
        env.red_pos[0] = np.array([3_000.0, 0.0, 5_000.0], dtype=np.float32)
        env.red_speed[0] = 130.0
        env.red_heading[0] = 0.0
        env.red_gamma[0] = 0.0
        env.detected_by[:] = 0.0
        env.comm_adj[:] = np.eye(env.config.num_blue, dtype=np.float32)
        env.target_cache_valid[:] = 0.0
        env.target_cache_confidence[:] = 0.0

        env.attack_window[attacker] = float(env._in_attack_window(attacker, typ))
        env.local_attack_window[attacker] = float(env._in_local_attack_window(attacker, typ))
        obs = env._get_obs()
        graph = env._get_graph_obs()
        local_window_idx = OBS3D_FIELD_NAMES.index("local_attack_window")

        self.assertEqual(float(env.attack_window[attacker]), 1.0)
        self.assertEqual(float(env.local_attack_window[attacker]), 0.0)
        self.assertEqual(float(obs[attacker, local_window_idx]), 0.0)
        self.assertEqual(
            float(graph["relation_adj"][RELATION_TASK_SUPPORT, 1, attacker]),
            0.0,
        )

        env._write_target_cache(
            attacker,
            pos=env.red_pos[0].copy(),
            vel=np.array([130.0, 0.0, 0.0], dtype=np.float32),
            source=attacker,
            generation_step=env.step_count,
            delivery_step=env.step_count,
            hop_count=0,
            confidence=1.0,
            path=[attacker],
        )
        env.local_attack_window[attacker] = float(env._in_local_attack_window(attacker, typ))
        obs = env._get_obs()

        self.assertEqual(float(env.local_attack_window[attacker]), 1.0)
        self.assertEqual(float(obs[attacker, local_window_idx]), 1.0)

    def test_union_graph_does_not_use_potential_task_support_without_delivery(self) -> None:
        env = UAVIntercept3DEnv(
            UAVIntercept3DConfig(
                strict_target_sensing=True,
                agent_target_info_bottleneck=True,
                seed=73,
            )
        )
        env.reset()
        env.detected_by[:] = 0.0
        env.detected_by[0] = 1.0
        env.comm_adj[:] = np.eye(env.config.num_blue, dtype=np.float32)
        env.message_age[:] = env.config.max_steps
        np.fill_diagonal(env.message_age, 0.0)
        env.attack_window[:] = 0.0

        graph = env._get_graph_obs()
        off_diag_blue = ~np.eye(env.config.num_blue, dtype=bool)

        self.assertEqual(float(np.sum(graph["relation_adj"][RELATION_TASK_SUPPORT, : env.config.num_blue, : env.config.num_blue][off_diag_blue])), 0.0)
        self.assertEqual(float(np.sum(graph["relation_adj"][RELATION_COMMUNICATION, : env.config.num_blue, : env.config.num_blue][off_diag_blue])), 0.0)
        self.assertEqual(float(np.sum(graph["adj"][: env.config.num_blue, : env.config.num_blue][off_diag_blue])), 0.0)
        # Static role compatibility may still be present as an edge feature, but
        # it must remain masked out by relation_adj/adj until communication is delivered.
        self.assertGreater(float(np.sum(graph["edge_feat"][: env.config.num_blue, : env.config.num_blue, 13][off_diag_blue])), 0.0)

    def test_relay_failure_blocks_relay_originated_task_support(self) -> None:
        env = UAVIntercept3DEnv(
            UAVIntercept3DConfig(
                strict_target_sensing=True,
                agent_target_info_bottleneck=True,
                radar_dropout_prob=1.0,
                communication_range_scale=10.0,
                communication_dropout_prob=0.0,
                message_delay_steps=1,
                failed_blue_agent=1,
                node_failure_start_step=1,
                node_failure_duration_steps=10,
                seed=79,
            )
        )
        env.reset()
        relay = 1
        attacker = 2
        env.pending_messages.clear()
        env.pending_target_messages.clear()
        env.comm_adj[:] = np.eye(env.config.num_blue, dtype=np.float32)
        env.detected_by[:] = 0.0
        env.target_cache_valid[:] = 0.0
        env.target_cache_path = [[] for _ in range(env.config.num_blue)]
        env.step_count = 1
        env._write_target_cache(
            relay,
            pos=np.array([10_000.0, 0.0, 5_000.0], dtype=np.float32),
            vel=np.array([200.0, 0.0, 0.0], dtype=np.float32),
            source=0,
            generation_step=0,
            delivery_step=0,
            hop_count=1,
            confidence=0.9,
            path=[0, relay],
        )
        env.pending_messages.append((1, attacker, relay))
        env.pending_target_messages.append(
            {
                "deliver_step": 1,
                "receiver": attacker,
                "sender": relay,
                "pos": env.target_cache_pos[relay].copy(),
                "vel": env.target_cache_vel[relay].copy(),
                "source": int(env.target_cache_source[relay]),
                "generation_step": int(env.target_cache_generation_step[relay]),
                "hop_count": int(env.target_cache_hop_count[relay] + 1),
                "confidence": 0.8,
                "path": [0, relay, attacker],
            }
        )

        env._update_sensing_and_comm()
        graph = env._get_graph_obs()

        self.assertTrue(env._is_comm_failed(relay))
        self.assertEqual(float(env.comm_adj[attacker, relay]), 0.0)
        self.assertEqual(float(env.target_cache_valid[attacker]), 0.0)
        self.assertEqual(float(graph["relation_adj"][RELATION_COMMUNICATION, attacker, relay]), 0.0)
        self.assertEqual(float(graph["relation_adj"][RELATION_TASK_SUPPORT, attacker, relay]), 0.0)
        self.assertEqual(float(graph["adj"][attacker, relay]), 0.0)

    def test_relay_task_support_uses_relay_cache_not_teammate_private_state(self) -> None:
        env = UAVIntercept3DEnv(
            UAVIntercept3DConfig(
                strict_target_sensing=True,
                agent_target_info_bottleneck=True,
                seed=81,
            )
        )
        env.reset()
        scout = 0
        relay = 1
        attacker = 2
        env.detected_by[:] = 0.0
        env.detected_by[scout] = 1.0
        env.comm_adj[:] = np.eye(env.config.num_blue, dtype=np.float32)
        env.comm_adj[relay, scout] = 1.0
        env.comm_adj[attacker, relay] = 1.0
        env.message_age[:] = env.config.max_steps
        np.fill_diagonal(env.message_age, 0.0)
        env.target_cache_valid[:] = 0.0
        env.target_cache_confidence[:] = 0.0

        graph = env._get_graph_obs()
        self.assertEqual(float(graph["relation_adj"][RELATION_TASK_SUPPORT, attacker, relay]), 0.0)

        env._write_target_cache(
            relay,
            pos=np.array([10_000.0, 0.0, 5_000.0], dtype=np.float32),
            vel=np.array([200.0, 0.0, 0.0], dtype=np.float32),
            source=scout,
            generation_step=env.step_count,
            delivery_step=env.step_count,
            hop_count=1,
            confidence=0.9,
            path=[scout, relay],
        )
        graph = env._get_graph_obs()
        self.assertEqual(float(graph["relation_adj"][RELATION_TASK_SUPPORT, attacker, relay]), 1.0)

    def test_post_failure_recovery_steps_use_stable_closure_window_start(self) -> None:
        args = argparse.Namespace(
            failed_blue_agent=1,
            node_failure_start_step=10,
            node_failure_duration_steps=40,
            attack_hold_steps=4,
        )
        step_infos = [
            {
                "step": float(step),
                "chain_closed": float(step >= 23),
                "node_failure_active": float(10 <= step < 50),
                "tracking_rate": 1.0,
                "comm_connectivity": 1.0,
            }
            for step in range(1, 31)
        ]

        metrics = post_failure_recovery_metrics(step_infos, args)

        self.assertEqual(float(metrics["post_failure_first_chain_step"]), 23.0)
        self.assertEqual(float(metrics["post_failure_chain_recovered"]), 1.0)
        self.assertEqual(float(metrics["post_failure_chain_recovery_steps"]), 10.0)

    def test_post_failure_fresh_info_recovery_separates_stale_cache(self) -> None:
        args = argparse.Namespace(
            failed_blue_agent=1,
            node_failure_start_step=10,
            node_failure_duration_steps=40,
            attack_hold_steps=4,
        )
        base_infos = [
            {
                "step": float(step),
                "chain_closed": float(step >= 23),
                "node_failure_active": float(10 <= step < 50),
                "tracking_rate": 1.0,
                "comm_connectivity": 1.0,
                "attacker_info_attack_window": float(step >= 20),
                "attacker_window_cache_generation_step_max": 4.0,
                "attacker_window_cache_delivery_step_max": 5.0,
                "attacker_window_direct_info": 0.0,
                "attacker_window_comm_info": 1.0,
            }
            for step in range(1, 31)
        ]

        stale = post_failure_recovery_metrics(base_infos, args)
        self.assertEqual(float(stale["post_failure_chain_recovered"]), 1.0)
        self.assertEqual(float(stale["post_failure_fresh_info_recovered"]), 0.0)
        self.assertEqual(float(stale["post_failure_stale_cache_recovered"]), 1.0)

        post_delivered_old_infos = [dict(info) for info in base_infos]
        for info in post_delivered_old_infos:
            if float(info["step"]) >= 20.0:
                info["attacker_window_cache_delivery_step_max"] = 21.0
        old_delivered = post_failure_recovery_metrics(post_delivered_old_infos, args)
        self.assertEqual(float(old_delivered["post_failure_chain_recovered"]), 1.0)
        self.assertEqual(float(old_delivered["post_failure_fresh_info_recovered"]), 0.0)
        self.assertEqual(float(old_delivered["post_failure_post_delivered_old_info_recovered"]), 1.0)
        self.assertEqual(float(old_delivered["post_failure_stale_cache_recovered"]), 0.0)

        endpoint_only_fresh_infos = [dict(info) for info in base_infos]
        for info in endpoint_only_fresh_infos:
            if float(info["step"]) == 23.0:
                info["attacker_window_cache_generation_step_max"] = 23.0
                info["attacker_window_cache_delivery_step_max"] = 23.0
        endpoint_only = post_failure_recovery_metrics(endpoint_only_fresh_infos, args)
        self.assertEqual(float(endpoint_only["post_failure_chain_recovered"]), 1.0)
        self.assertEqual(float(endpoint_only["post_failure_fresh_info_recovered"]), 0.0)

        fresh_infos = [dict(info) for info in base_infos]
        for info in fresh_infos:
            if float(info["step"]) >= 20.0:
                info["attacker_window_cache_generation_step_max"] = 20.0
                info["attacker_window_cache_delivery_step_max"] = 21.0

        fresh = post_failure_recovery_metrics(fresh_infos, args)
        self.assertEqual(float(fresh["post_failure_chain_recovered"]), 1.0)
        self.assertEqual(float(fresh["post_failure_fresh_info_recovered"]), 1.0)
        self.assertEqual(float(fresh["post_failure_stale_cache_recovered"]), 0.0)
        self.assertEqual(float(fresh["post_failure_fresh_info_recovery_steps"]), 10.0)
        self.assertEqual(float(fresh["post_failure_fresh_comm_recovered"]), 1.0)

        maintained_infos = [dict(info) for info in fresh_infos]
        for info in maintained_infos:
            if float(info["step"]) >= 10.0:
                info["chain_closed"] = 1.0
        maintained = post_failure_recovery_metrics(maintained_infos, args)
        self.assertEqual(float(maintained["post_failure_chain_maintained"]), 1.0)
        self.assertEqual(float(maintained["post_failure_fresh_info_recovered"]), 0.0)
        self.assertEqual(float(maintained["post_failure_fresh_info_acquired_without_prior_loss"]), 1.0)

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

    def test_centralized_critic_conditions_on_agent_role(self) -> None:
        torch.manual_seed(17)
        env = UAVIntercept3DEnv(UAVIntercept3DConfig(seed=17))
        _, share_obs, graph = env.reset()
        num_roles = max(4, int(np.max(graph["role"])) + 1)
        agent = RIGMAPPOAgent(
            obs_dim=env.obs_dim,
            node_feat_dim=graph["node_feat"].shape[-1],
            edge_feat_dim=graph["edge_feat"].shape[-1],
            share_obs_dim=share_obs.shape[-1],
            action_dim=env.action_dim,
            num_agents=env.num_agents,
            num_roles=num_roles,
            hidden_dim=32,
            role_dim=4,
            intent_dim=4,
            graph_encoder="multi_relation",
            use_intent_context=False,
        )

        captured_inputs: list[torch.Tensor] = []

        def _capture_critic_input(_module, inputs, _output) -> None:
            captured_inputs.append(inputs[0].detach().clone())

        handle = agent.critic.net[0].register_forward_hook(_capture_critic_input)
        try:
            role = torch.as_tensor(graph["role"][None, :], dtype=torch.long)
            share = torch.as_tensor(share_obs[None, :, :], dtype=torch.float32)
            values = agent.critic_value(share, role)
        finally:
            handle.remove()

        self.assertEqual(tuple(values.shape), (1, env.num_agents))
        self.assertEqual(captured_inputs[0].shape[-1], share_obs.shape[-1] + num_roles)
        role_tail = captured_inputs[0][0, :, share_obs.shape[-1] :]
        expected = torch.nn.functional.one_hot(role[0, : env.num_agents], num_classes=num_roles).float()
        torch.testing.assert_close(role_tail, expected)

    def test_no_role_identity_masks_explicit_actor_role_features(self) -> None:
        torch.manual_seed(19)
        env = UAVIntercept3DEnv(UAVIntercept3DConfig(seed=19))
        obs, share_obs, graph = env.reset()
        num_roles = max(4, int(np.max(graph["role"])) + 1)
        agent = RIGMAPPOAgent(
            obs_dim=env.obs_dim,
            node_feat_dim=graph["node_feat"].shape[-1],
            edge_feat_dim=graph["edge_feat"].shape[-1],
            share_obs_dim=share_obs.shape[-1],
            action_dim=env.action_dim,
            num_agents=env.num_agents,
            num_roles=num_roles,
            hidden_dim=32,
            role_dim=4,
            intent_dim=4,
            graph_encoder="multi_relation",
            graph_input_ablation="no_role_identity",
            use_intent_context=False,
        )
        agent.eval()

        captured_obs: list[torch.Tensor] = []
        captured_node_and_role: list[torch.Tensor] = []

        def _capture_obs_input(_module, inputs, _output) -> None:
            captured_obs.append(inputs[0].detach().clone())

        def _capture_node_input(_module, inputs, _output) -> None:
            captured_node_and_role.append(inputs[0].detach().clone())

        obs_handle = agent.actor.obs_encoder[0].register_forward_hook(_capture_obs_input)
        node_handle = agent.actor.input[0].register_forward_hook(_capture_node_input)
        try:
            with torch.no_grad():
                agent.get_action_and_value(
                    torch.as_tensor(obs[None, :, :], dtype=torch.float32),
                    torch.as_tensor(graph["node_feat"][None, :, :], dtype=torch.float32),
                    torch.as_tensor(graph["edge_feat"][None, :, :, :], dtype=torch.float32),
                    torch.as_tensor(graph["role"][None, :], dtype=torch.long),
                    torch.as_tensor(graph["adj"][None, :, :], dtype=torch.float32),
                    torch.as_tensor(share_obs[None, :, :], dtype=torch.float32),
                    relation_adj=torch.as_tensor(graph["relation_adj"][None, :, :, :], dtype=torch.float32),
                    deterministic=True,
                )
        finally:
            obs_handle.remove()
            node_handle.remove()

        role_obs = captured_obs[0][..., OBS3D_ROLE_IDENTITY_SLICE]
        torch.testing.assert_close(role_obs, torch.zeros_like(role_obs))
        ability_slice = captured_obs[0][..., 21:24]
        self.assertGreater(float(torch.abs(ability_slice).sum()), 0.0)
        node_input = captured_node_and_role[0]
        node_feat_dim = graph["node_feat"].shape[-1]
        torch.testing.assert_close(node_input[..., 11:16], torch.zeros_like(node_input[..., 11:16]))
        role_embedding_input = node_input[..., node_feat_dim:]
        torch.testing.assert_close(
            role_embedding_input,
            role_embedding_input[:, :1, :].expand_as(role_embedding_input),
        )

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

    def test_actor_graph_does_not_include_global_attack_hold_progress(self) -> None:
        env = UAVIntercept3DEnv(
            UAVIntercept3DConfig(
                strict_target_sensing=True,
                agent_target_info_bottleneck=True,
                seed=41,
            )
        )
        env.reset()
        env.attack_hold = 0
        graph_before = env._get_graph_obs()

        env.attack_hold = env.config.attack_hold_steps
        graph_after = env._get_graph_obs()

        self.assertEqual(graph_before["edge_feat"].shape[-1], EDGE3D_FEAT_DIM)
        np.testing.assert_allclose(graph_before["node_feat"], graph_after["node_feat"], atol=1e-6, rtol=0.0)
        np.testing.assert_allclose(graph_before["edge_feat"], graph_after["edge_feat"], atol=1e-6, rtol=0.0)
        np.testing.assert_allclose(graph_before["adj"], graph_after["adj"], atol=1e-6, rtol=0.0)
        np.testing.assert_allclose(graph_before["relation_adj"], graph_after["relation_adj"], atol=1e-6, rtol=0.0)

    def test_actor_logits_do_not_change_with_global_attack_hold(self) -> None:
        torch.manual_seed(41)
        env = UAVIntercept3DEnv(
            UAVIntercept3DConfig(
                strict_target_sensing=True,
                agent_target_info_bottleneck=True,
                seed=41,
            )
        )
        obs, share_obs, graph = env.reset()
        agent = self._make_multi_relation_agent(env, share_obs, graph, seed=41)

        env.attack_hold = 0
        logits_before = self._actor_logits(env, agent)
        env.attack_hold = env.config.attack_hold_steps
        logits_after = self._actor_logits(env, agent)

        np.testing.assert_allclose(logits_before, logits_after, atol=1e-6, rtol=0.0)

    def test_unreachable_target_cache_does_not_change_attacker_logits(self) -> None:
        torch.manual_seed(43)
        env = UAVIntercept3DEnv(
            UAVIntercept3DConfig(
                strict_target_sensing=True,
                agent_target_info_bottleneck=True,
                seed=43,
            )
        )
        obs, share_obs, graph = env.reset()
        agent = self._make_multi_relation_agent(env, share_obs, graph, seed=43)
        env.detected_by[:] = 0.0
        env.comm_adj[:] = np.eye(env.config.num_blue, dtype=np.float32)
        env.message_age[:] = env.config.max_steps
        np.fill_diagonal(env.message_age, 0.0)
        env.target_cache_valid[:] = 0.0
        env.target_cache_confidence[:] = 0.0
        env.target_cache_path = [[] for _ in range(env.config.num_blue)]

        logits_before = self._actor_logits(env, agent)[2]
        env._write_target_cache(
            0,
            pos=np.array([18_000.0, 6_000.0, 6_500.0], dtype=np.float32),
            vel=np.array([120.0, 70.0, 10.0], dtype=np.float32),
            source=0,
            generation_step=env.step_count,
            delivery_step=env.step_count,
            hop_count=0,
            confidence=1.0,
            path=[0],
        )
        logits_after = self._actor_logits(env, agent)[2]

        np.testing.assert_allclose(logits_before, logits_after, atol=1e-6, rtol=0.0)

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
        env.last_detected_target_pos = env.red_pos[0].copy()
        env.last_detected_target_vel = np.array([200.0, 0.0, 0.0], dtype=np.float32)
        env._write_target_cache(
            0,
            pos=env.last_detected_target_pos,
            vel=env.last_detected_target_vel,
            source=0,
            generation_step=env.step_count,
            delivery_step=env.step_count,
            hop_count=0,
            confidence=1.0,
            path=[0],
        )
        graph_detected = env._get_graph_obs()
        np.testing.assert_allclose(
            graph_a["node_feat"][target_node],
            graph_detected["node_feat"][target_node],
            atol=1e-6,
            rtol=0.0,
        )
        np.testing.assert_allclose(
            graph_a["edge_feat"][:, target_node, :11],
            graph_detected["edge_feat"][:, target_node, :11],
            atol=1e-6,
            rtol=0.0,
        )

        obs_detected = env._get_obs()
        rel_x_idx = OBS3D_FIELD_NAMES.index("target_rel_x_norm")
        expected_rel_x = (env.red_pos[0, 0] - env.blue_pos[0, 0]) / env.config.world_radius
        self.assertAlmostEqual(float(obs_detected[0, rel_x_idx]), float(expected_rel_x), places=6)

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

    def test_post_failure_rates_are_zero_when_episode_ends_before_failure(self) -> None:
        args = argparse.Namespace(
            failed_blue_agent=1,
            node_failure_start_step=40,
            node_failure_duration_steps=80,
        )
        metrics = post_failure_recovery_metrics(
            [
                {
                    "step": 34.0,
                    "node_failure_active": 0.0,
                    "chain_closed": 0.0,
                    "tracking_rate": 1.0,
                    "comm_connectivity": 1.0,
                }
            ],
            args,
        )

        self.assertEqual(float(metrics["post_failure_chain_recovered"]), 0.0)
        self.assertEqual(float(metrics["chain_closed_during_failure_rate"]), 0.0)
        self.assertEqual(float(metrics["tracking_during_failure_rate"]), 0.0)
        self.assertEqual(float(metrics["connectivity_during_failure"]), 0.0)

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

    def test_weaving_tiny_is_lower_amplitude_than_weaving_mild(self) -> None:
        def one_step_heading_delta(target_policy: str) -> float:
            env = UAVIntercept3DEnv(UAVIntercept3DConfig(target_policy=target_policy, seed=3))
            env.reset()
            env.blue_pos[:] = np.array(
                [
                    [-1_000.0, 0.0, 5_000.0],
                    [0.0, 0.0, 5_000.0],
                    [1_000.0, 0.0, 5_000.0],
                ],
                dtype=np.float32,
            )
            env.red_pos[0] = np.array([10_000.0, 0.0, 5_000.0], dtype=np.float32)
            env.red_heading[0] = 0.0
            env.red_gamma[0] = 0.0
            env.step_count = 8

            env._move_red()
            return abs(float(env.red_heading[0]))

        tiny_delta = one_step_heading_delta("weaving_tiny")
        mild_delta = one_step_heading_delta("weaving_mild")

        self.assertGreater(tiny_delta, 0.0)
        self.assertLess(tiny_delta, mild_delta)

    def test_attack_geometry_score_prefers_near_attack_geometry(self) -> None:
        env = UAVIntercept3DEnv(UAVIntercept3DConfig(seed=51))
        env.reset()
        attacker = 2
        env.blue_pos[attacker] = np.array([0.0, 0.0, 5_000.0], dtype=np.float32)
        env.blue_heading[attacker] = 0.0
        env.blue_gamma[attacker] = 0.0
        env.blue_speed[attacker] = 270.0
        env.red_speed[0] = 130.0
        env.red_heading[0] = 0.0
        env.red_gamma[0] = 0.0

        env.red_pos[0] = np.array([3_000.0, 0.0, 5_000.0], dtype=np.float32)
        near_score = env._attack_geometry_score()
        env.red_pos[0] = np.array([20_000.0, 0.0, 5_000.0], dtype=np.float32)
        far_score = env._attack_geometry_score()

        self.assertGreater(near_score, 0.5)
        self.assertGreater(near_score, far_score)

    def test_attack_geometry_reward_weight_is_opt_in(self) -> None:
        env = UAVIntercept3DEnv(UAVIntercept3DConfig(seed=52))
        env.reset()
        attacker = 2
        env.blue_pos[attacker] = np.array([0.0, 0.0, 5_000.0], dtype=np.float32)
        env.blue_heading[attacker] = 0.0
        env.blue_gamma[attacker] = 0.0
        env.blue_speed[attacker] = 270.0
        env.red_pos[0] = np.array([3_000.0, 0.0, 5_000.0], dtype=np.float32)
        env.red_speed[0] = 130.0
        env.red_heading[0] = 0.0
        env.red_gamma[0] = 0.0
        cur_range = env._mean_target_range()

        env.config.attack_geometry_reward_weight = 0.0
        reward_without = float(env._compute_rewards(cur_range, cur_range, 0.0, 0.0, 0.0, 0.0)[attacker, 0])
        env.config.attack_geometry_reward_weight = 0.5
        reward_with = float(env._compute_rewards(cur_range, cur_range, 0.0, 0.0, 0.0, 0.0)[attacker, 0])

        self.assertGreater(reward_with, reward_without)

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

    def _make_multi_relation_agent(
        self,
        env: UAVIntercept3DEnv,
        share_obs: np.ndarray,
        graph: dict[str, np.ndarray],
        *,
        seed: int,
    ) -> RIGMAPPOAgent:
        torch.manual_seed(seed)
        num_roles = max(5, int(np.max(graph["role"])) + 1)
        agent = RIGMAPPOAgent(
            obs_dim=env.obs_dim,
            node_feat_dim=graph["node_feat"].shape[-1],
            edge_feat_dim=graph["edge_feat"].shape[-1],
            share_obs_dim=share_obs.shape[-1],
            action_dim=env.action_dim,
            num_agents=env.num_agents,
            num_roles=num_roles,
            hidden_dim=32,
            role_dim=4,
            intent_dim=4,
            graph_encoder="multi_relation",
            use_intent_context=False,
        )
        agent.eval()
        return agent

    def _actor_logits(self, env: UAVIntercept3DEnv, agent: RIGMAPPOAgent) -> np.ndarray:
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
        return logits[0].numpy()


if __name__ == "__main__":
    unittest.main()
