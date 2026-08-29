"""Rollout-free tests for the frozen D4 KL-boundary backtracking guard."""
from __future__ import annotations

import copy
from dataclasses import replace
from pathlib import Path
import tempfile

import numpy as np
import torch

from algorithms.ri_gmappo.simple_ri_gmappo import (
    POLICY_KL_BACKTRACK_BISECTION_STEPS,
    load_training_checkpoint,
    make_optimizer,
    save_training_checkpoint,
    update_policy,
)
from tests.test_drtp_stable_v2_kl_guard import (
    assert_nested_equal,
    guard_config,
    module_parameters,
    on_policy_batch,
    optimizer_parameter_state,
)
from tests.test_tc_sam import agent, parameters


def backtrack_config(*, lr: float, epochs: int = 1):
    return replace(
        guard_config(lr=lr, epochs=epochs),
        policy_update_guard_mode="post_step_actor_backtrack",
    )


def test_backtrack_accepts_small_step_and_exactly_preserves_original_update():
    torch.manual_seed(4201)
    np.random.seed(4201)
    base = agent()
    projected, original = agent(), agent()
    projected.load_state_dict(base.state_dict())
    original.load_state_dict(base.state_dict())
    projected_cfg = backtrack_config(lr=1e-6, epochs=4)
    original_cfg = replace(
        projected_cfg, target_kl=None, policy_update_guard_mode="none"
    )
    projected_optimizer = make_optimizer(projected, projected_cfg)
    original_optimizer = make_optimizer(original, original_cfg)
    state = on_policy_batch(base)
    np.random.seed(4211)
    info = update_policy(
        projected, projected_optimizer, copy.deepcopy(state), projected_cfg, torch.device("cpu"), 1
    )
    np.random.seed(4211)
    update_policy(
        original, original_optimizer, copy.deepcopy(state), original_cfg, torch.device("cpu"), 1
    )
    assert info["policy_guard_triggered"] == 0.0
    assert info["policy_backtrack_alpha"] == 1.0
    assert info["policy_backtrack_iterations"] == 0
    assert info["actor_projection_l2"] == 0.0
    assert all(torch.equal(left, right) for left, right in zip(parameters(projected), parameters(original)))
    assert_nested_equal(projected_optimizer.state_dict(), original_optimizer.state_dict())


def test_backtrack_retains_a_maximal_safe_actor_step_and_critic_step():
    torch.manual_seed(4202)
    np.random.seed(4202)
    model = agent()
    warmup_cfg = backtrack_config(lr=1e-6)
    optimizer = make_optimizer(model, warmup_cfg)
    update_policy(model, optimizer, on_policy_batch(model), warmup_cfg, torch.device("cpu"), 1)
    actor_before = module_parameters(model.actor)
    critic_before = module_parameters(model.critic)
    actor_adam_before = optimizer_parameter_state(optimizer, model.actor)
    optimizer.param_groups[0]["lr"] = 0.5
    cfg = replace(warmup_cfg, ppo_epochs=4)
    info = update_policy(model, optimizer, on_policy_batch(model), cfg, torch.device("cpu"), 2)

    assert info["policy_guard_triggered"] == 1.0
    assert info["policy_guard_reason"] == "post_step_kl_backtracked"
    assert info["policy_guard_epoch"] == 1
    assert info["ppo_epochs_ran"] == 1
    assert info["policy_steps_attempted"] == 1
    assert info["policy_steps_accepted"] == 1
    assert info["policy_kl_attempted_max"] > cfg.target_kl
    assert 0.0 <= info["policy_kl_post_step"] <= cfg.target_kl
    assert 0.0 < info["policy_backtrack_alpha"] < 1.0
    assert info["policy_backtrack_iterations"] == POLICY_KL_BACKTRACK_BISECTION_STEPS
    assert 0.0 < info["actor_accepted_update_l2"] < info["actor_attempted_update_l2"]
    assert info["actor_projection_l2"] > 0.0
    assert info["actor_rollback_l2"] == 0.0
    assert info["actor_optimizer_state_restored"] == 0.0
    assert info["actor_optimizer_state_retained_after_projection"] == 1.0
    assert info["critic_step_retained_after_policy_guard"] == 1.0
    assert info["critic_step_retained_after_actor_rollback"] == 0.0
    assert any(not torch.equal(left, right) for left, right in zip(actor_before, module_parameters(model.actor)))
    assert any(not torch.equal(left, right) for left, right in zip(critic_before, module_parameters(model.critic)))
    actor_adam_after = optimizer_parameter_state(optimizer, model.actor)
    assert any(
        not torch.equal(actor_adam_before[name]["exp_avg"], actor_adam_after[name]["exp_avg"])
        for name in actor_adam_before
    )
    actor_steps = [
        int(optimizer.state[parameter]["step"].item())
        for parameter in model.actor.parameters()
        if "step" in optimizer.state.get(parameter, {})
    ]
    critic_steps = [
        int(optimizer.state[parameter]["step"].item())
        for parameter in model.critic.parameters()
        if "step" in optimizer.state.get(parameter, {})
    ]
    assert actor_steps and all(step == 2 for step in actor_steps)
    assert critic_steps and all(step == 2 for step in critic_steps)


def test_backtrack_is_deterministic_and_checkpoint_resume_exact():
    torch.manual_seed(4203)
    base = agent()
    left, right = agent(), agent()
    left.load_state_dict(base.state_dict())
    right.load_state_dict(base.state_dict())
    cfg = backtrack_config(lr=0.5, epochs=4)
    left_optimizer, right_optimizer = make_optimizer(left, cfg), make_optimizer(right, cfg)
    state = on_policy_batch(base)
    np.random.seed(4204)
    left_info = update_policy(left, left_optimizer, copy.deepcopy(state), cfg, torch.device("cpu"), 1)
    np.random.seed(4204)
    right_info = update_policy(right, right_optimizer, copy.deepcopy(state), cfg, torch.device("cpu"), 1)
    assert left_info == right_info
    assert all(torch.equal(a, b) for a, b in zip(parameters(left), parameters(right)))
    assert_nested_equal(left_optimizer.state_dict(), right_optimizer.state_dict())

    with tempfile.TemporaryDirectory() as directory:
        checkpoint = Path(directory) / "stable_v2_d4_synthetic.pt"
        save_training_checkpoint(checkpoint, right, right_optimizer, update=1)
        resumed = agent()
        resumed_optimizer = make_optimizer(resumed, cfg)
        load_training_checkpoint(resumed, resumed_optimizer, str(checkpoint), torch.device("cpu"))
        next_state = on_policy_batch(left)
        np.random.seed(4205)
        left_next = update_policy(left, left_optimizer, copy.deepcopy(next_state), cfg, torch.device("cpu"), 2)
        np.random.seed(4205)
        resumed_next = update_policy(
            resumed, resumed_optimizer, copy.deepcopy(next_state), cfg, torch.device("cpu"), 2
        )
        assert left_next == resumed_next
        assert all(torch.equal(a, b) for a, b in zip(parameters(left), parameters(resumed)))
        assert_nested_equal(left_optimizer.state_dict(), resumed_optimizer.state_dict())


def test_backtrack_nonfinite_step_restores_full_transaction():
    torch.manual_seed(4206)
    model = agent()
    cfg = backtrack_config(lr=1e-6)
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
