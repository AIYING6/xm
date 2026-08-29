"""Synthetic, rollout-free tests for the opt-in Stable-v2 KL rollback guard."""
from __future__ import annotations

import copy
from dataclasses import replace
from pathlib import Path
import tempfile

import numpy as np
import torch

from algorithms.ri_gmappo.simple_ri_gmappo import (
    RIGMAPPOConfig,
    load_training_checkpoint,
    make_optimizer,
    save_training_checkpoint,
    update_policy,
)
from tests.test_tc_sam import agent, batch, parameters


def guard_config(*, lr: float, epochs: int = 1, enabled: bool = True) -> RIGMAPPOConfig:
    return RIGMAPPOConfig(
        env_name="3d_intercept", num_envs=4, rollout_steps=64, minibatch_graphs=256,
        ppo_epochs=epochs, graph_encoder="single", hidden_dim=115, role_dim=8, intent_dim=8,
        role_gate_mode="none", actor_gradient_mode="standard", critic_warmup_updates=0,
        evaluation_enabled=False, device="cpu", lr=lr, clip_coef=0.2, max_grad_norm=0.5,
        target_kl=0.02 if enabled else None,
        policy_update_guard_mode="post_step_actor_rollback" if enabled else "none",
    )


def on_policy_batch(model) -> dict:
    state = batch()
    steps, envs, agents = state["actions"].shape
    graphs = steps * envs
    with torch.no_grad():
        _, logp, _, _, _, _, _ = model.get_action_and_value(
            torch.as_tensor(state["obs"].reshape(graphs, agents, -1)),
            torch.as_tensor(state["node_feat"].reshape(graphs, *state["node_feat"].shape[2:])),
            torch.as_tensor(state["edge_feat"].reshape(graphs, *state["edge_feat"].shape[2:])),
            torch.as_tensor(state["role"].reshape(graphs, *state["role"].shape[2:])),
            torch.as_tensor(state["adj"].reshape(graphs, *state["adj"].shape[2:])),
            torch.as_tensor(state["share_obs"].reshape(graphs, agents, -1)),
            relation_adj=torch.as_tensor(
                state["relation_adj"].reshape(graphs, *state["relation_adj"].shape[2:])
            ),
            action=torch.as_tensor(state["actions"].reshape(graphs, agents)),
            intent_label=torch.as_tensor(state["intent_label"].reshape(graphs, -1)),
        )
    state["logp"] = logp.reshape(steps, envs, agents).cpu().numpy()
    return state


def module_parameters(module) -> list[torch.Tensor]:
    return [parameter.detach().clone() for parameter in module.parameters()]


def optimizer_parameter_state(optimizer, module) -> dict[str, dict]:
    named = dict(module.named_parameters())
    return {
        name: copy.deepcopy(optimizer.state[parameter])
        for name, parameter in named.items()
        if parameter in optimizer.state
    }


def assert_nested_equal(left, right) -> None:
    assert type(left) is type(right)
    if isinstance(left, torch.Tensor):
        assert torch.equal(left, right)
    elif isinstance(left, dict):
        assert left.keys() == right.keys()
        for key in left:
            assert_nested_equal(left[key], right[key])
    else:
        assert left == right


def test_guard_accepts_small_step_and_exactly_preserves_original_update():
    torch.manual_seed(4101)
    np.random.seed(4101)
    base = agent()
    guarded, original = agent(), agent()
    guarded.load_state_dict(base.state_dict())
    original.load_state_dict(base.state_dict())
    guarded_cfg = guard_config(lr=1e-6, epochs=4)
    original_cfg = guard_config(lr=1e-6, epochs=4, enabled=False)
    guarded_optimizer = make_optimizer(guarded, guarded_cfg)
    original_optimizer = make_optimizer(original, original_cfg)
    state = on_policy_batch(base)
    np.random.seed(4111)
    info = update_policy(
        guarded, guarded_optimizer, copy.deepcopy(state), guarded_cfg, torch.device("cpu"), 1
    )
    np.random.seed(4111)
    update_policy(
        original, original_optimizer, copy.deepcopy(state), original_cfg, torch.device("cpu"), 1
    )
    assert info["policy_guard_triggered"] == 0.0
    assert info["policy_steps_attempted"] == 4
    assert info["policy_steps_accepted"] == 4
    assert 0.0 <= info["policy_kl_post_step"] <= guarded_cfg.target_kl
    assert info["actor_accepted_update_l2"] > 0.0
    assert all(torch.equal(left, right) for left, right in zip(parameters(guarded), parameters(original)))
    assert_nested_equal(guarded_optimizer.state_dict(), original_optimizer.state_dict())


