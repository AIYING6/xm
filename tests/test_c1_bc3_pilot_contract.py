"""Contract tests for the C1 BC3 identifiability pilot.

These tests avoid the optional LBF dependency.  They only test the frozen
posterior feature and its four model input paths.
"""
from __future__ import annotations

import torch

from algorithms.c1_bc3_mappo import C1PilotMAPPO, update_capability_posterior


def test_all_arms_have_matched_output_shapes() -> None:
    obs = torch.zeros((2, 2, 12))
    critic = torch.zeros((2, 2, 22))
    masks = torch.ones((2, 2, 6))
    posterior = torch.full((2, 2), 0.5)
    for arm in ("ff_mappo", "recurrent_mappo", "bc3_mappo", "shuffled_bc3_mappo"):
        model = C1PilotMAPPO(obs_dim=12, critic_dim=22, action_dim=6, arm=arm)
        memory = model.initial_memory(2, 2, device="cpu") if model.uses_memory else None
        distribution, next_memory = model.action_distribution(
            obs, masks, memory=memory, posterior=posterior if model.uses_posterior else None
        )
        assert distribution.logits.shape == (2, 2, 6)
        assert model.value(critic).shape == (2, 2)
        assert (next_memory is not None) is model.uses_memory


def test_posterior_uses_only_a_public_joint_receipt_and_public_outcome() -> None:
    prior = torch.full((2, 2), 0.5)
    no_attempt = update_capability_posterior(
        prior, joint_load_receipt=torch.zeros_like(prior), public_team_reward=torch.zeros_like(prior)
    )
    failed_attempt = update_capability_posterior(
        prior, joint_load_receipt=torch.ones_like(prior), public_team_reward=torch.zeros_like(prior)
    )
    successful_attempt = update_capability_posterior(
        prior, joint_load_receipt=torch.ones_like(prior), public_team_reward=torch.ones_like(prior)
    )
    assert torch.equal(no_attempt, prior)
    assert torch.all(failed_attempt < prior)
    assert torch.all(successful_attempt > prior)
