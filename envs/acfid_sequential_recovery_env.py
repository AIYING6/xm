"""Sequential, zero-training qualification environment for ACFID."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from itertools import combinations

import numpy as np

from envs.acfid_compound_fault_env import ACTIONS, FAULTS, ACFIDCompoundFaultEnv, RecoveryContext


@dataclass(frozen=True)
class ACFIDSequentialConfig:
    allowed_fault_sets: tuple[frozenset[str], ...]
    seed: int = 0
    horizon: int = 7
    fault_onset: int = 1
    detection_step: int = 2

    def __post_init__(self) -> None:
        if not 0 < self.fault_onset < self.detection_step < self.horizon - 1:
            raise ValueError("fault onset, detection, and recovery horizon must be ordered")
        if not self.allowed_fault_sets:
            raise ValueError("fault support cannot be empty")
        if any(not faults.issubset(FAULTS) for faults in self.allowed_fault_sets):
            raise ValueError("unknown primitive fault")


class ACFIDSequentialRecoveryEnv:
    """Detected-fault recovery with delayed task outcome and fixed low-level execution."""

    action_dim = len(ACTIONS)
    context_dim = 7
    fault_dim = 5
    relation_dim = 3

    def __init__(self, config: ACFIDSequentialConfig):
        self.config = config; self.model = ACFIDCompoundFaultEnv(); self.rng = np.random.default_rng(config.seed)
        self.step_count = 0; self.done = False

    @staticmethod
    def fault_descriptors() -> np.ndarray:
        descriptors = []
        types = ("sense", "relay", "act")
        for fault in FAULTS:
            kind, branch = fault.rsplit("_", 1)
            descriptors.append([*(float(kind == value) for value in types), float(branch == "0"), float(branch == "1")])
        return np.asarray(descriptors, dtype=np.float32)

    @classmethod
    def pair_relations(cls) -> np.ndarray:
        result = np.zeros((len(FAULTS), len(FAULTS), cls.relation_dim), dtype=np.float32)
        stage = {"sense": 0, "relay": 1, "act": 2}
        for i, first in enumerate(FAULTS):
            type_i, branch_i = first.rsplit("_", 1)
            for j, second in enumerate(FAULTS):
                type_j, branch_j = second.rsplit("_", 1)
                distance = abs(stage[type_i] - stage[type_j]) + (0 if branch_i == branch_j else 2)
                result[i, j] = [float(branch_i == branch_j), float(abs(stage[type_i] - stage[type_j]) == 1), distance / 4.0]
        return result

    def _observation(self) -> dict[str, np.ndarray]:
        visible = self.step_count >= self.config.detection_step
        active = np.asarray([float(visible and fault in self.faults) for fault in FAULTS], dtype=np.float32)
        context = np.asarray([*self.context.demand, *self.context.urgency, self.context.cross_link,
                              self.context.reserve, (self.config.horizon - self.step_count) / self.config.horizon], dtype=np.float32)
        mask = np.ones(self.action_dim, dtype=np.float32) if visible and self.selected_action is None else np.asarray([1, 0, 0, 0, 0], dtype=np.float32)
        return {"context": context, "fault_features": self.fault_descriptors(), "active_faults": active,
                "pair_relations": self.pair_relations(), "action_mask": mask}

    def reset(self, *, fault_set: frozenset[str] | None = None, context: RecoveryContext | None = None):
        if fault_set is None:
            fault_set = self.config.allowed_fault_sets[int(self.rng.integers(len(self.config.allowed_fault_sets)))]
        if fault_set not in self.config.allowed_fault_sets:
            raise ValueError("fault set is outside this environment split")
        self.faults = fault_set; self.context = context or self.model.sample_context(self.rng)
        self.noise = self.rng.lognormal(0.0, 0.055, size=(32, 2)); self.step_count = 0; self.done = False
        self.selected_action: str | None = None; self.terminal_value: float | None = None
        return self._observation()

    def step(self, action: int):
        if self.done: raise RuntimeError("episode already complete")
        if action < 0 or action >= self.action_dim: raise ValueError("invalid recovery action")
        if self.step_count == self.config.detection_step and self.selected_action is None:
            self.selected_action = ACTIONS[action]
            self.terminal_value = self.model.q_values(self.context, self.faults, self.noise)[self.selected_action]
        self.step_count += 1; self.done = self.step_count >= self.config.horizon
        reward = float(self.terminal_value) if self.done and self.terminal_value is not None else 0.0
        info = {"fault_injected": self.step_count > self.config.fault_onset and bool(self.faults),
                "fault_detected": self.step_count > self.config.detection_step,
                "selected_action": self.selected_action, "terminal_value": self.terminal_value,
                "success": bool(self.done and self.terminal_value is not None and self.terminal_value >= 0.85),
                "timeout": bool(self.done and (self.terminal_value is None or self.terminal_value < 0.45))}
        return self._observation(), reward, self.done, info

    def runtime_state(self) -> dict:
        return deepcopy({"rng": self.rng.bit_generator.state, "step_count": self.step_count, "done": self.done,
                         "faults": self.faults, "context": self.context, "noise": self.noise,
                         "selected_action": self.selected_action, "terminal_value": self.terminal_value})

    def restore_runtime_state(self, state: dict) -> None:
        state = deepcopy(state); self.rng = np.random.default_rng(); self.rng.bit_generator.state = state.pop("rng")
        for key, value in state.items(): setattr(self, key, value)


def all_sets_of_orders(*orders: int) -> tuple[frozenset[str], ...]:
    return tuple(frozenset(values) for order in orders for values in combinations(FAULTS, order))
