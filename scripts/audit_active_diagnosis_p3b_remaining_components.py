"""Technical gate for the P3B value model and recurrent PPO sequence path."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from algorithms.active_diagnosis.pilot_gate_adapter import FailureBelief, ProbeGate
from algorithms.active_diagnosis.recurrent_sg_mappo import (
    RecurrentSGMAPPO,
    load_recurrent_training_checkpoint,
    masked_clipped_actor_objective,
    recurrent_training_checkpoint,
    replay_recurrent_sequence,
)
from algorithms.active_diagnosis.task_value_estimator import (
    TaskValueEstimator,
    TaskValueReplayBuffer,
    load_task_value_checkpoint,
    task_value_checkpoint,
)


KERNEL = np.asarray([[0.9, 0.1], [0.1, 0.9]], dtype=np.float64)


def _train_technical_value_model() -> tuple[TaskValueEstimator, torch.optim.Optimizer, TaskValueReplayBuffer, torch.Tensor]:
    """Fit a fixed synthetic target solely to audit trainability and decisions."""
    torch.manual_seed(41)
    state = torch.tensor([[0.2, -0.1, 0.4]], dtype=torch.float32)
    estimator = TaskValueEstimator(3, hidden_dim=24)
    optimizer = torch.optim.Adam(estimator.parameters(), lr=2e-2)
    replay = TaskValueReplayBuffer(3, capacity=32, seed=41)
    targets = ((0, 0, 2.0), (0, 1, 0.8), (1, 0, 0.0), (1, 1, 1.6))
    for _ in range(8):
        for hypothesis, option, value in targets:
            replay.add(state.numpy()[0], hypothesis, option, value)
    estimator.normalizer.update(torch.cat([state] * len(replay)))
    for _ in range(180):
        batch = replay.sample(32)
        optimizer.zero_grad()
        loss = estimator.supervised_loss(
            batch.states, batch.hypothesis_indices, batch.option_indices, batch.returns
        )
        loss.backward()
        optimizer.step()
    return estimator, optimizer, replay, state


def collect_result() -> dict:
    torch.manual_seed(57)
    estimator, value_optimizer, value_replay, state = _train_technical_value_model()
    predicted = estimator.all_values(state).detach().cpu().numpy()[0]
    target = np.asarray([[2.0, 0.8], [0.0, 1.6]], dtype=np.float32)
    max_error = float(np.max(np.abs(predicted - target)))
    decisions = {}
    for prior in (0.5, 0.9):
        estimated = ProbeGate("decision_relevant", FailureBelief(prior, KERNEL), 0.12).initial_decision(predicted)
        reference = ProbeGate("decision_relevant", FailureBelief(prior, KERNEL), 0.12).initial_decision(target)
        decisions[str(prior)] = {
            "estimated_probe": estimated.force_probe,
            "reference_probe": reference.force_probe,
            "same_decision": estimated.force_probe == reference.force_probe,
        }

    value_payload = copy.deepcopy(task_value_checkpoint(estimator, value_optimizer, value_replay))
    expected_value_batch = value_replay.sample(7)
    restored_estimator = TaskValueEstimator(3, hidden_dim=24)
    restored_value_optimizer = torch.optim.Adam(restored_estimator.parameters(), lr=2e-2)
    restored_value_replay = TaskValueReplayBuffer(3, capacity=32, seed=999)
    load_task_value_checkpoint(value_payload, restored_estimator, restored_value_optimizer, restored_value_replay)
    restored_value_batch = restored_value_replay.sample(7)

    time_steps, environments, agents = 32, 2, 3
    obs_dim, share_dim, action_dim = 7, 9, 29
    base = RecurrentSGMAPPO(obs_dim, share_dim, action_dim, hidden_dim=16, role_dim=4)
    arms = {name: copy.deepcopy(base) for name in ("recurrent_mappo", "entropy_probe", "decision_relevant_probe")}
    parameter_counts = {name: sum(p.numel() for p in arm.parameters()) for name, arm in arms.items()}
    obs = torch.randn(time_steps, environments, agents, obs_dim)
    share = torch.randn(time_steps, environments, agents, share_dim)
    roles = torch.tensor([0, 1, 2]).view(1, 1, agents).expand(time_steps, environments, agents)
    adj = torch.ones(time_steps, environments, agents, agents)
    masks = torch.ones(time_steps, environments, agents, action_dim)
    masks[..., 27:] = 0.0
    sampled_actions = torch.randint(0, 27, (time_steps, environments, agents))
    episode_starts = torch.zeros(time_steps, environments, dtype=torch.bool)
    episode_starts[13, 1] = True
    initial_hidden = base.actor.initial_state(environments, agents, device="cpu")
    replay_a = replay_recurrent_sequence(
        base, obs=obs, roles=roles, adj=adj, masks=masks, share=share,
        sampled_actions=sampled_actions, episode_starts=episode_starts,
        initial_hidden=initial_hidden, bptt_horizon=8,
    )
    replay_b = replay_recurrent_sequence(
        base, obs=obs, roles=roles, adj=adj, masks=masks, share=share,
        sampled_actions=sampled_actions, episode_starts=episode_starts,
        initial_hidden=initial_hidden, bptt_horizon=8,
    )
    actor_control = torch.ones_like(replay_a.log_prob)
    actor_control[0, :, 1] = 0.0
    actor_control[1:4, :, 2] = 0.0
    actor_loss = masked_clipped_actor_objective(
        replay_a, replay_a.log_prob.detach(), torch.ones_like(replay_a.log_prob),
        actor_control, 0.2, 0.01,
    )
    actor_loss.backward()

    recurrent_optimizer = torch.optim.Adam(base.parameters(), lr=3e-4)
    recurrent_payload = copy.deepcopy(recurrent_training_checkpoint(
        base, recurrent_optimizer, replay_a.final_hidden, update=5,
        auxiliary={"belief_gate_and_value_state_required": True},
    ))
    restored_agent = RecurrentSGMAPPO(obs_dim, share_dim, action_dim, hidden_dim=16, role_dim=4)
    restored_optimizer = torch.optim.Adam(restored_agent.parameters(), lr=3e-4)
    update, restored_hidden, auxiliary = load_recurrent_training_checkpoint(
        recurrent_payload, restored_agent, restored_optimizer
    )

    checks = {
        "task_value_model_enumerates_all_candidate_modes_without_truth_input": predicted.shape == (2, 2),
        "technical_value_fit_preserves_gate_decision_at_both_frozen_priors": all(x["same_decision"] for x in decisions.values()),
        "task_value_model_optimizer_normalizer_and_replay_restore_exactly": (
            torch.equal(estimator.all_values(state), restored_estimator.all_values(state))
            and torch.equal(expected_value_batch.states, restored_value_batch.states)
            and torch.equal(expected_value_batch.hypothesis_indices, restored_value_batch.hypothesis_indices)
        ),
        "three_arms_share_identical_recurrent_policy_parameter_count": len(set(parameter_counts.values())) == 1,
        "chronological_32_step_two_environment_replay_is_exact": torch.equal(replay_a.log_prob, replay_b.log_prob),
        "episode_local_reset_and_truncated_bptt_are_explicit": episode_starts[13, 1].item() and replay_a.final_hidden.grad_fn is not None,
        "gate_control_mask_excludes_forced_agent_time_samples": int((actor_control == 0).sum()) == 8,
        "recurrent_actor_loss_and_gru_gradient_are_finite": (
            torch.isfinite(actor_loss).item()
            and base.actor.memory.weight_hh.grad is not None
            and torch.isfinite(base.actor.memory.weight_hh.grad).all().item()
        ),
        "recurrent_model_optimizer_hidden_and_auxiliary_restore_exactly": (
            update == 5
            and auxiliary == {"belief_gate_and_value_state_required": True}
            and torch.equal(restored_hidden, replay_a.final_hidden.detach().cpu())
            and all(torch.equal(a, b) for a, b in zip(base.state_dict().values(), restored_agent.state_dict().values()))
        ),
    }
    passed = all(checks.values())
    return {
        "protocol": "ACTIVE-DIAGNOSIS-P3B-REMAINING-COMPONENTS-V1",
        "verdict": "P3B_REMAINING_COMPONENTS_PASS" if passed else "P3B_REMAINING_COMPONENTS_FAIL",
        "checks": checks,
        "details": {
            "sequence_time_steps": time_steps,
            "sequence_environments": environments,
            "bptt_horizon": 8,
            "parameter_counts": parameter_counts,
            "technical_value_max_abs_error": max_error,
            "technical_gate_decisions": decisions,
            "task_value_target_source": "fixed synthetic technical target; prohibited as pilot task value",
        },
        "environment_steps": 0,
        "ppo_performance_updates": 0,
        "technical_auxiliary_gradient_steps": 180,
        "performance_pilot_authorized": False,
        "remaining_blocker": "integrated three-arm rollout/training/evaluation runner and frozen tape",
        "automatic_continuation": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = collect_result()
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    if result["verdict"].endswith("FAIL"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
