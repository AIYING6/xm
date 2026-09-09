"""Trainable task-value model for decision-relevant active diagnosis.

The latent simulator hypothesis is permitted only as a supervision index.  At
decision time the model enumerates every candidate hypothesis from the same
deployment-legal state and returns ``Q(state, hypothesis, recovery_option)``.
No true failure label is part of the actor or gate observation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class DeploymentStateNormalizer(nn.Module):
    """Serializable running moments for deployment-legal state only."""

    def __init__(self, state_dim: int, epsilon: float = 1e-5) -> None:
        super().__init__()
        self.state_dim = int(state_dim)
        self.epsilon = float(epsilon)
        self.register_buffer("count", torch.zeros((), dtype=torch.float64))
        self.register_buffer("mean", torch.zeros(self.state_dim, dtype=torch.float64))
        self.register_buffer("m2", torch.zeros(self.state_dim, dtype=torch.float64))

    @torch.no_grad()
    def update(self, states: torch.Tensor) -> None:
        values = states.detach().to(device=self.mean.device, dtype=torch.float64).reshape(-1, self.state_dim)
        if values.numel() == 0:
            return
        batch_count = torch.tensor(float(values.shape[0]), dtype=torch.float64, device=values.device)
        batch_mean = values.mean(0)
        batch_m2 = ((values - batch_mean) ** 2).sum(0)
        if self.count.item() == 0:
            self.count.copy_(batch_count)
            self.mean.copy_(batch_mean)
            self.m2.copy_(batch_m2)
            return
        delta = batch_mean - self.mean
        total = self.count + batch_count
        self.mean.add_(delta * batch_count / total)
        self.m2.add_(batch_m2 + delta.square() * self.count * batch_count / total)
        self.count.copy_(total)

    def forward(self, states: torch.Tensor) -> torch.Tensor:
        values = states.to(dtype=torch.float32)
        if self.count.item() < 2:
            return values
        variance = (self.m2 / (self.count - 1.0)).clamp_min(self.epsilon).to(dtype=values.dtype)
        return (values - self.mean.to(dtype=values.dtype)) / torch.sqrt(variance)


class TaskValueEstimator(nn.Module):
    """Estimate task return for each candidate failure mode and recovery."""

    def __init__(self, state_dim: int, hidden_dim: int = 64, hypotheses: int = 2, options: int = 2) -> None:
        super().__init__()
        if hypotheses < 2 or options < 2:
            raise ValueError("decision-relevant estimation requires at least two hypotheses and options")
        self.state_dim = int(state_dim)
        self.hypotheses = int(hypotheses)
        self.options = int(options)
        self.normalizer = DeploymentStateNormalizer(self.state_dim)
        self.network = nn.Sequential(
            nn.Linear(self.state_dim + self.hypotheses + self.options, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, 1),
        )

    def all_values(self, states: torch.Tensor) -> torch.Tensor:
        """Enumerate candidates without receiving the realized hypothesis."""
        if states.ndim != 2 or states.shape[-1] != self.state_dim:
            raise ValueError("states must have shape [batch, state_dim]")
        batch = states.shape[0]
        normalized = self.normalizer(states)
        h = torch.eye(self.hypotheses, device=states.device, dtype=normalized.dtype)
        o = torch.eye(self.options, device=states.device, dtype=normalized.dtype)
        state_grid = normalized[:, None, None, :].expand(batch, self.hypotheses, self.options, self.state_dim)
        h_grid = h[None, :, None, :].expand(batch, self.hypotheses, self.options, self.hypotheses)
        o_grid = o[None, None, :, :].expand(batch, self.hypotheses, self.options, self.options)
        features = torch.cat((state_grid, h_grid, o_grid), dim=-1)
        return self.network(features).squeeze(-1)

    def supervised_loss(
        self,
        states: torch.Tensor,
        hypothesis_indices: torch.Tensor,
        option_indices: torch.Tensor,
        returns: torch.Tensor,
    ) -> torch.Tensor:
        """Use simulator truth only to select a supervised prediction cell."""
        values = self.all_values(states)
        rows = torch.arange(values.shape[0], device=values.device)
        predicted = values[rows, hypothesis_indices.long(), option_indices.long()]
        return F.smooth_l1_loss(predicted, returns.to(dtype=predicted.dtype))


@dataclass(frozen=True)
class TaskValueBatch:
    states: torch.Tensor
    hypothesis_indices: torch.Tensor
    option_indices: torch.Tensor
    returns: torch.Tensor


class TaskValueReplayBuffer:
    """Bounded, serializable supervision replay with explicit RNG ownership."""

    runtime_format = "active_diagnosis_task_value_replay_v1"

    def __init__(self, state_dim: int, capacity: int = 4096, seed: int = 0) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.state_dim = int(state_dim)
        self.capacity = int(capacity)
        self._rng = np.random.default_rng(seed)
        self._records: list[tuple[np.ndarray, int, int, float]] = []
        self._cursor = 0

    def __len__(self) -> int:
        return len(self._records)

    def add(self, state: np.ndarray, hypothesis_index: int, option_index: int, discounted_return: float) -> None:
        value = np.asarray(state, dtype=np.float32).reshape(self.state_dim).copy()
        record = (value, int(hypothesis_index), int(option_index), float(discounted_return))
        if len(self._records) < self.capacity:
            self._records.append(record)
        else:
            self._records[self._cursor] = record
        self._cursor = (self._cursor + 1) % self.capacity

    def sample(self, batch_size: int, device: torch.device | str = "cpu") -> TaskValueBatch:
        if not self._records:
            raise RuntimeError("cannot sample an empty task-value replay")
        indices = self._rng.integers(0, len(self._records), size=int(batch_size))
        records = [self._records[int(i)] for i in indices]
        return TaskValueBatch(
            states=torch.as_tensor(np.stack([x[0] for x in records]), device=device),
            hypothesis_indices=torch.as_tensor([x[1] for x in records], device=device),
            option_indices=torch.as_tensor([x[2] for x in records], device=device),
            returns=torch.as_tensor([x[3] for x in records], dtype=torch.float32, device=device),
        )

    def state_dict(self) -> dict[str, Any]:
        return {
            "format": self.runtime_format,
            "state_dim": self.state_dim,
            "capacity": self.capacity,
            "cursor": self._cursor,
            "records": [(x.copy(), h, o, r) for x, h, o, r in self._records],
            "rng_state": self._rng.bit_generator.state,
        }

    def load_state_dict(self, state: dict[str, Any]) -> None:
        if state.get("format") != self.runtime_format:
            raise ValueError("incompatible task-value replay state")
        if int(state["state_dim"]) != self.state_dim or int(state["capacity"]) != self.capacity:
            raise ValueError("task-value replay dimensions differ")
        self._records = [
            (np.asarray(x, dtype=np.float32).reshape(self.state_dim).copy(), int(h), int(o), float(r))
            for x, h, o, r in state["records"]
        ]
        self._cursor = int(state["cursor"])
        self._rng.bit_generator.state = state["rng_state"]


def task_value_checkpoint(
    estimator: TaskValueEstimator,
    optimizer: torch.optim.Optimizer,
    replay: TaskValueReplayBuffer,
) -> dict[str, Any]:
    return {
        "format": "active_diagnosis_task_value_estimator_v1",
        "model": estimator.state_dict(),
        "optimizer": optimizer.state_dict(),
        "replay": replay.state_dict(),
    }


def load_task_value_checkpoint(
    payload: dict[str, Any],
    estimator: TaskValueEstimator,
    optimizer: torch.optim.Optimizer,
    replay: TaskValueReplayBuffer,
) -> None:
    if payload.get("format") != "active_diagnosis_task_value_estimator_v1":
        raise ValueError("incompatible task-value checkpoint")
    estimator.load_state_dict(payload["model"])
    optimizer.load_state_dict(payload["optimizer"])
    replay.load_state_dict(payload["replay"])
