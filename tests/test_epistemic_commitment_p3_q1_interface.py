from __future__ import annotations

import torch

from algorithms.epistemic_commitment_p3_policy import (
    P3CentralCritic,
    P3PolicyConfig,
    P3RecurrentActor,
)
from scripts.audit_epistemic_commitment_p3_q1_interface import audit, load_freeze


def test_q1_freeze_budget_and_scope_are_exact() -> None:
    freeze = load_freeze()
    assert freeze["method"] == "recurrent_mappo"
    assert freeze["training_seeds"] == [98311, 98312, 98313]
    assert freeze["episodes_per_update"] * freeze["updates_per_run"] == freeze["episodes_per_run"]
    assert freeze["episodes_per_run"] * freeze["physical_steps_per_episode"] == 499_968
    assert set(freeze["training_cells"]).isdisjoint(freeze["heldout_cells_evaluation_only"])
    assert freeze["training_authorized"] is False


def test_q1_policy_shapes_and_role_mask_contract() -> None:
    config = P3PolicyConfig()
    actor = P3RecurrentActor(config)
    critic = P3CentralCritic(config)
    output = actor(torch.zeros((3, 8, config.observation_dim)))
    assert output["mode_logits"].shape == (3, 8, 3)
    assert output["guidance_mean"].shape == (3, 8, 2)
    assert output["guidance_log_std"].shape == (3, 8, 2)
    assert output["hidden"].shape == (1, 3, config.actor_hidden_dim)
    assert critic(torch.zeros((8, config.critic_input_dim))).shape == (8,)


def test_q1_one_update_interface_audit_passes() -> None:
    report = audit()
    assert report["verdict"] == "P3_Q1_INTERFACE_PASS_TO_RUNNER_IMPLEMENTATION"
    assert all(report["checks"].values())
    assert report["scientific_training_started"] is False
    assert report["technical_smoke_ppo_updates"] == 1

