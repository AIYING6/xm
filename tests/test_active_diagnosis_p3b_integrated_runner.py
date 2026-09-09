import copy
from dataclasses import replace

import numpy as np
import torch

from algorithms.active_diagnosis.pilot_runner import (
    ActiveDiagnosisPPOConfig,
    calibrate_task_value_estimator,
    collect_rollout,
    load_runtime_state_dict,
    make_runtime,
    runtime_state_dict,
    update_from_rollout,
)
from algorithms.active_diagnosis.recurrent_sg_mappo import RecurrentSGMAPPO
from algorithms.active_diagnosis.task_value_estimator import TaskValueEstimator, TaskValueReplayBuffer
from envs.active_diagnosis_semantic_env import RECOVERABLE_RANGE_LOSS
from envs.active_diagnosis_trainable_uav_env import (
    ActiveDiagnosisTrainableConfig,
    ActiveDiagnosisTrainableUAVEnv,
    HARD_TERMINAL_COMM_FAILURE,
)


def _components(arm: str):
    envs = [
        ActiveDiagnosisTrainableUAVEnv(ActiveDiagnosisTrainableConfig(RECOVERABLE_RANGE_LOSS, 901)),
        ActiveDiagnosisTrainableUAVEnv(ActiveDiagnosisTrainableConfig(HARD_TERMINAL_COMM_FAILURE, 902)),
    ]
    agent = RecurrentSGMAPPO(envs[0].obs_dim, envs[0].share_obs_dim, envs[0].action_dim, hidden_dim=20)
    estimator = TaskValueEstimator(envs[0].obs_dim, hidden_dim=20)
    replay = TaskValueReplayBuffer(envs[0].obs_dim, capacity=64, seed=11)
    runtime = make_runtime(arm, envs, agent, recoverable_prior=0.5, device="cpu")
    return envs, agent, estimator, replay, runtime


def test_entropy_gate_collects_distinct_sampled_and_executed_actions() -> None:
    torch.manual_seed(1)
    _, agent, estimator, replay, runtime = _components("entropy_probe")
    batch = collect_rollout(
        agent, estimator, replay, runtime,
        ActiveDiagnosisPPOConfig(rollout_steps=16, bptt_horizon=8, ppo_epochs=1),
    )
    assert batch["illegal_executed_actions"] == 0
    assert np.any(batch["sampled_actions"] != batch["executed_actions"])
    assert np.any(batch["actor_control_mask"] == 0.0)
    assert batch["old_log_prob"].shape == (16, 2, 3)


def test_real_rollout_replays_and_takes_one_finite_ppo_update() -> None:
    torch.manual_seed(2)
    _, agent, estimator, replay, runtime = _components("decision_relevant_probe")
    cfg = ActiveDiagnosisPPOConfig(rollout_steps=16, bptt_horizon=8, ppo_epochs=1)
    batch = collect_rollout(agent, estimator, replay, runtime, cfg)
    optimizer = torch.optim.Adam(agent.parameters(), lr=3e-4)
    metrics = update_from_rollout(agent, optimizer, batch, cfg)
    assert batch["illegal_executed_actions"] == 0
    assert all(np.isfinite(value) for value in metrics.values())


def test_mid_episode_runtime_restore_reproduces_next_real_rollout() -> None:
    torch.manual_seed(3); np.random.seed(3)
    _, agent, estimator, replay, runtime = _components("entropy_probe")
    warmup = ActiveDiagnosisPPOConfig(rollout_steps=5, bptt_horizon=4, ppo_epochs=1)
    collect_rollout(agent, estimator, replay, runtime, warmup)
    saved_runtime = copy.deepcopy(runtime_state_dict(runtime))
    saved_agent = copy.deepcopy(agent.state_dict())
    saved_estimator = copy.deepcopy(estimator.state_dict())
    first = collect_rollout(agent, estimator, replay, runtime, warmup)

    _, clone_agent, clone_estimator, clone_replay, clone_runtime = _components("entropy_probe")
    clone_agent.load_state_dict(saved_agent)
    clone_estimator.load_state_dict(saved_estimator)
    load_runtime_state_dict(clone_runtime, saved_runtime)
    second = collect_rollout(clone_agent, clone_estimator, clone_replay, clone_runtime, warmup)
    for key in ("sampled_actions", "executed_actions", "old_log_prob", "rewards", "dones"):
        assert np.array_equal(first[key], second[key])


def test_completed_training_episode_adds_real_return_supervision() -> None:
    torch.manual_seed(6)
    envs, agent, estimator, replay, runtime = _components("recurrent_mappo")
    for env in envs:
        env.base.config = replace(env.base.config, max_steps=6)
    batch = collect_rollout(
        agent, estimator, replay, runtime,
        ActiveDiagnosisPPOConfig(rollout_steps=6, bptt_horizon=3, ppo_epochs=1),
    )
    assert runtime.completed_episodes == 2
    assert len(replay) == 2
    records = replay.state_dict()["records"]
    assert {record[1] for record in records} == {0, 1}
    assert all(np.isfinite(record[3]) for record in records)
    assert batch["dones"][-1].tolist() == [1.0, 1.0]


def test_calibration_has_full_factorial_cells_and_never_updates_actor() -> None:
    torch.manual_seed(7)
    env = ActiveDiagnosisTrainableUAVEnv()
    agent = RecurrentSGMAPPO(env.obs_dim, env.share_obs_dim, env.action_dim, hidden_dim=8)
    estimator = TaskValueEstimator(env.obs_dim, hidden_dim=8)
    optimizer = torch.optim.Adam(estimator.parameters(), lr=1e-2)
    before = copy.deepcopy(agent.state_dict())
    report = calibrate_task_value_estimator(
        agent, estimator, optimizer,
        geometry_seeds=[9201, 9202], train_geometry_count=1, gradient_steps=3,
    )
    assert report["episodes"] == 8
    assert report["ppo_updates"] == 0
    assert report["actor_parameters_changed"] is False
    assert all(torch.equal(before[key], agent.state_dict()[key]) for key in before)
    for records in report["records"].values():
        assert {(row["hypothesis_index"], row["recovery_option"]) for row in records} == {
            (0, 0), (0, 1), (1, 0), (1, 1)
        }


def test_task_value_inputs_are_relay_local_observations_not_critic_state() -> None:
    envs, agent, estimator, replay, runtime = _components("decision_relevant_probe")
    assert estimator.state_dim == envs[0].obs_dim
    assert estimator.state_dim != envs[0].share_obs_dim
    assert runtime.supervision[0].initial_gate_observation.shape == (envs[0].obs_dim,)
    envs[0].base.config = replace(envs[0].base.config, max_steps=2)
    envs[1].base.config = replace(envs[1].base.config, max_steps=2)
    collect_rollout(
        agent, estimator, replay, runtime,
        ActiveDiagnosisPPOConfig(rollout_steps=2, bptt_horizon=2, ppo_epochs=1),
    )
    assert all(len(record[0]) == envs[0].obs_dim for record in replay.state_dict()["records"])
