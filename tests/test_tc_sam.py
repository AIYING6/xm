"""Training-free unit tests for the frozen actor-only TC-SAM PPO update."""
from __future__ import annotations

import copy
from pathlib import Path
import tempfile

import numpy as np
import torch

from algorithms.ri_gmappo.simple_ri_gmappo import (
    RIGMAPPOAgent,
    RIGMAPPOConfig,
    _restore_parameter_copies,
    _sam_perturbations,
    load_training_checkpoint,
    make_optimizer,
    save_training_checkpoint,
    update_policy,
)


def agent() -> RIGMAPPOAgent:
    return RIGMAPPOAgent(
        obs_dim=34, node_feat_dim=20, edge_feat_dim=17, share_obs_dim=47,
        action_dim=27, num_agents=3, num_roles=5, hidden_dim=115,
        role_dim=8, intent_dim=8, graph_encoder="single", role_gate_mode="none",
        use_intent_context=False,
    )


def config(*, sam_enabled: bool, rho: float = 0.05) -> RIGMAPPOConfig:
    return RIGMAPPOConfig(
        env_name="3d_intercept", num_envs=4, rollout_steps=64, minibatch_graphs=256,
        ppo_epochs=1, graph_encoder="single", hidden_dim=115, role_dim=8, intent_dim=8,
        role_gate_mode="none", actor_gradient_mode="utr", fixed_stratified_topology_sampler=True,
        fixed_stratified_topology_sampler_seed=11, sam_enabled=sam_enabled, sam_rho=rho,
        critic_warmup_updates=0, evaluation_enabled=False, device="cpu",
    )


def batch() -> dict:
    generator = torch.Generator().manual_seed(123)
    steps, envs, agents, nodes = 64, 4, 3, 4
    adj = torch.ones(steps, envs, nodes, nodes)
    return {
        "obs": torch.randn(steps, envs, agents, 34, generator=generator).numpy(),
        "node_feat": torch.randn(steps, envs, nodes, 20, generator=generator).numpy(),
        "edge_feat": torch.randn(steps, envs, nodes, nodes, 17, generator=generator).numpy(),
        "role": torch.tensor([0, 1, 2, 4]).view(1, 1, nodes).expand(steps, envs, nodes).numpy(),
        "adj": adj.numpy(),
        "relation_adj": torch.ones(steps, envs, 3, nodes, nodes).numpy(),
        "intent_label": torch.randint(0, 4, (steps, envs, 1), generator=generator).numpy(),
        "share_obs": torch.randn(steps, envs, agents, 47, generator=generator).numpy(),
        "actions": torch.randint(0, 27, (steps, envs, agents), generator=generator).numpy(),
        "logp": torch.randn(steps, envs, agents, generator=generator).mul_(0.01).numpy(),
        "advantages": torch.randn(steps, envs, agents, generator=generator).numpy(),
        "returns": torch.randn(steps, envs, agents, generator=generator).numpy(),
        "condition_is_nominal": np.asarray([[True, True, False, False]] * steps),
        "has_intent_label": True,
    }


def parameters(model: torch.nn.Module) -> list[torch.Tensor]:
    return [parameter.detach().clone() for parameter in model.parameters()]


def test_tc_sam_parameter_count_and_inference_identity():
    torch.manual_seed(4)
    left, right = agent().eval(), agent().eval()
    right.load_state_dict(left.state_dict())
    assert sum(parameter.numel() for parameter in left.parameters()) == 116_728
    state = batch()
    inputs = (
        torch.as_tensor(state["obs"][0, 0][None]), torch.as_tensor(state["node_feat"][0, 0][None]),
        torch.as_tensor(state["edge_feat"][0, 0][None]), torch.as_tensor(state["role"][0, 0][None]),
        torch.as_tensor(state["adj"][0, 0][None]), torch.as_tensor(state["share_obs"][0, 0][None]),
    )
    with torch.no_grad():
        left_out = left.get_action_and_value(*inputs, deterministic=True)[0]
        right_out = right.get_action_and_value(*inputs, deterministic=True)[0]
    assert torch.equal(left_out, right_out)


