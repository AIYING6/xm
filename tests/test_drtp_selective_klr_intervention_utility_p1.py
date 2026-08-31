"""Rollout-free invariants for the P1 observational KL alarm hook."""
from __future__ import annotations

import copy

import numpy as np
import torch

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOConfig, make_optimizer, update_policy
from tests.test_drtp_stable_v2_kl_guard import assert_nested_equal, on_policy_batch
from tests.test_tc_sam import agent, parameters


def cfg() -> RIGMAPPOConfig:
    return RIGMAPPOConfig(
        env_name="3d_intercept", num_envs=4, rollout_steps=64, minibatch_graphs=256,
        ppo_epochs=4, graph_encoder="single", hidden_dim=115, role_dim=8, intent_dim=8,
        role_gate_mode="none", actor_gradient_mode="standard", evaluation_enabled=False,
        device="cpu", lr=0.5, clip_coef=0.2, max_grad_norm=0.5,
        target_kl=None, policy_update_guard_mode="none",
        intervention_utility_audit_enabled=True, intervention_utility_alarm_kl=0.02,
        intervention_utility_probe_count=4,
    )


def test_p1_alarm_callback_is_observational_and_captures_pre_post_state():
    torch.manual_seed(8801); np.random.seed(8801)
    base, model = agent(), agent(); model.load_state_dict(base.state_dict())
    optimizer = make_optimizer(model, cfg())
    events = []

    def callback(event):
        # Mimic a writer which reads snapshots but must not alter the official state.
        events.append(event)

    info = update_policy(model, optimizer, on_policy_batch(base), cfg(), torch.device("cpu"), 1, intervention_utility_callback=callback)
    assert info["intervention_utility_alarm_count"] == len(events)
    assert len(events) >= 1
    event = events[0]
    assert event["alarm_kl"] > event["alarm_threshold"] == 0.02
    assert "model_state" in event["pre_state"] and "optimizer_state" in event["pre_state"]
    assert "post_model_state" in event and "post_optimizer_state" in event
    # Later PPO epochs may legitimately change the final model, but the
    # callback receives a genuine attempted update rather than an alias of the
    # pre-step actor state.
    assert any(
        not torch.equal(event["pre_state"]["actor_state"][key], event["post_actor_state"][key])
        for key in event["pre_state"]["actor_state"]
    )


def test_p1_default_off_preserves_the_original_ppo_path():
    torch.manual_seed(8802); np.random.seed(8802)
    base, left, right = agent(), agent(), agent()
    left.load_state_dict(base.state_dict()); right.load_state_dict(base.state_dict())
    disabled = cfg(); disabled.intervention_utility_audit_enabled = False; disabled.intervention_utility_alarm_kl = None
    left_optimizer, right_optimizer = make_optimizer(left, disabled), make_optimizer(right, disabled)
    batch = on_policy_batch(base)
    np.random.seed(8803); update_policy(left, left_optimizer, copy.deepcopy(batch), disabled, torch.device("cpu"), 1)
    np.random.seed(8803); update_policy(right, right_optimizer, copy.deepcopy(batch), disabled, torch.device("cpu"), 1)
    assert all(torch.equal(a, b) for a, b in zip(parameters(left), parameters(right)))
    assert_nested_equal(left_optimizer.state_dict(), right_optimizer.state_dict())