def test_guard_rolls_back_actor_and_actor_adam_but_retains_critic_step():
    torch.manual_seed(4102)
    np.random.seed(4102)
    model = agent()
    cfg = guard_config(lr=1e-6, epochs=1)
    optimizer = make_optimizer(model, cfg)
    first_state = on_policy_batch(model)
    update_policy(model, optimizer, first_state, cfg, torch.device("cpu"), 1)
    actor_before = module_parameters(model.actor)
    critic_before = module_parameters(model.critic)
    actor_adam_before = optimizer_parameter_state(optimizer, model.actor)
    optimizer.param_groups[0]["lr"] = 0.5
    info = update_policy(model, optimizer, on_policy_batch(model), replace(cfg, ppo_epochs=4), torch.device("cpu"), 2)
    assert info["policy_guard_triggered"] == 1.0
    assert info["policy_guard_reason"] == "post_step_kl_exceeded"
    assert info["policy_guard_epoch"] == 1
    assert info["ppo_epochs_ran"] == 1
    assert info["policy_steps_attempted"] == 1
    assert info["policy_steps_accepted"] == 0
    assert info["policy_kl_attempted_max"] > cfg.target_kl
    assert info["policy_kl_post_step"] <= cfg.target_kl
    assert info["actor_rollback_l2"] > 0.0
    assert info["actor_optimizer_state_restored"] == 1.0
    assert info["critic_step_retained_after_actor_rollback"] == 1.0
    assert all(torch.equal(left, right) for left, right in zip(actor_before, module_parameters(model.actor)))
    assert any(not torch.equal(left, right) for left, right in zip(critic_before, module_parameters(model.critic)))
    assert_nested_equal(actor_adam_before, optimizer_parameter_state(optimizer, model.actor))
    assert all(int(optimizer.state[parameter]["step"].item()) == 2 for parameter in model.critic.parameters())


def test_guard_nonfinite_step_restores_full_transaction():
    torch.manual_seed(4108)
    model = agent()
    cfg = guard_config(lr=1e-6)
    optimizer = make_optimizer(model, cfg)
    model_before = copy.deepcopy(model.state_dict())
    optimizer_before = copy.deepcopy(optimizer.state_dict())
    original_step = optimizer.step

    def nonfinite_step(*args, **kwargs):
        result = original_step(*args, **kwargs)
        with torch.no_grad():
            next(model.actor.parameters()).view(-1)[0] = float("nan")
        return result

    optimizer.step = nonfinite_step
    try:
        update_policy(model, optimizer, on_policy_batch(model), cfg, torch.device("cpu"), 1)
    except FloatingPointError as exc:
        assert "non-finite Stable-v2 policy update transaction" in str(exc)
    else:
        raise AssertionError("non-finite update must fail fast")
    assert_nested_equal(model_before, model.state_dict())
    assert_nested_equal(optimizer_before, optimizer.state_dict())


def test_guard_is_deterministic_and_checkpoint_resume_exact():
    torch.manual_seed(4103)
    base = agent()
    left, right = agent(), agent()
    left.load_state_dict(base.state_dict())
    right.load_state_dict(base.state_dict())
    cfg = guard_config(lr=0.5, epochs=4)
    left_optimizer, right_optimizer = make_optimizer(left, cfg), make_optimizer(right, cfg)
    state = on_policy_batch(base)
    np.random.seed(4104)
    left_info = update_policy(left, left_optimizer, copy.deepcopy(state), cfg, torch.device("cpu"), 1)
    np.random.seed(4104)
    right_info = update_policy(right, right_optimizer, copy.deepcopy(state), cfg, torch.device("cpu"), 1)
    assert left_info == right_info
    assert all(torch.equal(a, b) for a, b in zip(parameters(left), parameters(right)))
    with tempfile.TemporaryDirectory() as directory:
        checkpoint = Path(directory) / "stable_v2_synthetic.pt"
        save_training_checkpoint(checkpoint, right, right_optimizer, update=1)
        resumed = agent()
        resumed_optimizer = make_optimizer(resumed, cfg)
        load_training_checkpoint(resumed, resumed_optimizer, str(checkpoint), torch.device("cpu"))
        next_state = on_policy_batch(left)
        np.random.seed(4105)
        left_next = update_policy(left, left_optimizer, copy.deepcopy(next_state), cfg, torch.device("cpu"), 2)
        np.random.seed(4105)
        resumed_next = update_policy(resumed, resumed_optimizer, copy.deepcopy(next_state), cfg, torch.device("cpu"), 2)
        assert left_next == resumed_next
        assert all(torch.equal(a, b) for a, b in zip(parameters(left), parameters(resumed)))


def test_guard_default_off_does_not_change_original_update():
    torch.manual_seed(4106)
    base = agent()
    left, right = agent(), agent()
    left.load_state_dict(base.state_dict())
    right.load_state_dict(base.state_dict())
    cfg = guard_config(lr=3e-4, enabled=False)
    explicit_none = replace(cfg, policy_update_guard_mode="none")
    left_optimizer, right_optimizer = make_optimizer(left, cfg), make_optimizer(right, explicit_none)
    state = on_policy_batch(base)
    np.random.seed(4107)
    update_policy(left, left_optimizer, copy.deepcopy(state), cfg, torch.device("cpu"), 1)
    np.random.seed(4107)
    update_policy(right, right_optimizer, copy.deepcopy(state), explicit_none, torch.device("cpu"), 1)
    assert all(torch.equal(a, b) for a, b in zip(parameters(left), parameters(right)))