def test_sam_perturbation_norm_and_exact_restore():
    torch.manual_seed(5)
    model = agent()
    actor_parameters = list(model.actor.parameters())
    gradients = [torch.randn_like(parameter) for parameter in actor_parameters]
    perturbations, _gradient_norm, perturbation_norm = _sam_perturbations(gradients, rho=0.05, epsilon=1e-12)
    assert torch.allclose(perturbation_norm, torch.tensor(0.05), atol=1e-6, rtol=1e-6)
    originals = [parameter.detach().clone() for parameter in actor_parameters]
    with torch.no_grad():
        for parameter, perturbation in zip(actor_parameters, perturbations):
            parameter.add_(perturbation)
    _restore_parameter_copies(actor_parameters, originals)
    assert all(torch.equal(parameter, original) for parameter, original in zip(actor_parameters, originals))


def test_rho_zero_reduces_to_utr_update_within_tolerance():
    torch.manual_seed(6)
    baseline, sam = agent(), agent()
    sam.load_state_dict(baseline.state_dict())
    baseline_optimizer, sam_optimizer = make_optimizer(baseline, config(sam_enabled=False)), make_optimizer(sam, config(sam_enabled=True, rho=0.0))
    state = batch()
    torch.manual_seed(77)
    baseline_info = update_policy(baseline, baseline_optimizer, copy.deepcopy(state), config(sam_enabled=False), torch.device("cpu"), 1)
    torch.manual_seed(77)
    sam_info = update_policy(sam, sam_optimizer, copy.deepcopy(state), config(sam_enabled=True, rho=0.0), torch.device("cpu"), 1)
    for left, right in zip(parameters(baseline), parameters(sam)):
        torch.testing.assert_close(left, right, rtol=2e-6, atol=2e-7)
    assert sam_info["sam_enabled"] == 1.0
    assert sam_info["sam_perturbation_norm"] == 0.0
    assert np.isfinite(baseline_info["loss"]) and np.isfinite(sam_info["loss"])


def test_sam_update_is_finite_and_optimizer_steps_once():
    torch.manual_seed(8)
    model, cfg = agent(), config(sam_enabled=True)
    optimizer = make_optimizer(model, cfg)
    info = update_policy(model, optimizer, batch(), cfg, torch.device("cpu"), 1)
    assert all(np.isfinite(float(value)) for key, value in info.items() if isinstance(value, (float, int)))
    assert info["sam_perturbation_norm"] > 0.0
    assert info["sam_second_gradient_norm"] > 0.0
    assert all(
        row["sam_first_minibatch_hash"]
        and row["sam_first_minibatch_hash"] == row["sam_second_minibatch_hash"]
        for row in info["actor_gradient_rows"]
    )
    state_steps = [int(state["step"].item()) for state in optimizer.state.values() if "step" in state]
    assert state_steps and set(state_steps) == {1}


def test_sam_checkpoint_reload_next_update_is_exact():
    torch.manual_seed(12)
    cfg = config(sam_enabled=True)
    reference, resumed = agent(), agent()
    resumed.load_state_dict(reference.state_dict())
    reference_optimizer, resumed_optimizer = make_optimizer(reference, cfg), make_optimizer(resumed, cfg)
    state = batch()
    torch.manual_seed(88)
    update_policy(reference, reference_optimizer, copy.deepcopy(state), cfg, torch.device("cpu"), 1)
    torch.manual_seed(88)
    update_policy(resumed, resumed_optimizer, copy.deepcopy(state), cfg, torch.device("cpu"), 1)
    with tempfile.TemporaryDirectory() as directory:
        checkpoint = Path(directory) / "synthetic_sam.pt"
        save_training_checkpoint(checkpoint, resumed, resumed_optimizer, update=1)
        loaded = agent()
        loaded_optimizer = make_optimizer(loaded, cfg)
        load_training_checkpoint(loaded, loaded_optimizer, str(checkpoint), torch.device("cpu"))
        next_state = batch()
        torch.manual_seed(99)
        update_policy(reference, reference_optimizer, copy.deepcopy(next_state), cfg, torch.device("cpu"), 2)
        torch.manual_seed(99)
        update_policy(loaded, loaded_optimizer, copy.deepcopy(next_state), cfg, torch.device("cpu"), 2)
        for left, right in zip(parameters(reference), parameters(loaded)):
            assert torch.equal(left, right)
