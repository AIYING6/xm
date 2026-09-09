import copy

import numpy as np
import torch

from algorithms.active_diagnosis.task_value_estimator import (
    TaskValueEstimator,
    TaskValueReplayBuffer,
    load_task_value_checkpoint,
    task_value_checkpoint,
)


def _fit_small_estimator():
    torch.manual_seed(4)
    estimator = TaskValueEstimator(3, hidden_dim=24)
    optimizer = torch.optim.Adam(estimator.parameters(), lr=2e-2)
    states = torch.tensor([[0.2, -0.1, 0.4]]).repeat(64, 1)
    hypothesis = torch.tensor([0, 0, 1, 1]).repeat(16)
    option = torch.tensor([0, 1, 0, 1]).repeat(16)
    returns = torch.tensor([2.0, 0.6, -0.5, 1.5]).repeat(16)
    estimator.normalizer.update(states)
    for _ in range(160):
        optimizer.zero_grad()
        loss = estimator.supervised_loss(states, hypothesis, option, returns)
        loss.backward()
        optimizer.step()
    return estimator, optimizer, states[:1]


def test_estimator_enumerates_candidates_without_realized_hypothesis_input() -> None:
    estimator, _, state = _fit_small_estimator()
    values = estimator.all_values(state)
    assert values.shape == (1, 2, 2)
    assert values[0, 0].argmax().item() == 0
    assert values[0, 1].argmax().item() == 1


def test_value_replay_and_optimizer_restore_exactly() -> None:
    estimator, optimizer, state = _fit_small_estimator()
    replay = TaskValueReplayBuffer(3, capacity=8, seed=19)
    for h in range(2):
        for option in range(2):
            replay.add(state.numpy()[0], h, option, float(h + option))
    payload = copy.deepcopy(task_value_checkpoint(estimator, optimizer, replay))
    expected_batch = replay.sample(5)

    restored = TaskValueEstimator(3, hidden_dim=24)
    restored_optimizer = torch.optim.Adam(restored.parameters(), lr=2e-2)
    restored_replay = TaskValueReplayBuffer(3, capacity=8, seed=999)
    load_task_value_checkpoint(payload, restored, restored_optimizer, restored_replay)
    actual_batch = restored_replay.sample(5)
    assert torch.equal(expected_batch.states, actual_batch.states)
    assert torch.equal(expected_batch.hypothesis_indices, actual_batch.hypothesis_indices)
    assert torch.equal(estimator.all_values(state), restored.all_values(state))


def test_replay_copies_deployment_state_and_not_later_mutation() -> None:
    replay = TaskValueReplayBuffer(2, capacity=2)
    state = np.asarray([1.0, 2.0], dtype=np.float32)
    replay.add(state, 0, 1, 3.0)
    state[:] = 99.0
    stored = replay.state_dict()["records"][0][0]
    assert stored.tolist() == [1.0, 2.0]
