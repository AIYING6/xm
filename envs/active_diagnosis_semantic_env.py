"""Minimal zero-training environment for the active-diagnosis semantic gate.

This module is deliberately independent of the trainable UAV environment.  It
exists only to test whether a latent communication-failure cause can be hidden
before a costly, legal physical probe and become distinguishable afterwards.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from enum import IntEnum

import numpy as np


RECOVERABLE_RANGE_LOSS = "recoverable_range_loss"
HARD_RELAY_FAILURE = "hard_relay_failure"
FAILURE_HYPOTHESES = (RECOVERABLE_RANGE_LOSS, HARD_RELAY_FAILURE)


class DiagnosticMode(IntEnum):
    CONTINUE_TASK = 0
    HANDSHAKE_PROBE = 1
    DEGRADE_TASK = 2


@dataclass(frozen=True)
class ActiveDiagnosisSemanticConfig:
    world_radius: float = 100.0
    minimum_separation: float = 2.0
    handshake_radius: float = 8.0
    probe_duration_steps: int = 3
    probe_energy_cost: float = 0.12
    max_probe_count: int = 1
    ack_probability_recoverable: float = 0.9
    ack_probability_hard_failure: float = 0.1
    initial_energy: float = 1.0

    def __post_init__(self) -> None:
        if self.probe_duration_steps <= 0:
            raise ValueError("probe_duration_steps must be positive")
        if not 0.0 < self.probe_energy_cost < self.initial_energy:
            raise ValueError("probe energy cost must be positive and feasible")
        if self.max_probe_count != 1:
            raise ValueError("P1B freezes exactly one probe per episode")
        if not 0.0 <= self.ack_probability_hard_failure < self.ack_probability_recoverable <= 1.0:
            raise ValueError("probe must be more informative under recoverable loss")


class ActiveDiagnosisSemanticEnv:
    """Small state machine exposing only legal deployment-side observations."""

    runtime_format = "active_diagnosis_semantic_env_state_v1"

    def __init__(
        self,
        hypothesis: str,
        seed: int,
        config: ActiveDiagnosisSemanticConfig | None = None,
    ) -> None:
        if hypothesis not in FAILURE_HYPOTHESES:
            raise ValueError(f"unknown hypothesis: {hypothesis}")
        self.hypothesis = hypothesis
        self.seed = int(seed)
        self.config = config or ActiveDiagnosisSemanticConfig()
        self.rng = np.random.default_rng(self.seed)
        self.reset()

    def reset(self) -> dict[str, float]:
        # Both hidden hypotheses deliberately share the exact physical state.
        self.positions = np.asarray(
            [[-20.0, 0.0, 10.0], [20.0, 0.0, 10.0], [0.0, 25.0, 10.0]],
            dtype=np.float64,
        )
        self.handshake_zone = np.asarray([0.0, 0.0, 10.0], dtype=np.float64)
        self.step_count = 0
        self.energy = self.config.initial_energy
        self.message_age = 1
        self.message_received = False
        self.handshake_ack = False
        self.probe_count = 0
        self.mode = DiagnosticMode.CONTINUE_TASK
        self.terminated = False
        return self.actor_observation()

    def actor_observation(self) -> dict[str, float]:
        """Return deployment-legal fields; the latent hypothesis is excluded."""
        relay_distance = float(np.linalg.norm(self.positions[1] - self.handshake_zone))
        return {
            "step_norm": self.step_count / 10.0,
            "relay_handshake_distance_norm": relay_distance / self.config.world_radius,
            "message_received": float(self.message_received),
            "message_age_norm": min(1.0, self.message_age / 10.0),
            "handshake_ack": float(self.handshake_ack),
            "probe_budget_remaining": float(self.probe_count < self.config.max_probe_count),
            "energy": float(self.energy),
            "mode": float(int(self.mode)),
        }

    def legal_modes(self) -> tuple[DiagnosticMode, ...]:
        legal = [DiagnosticMode.CONTINUE_TASK, DiagnosticMode.DEGRADE_TASK]
        if self.probe_count < self.config.max_probe_count and not self.terminated:
            legal.append(DiagnosticMode.HANDSHAKE_PROBE)
        return tuple(legal)

    def step(self, mode: DiagnosticMode | int) -> tuple[dict[str, float], dict[str, float]]:
        if self.terminated:
            raise RuntimeError("episode is terminated")
        mode = DiagnosticMode(mode)
        if mode not in self.legal_modes():
            raise ValueError(f"illegal diagnostic mode: {mode}")
        self.mode = mode
        prior_step = self.step_count
        prior_energy = self.energy
        if mode == DiagnosticMode.HANDSHAKE_PROBE:
            self._execute_probe()
        else:
            self.step_count += 1
            self.message_age += 1
            self.terminated = True
        return self.actor_observation(), {
            "elapsed_steps": float(self.step_count - prior_step),
            "energy_cost": float(prior_energy - self.energy),
            "collision": float(self._has_collision()),
            "boundary_violation": float(self._has_boundary_violation()),
            "probe_executed": float(mode == DiagnosticMode.HANDSHAKE_PROBE),
        }

    def _execute_probe(self) -> None:
        self.probe_count += 1
        start = self.positions[1].copy()
        for index in range(1, self.config.probe_duration_steps + 1):
            alpha = index / self.config.probe_duration_steps
            self.positions[1] = (1.0 - alpha) * start + alpha * self.handshake_zone
            self.step_count += 1
            self.message_age += 1
            if self._has_collision() or self._has_boundary_violation():
                raise RuntimeError("frozen probe controller violated safety geometry")
        probability = (
            self.config.ack_probability_recoverable
            if self.hypothesis == RECOVERABLE_RANGE_LOSS
            else self.config.ack_probability_hard_failure
        )
        self.handshake_ack = bool(self.rng.random() < probability)
        self.message_received = self.handshake_ack
        if self.message_received:
            self.message_age = 0
        self.energy -= self.config.probe_energy_cost

    def _has_collision(self) -> bool:
        for first in range(len(self.positions)):
            for second in range(first + 1, len(self.positions)):
                if np.linalg.norm(self.positions[first] - self.positions[second]) < self.config.minimum_separation:
                    return True
        return False

    def _has_boundary_violation(self) -> bool:
        return bool(np.any(np.linalg.norm(self.positions[:, :2], axis=1) > self.config.world_radius))

    def state_dict(self) -> dict:
        return {
            "format": self.runtime_format,
            "hypothesis": self.hypothesis,
            "seed": self.seed,
            "rng": deepcopy(self.rng.bit_generator.state),
            "positions": self.positions.tolist(),
            "step_count": self.step_count,
            "energy": self.energy,
            "message_age": self.message_age,
            "message_received": self.message_received,
            "handshake_ack": self.handshake_ack,
            "probe_count": self.probe_count,
            "mode": int(self.mode),
            "terminated": self.terminated,
        }

    def load_state_dict(self, state: dict) -> None:
        if state.get("format") != self.runtime_format:
            raise ValueError("incompatible semantic environment state")
        if state.get("hypothesis") != self.hypothesis or int(state.get("seed")) != self.seed:
            raise ValueError("state belongs to another latent experiment")
        self.positions = np.asarray(state["positions"], dtype=np.float64)
        self.step_count = int(state["step_count"])
        self.energy = float(state["energy"])
        self.message_age = int(state["message_age"])
        self.message_received = bool(state["message_received"])
        self.handshake_ack = bool(state["handshake_ack"])
        self.probe_count = int(state["probe_count"])
        self.mode = DiagnosticMode(int(state["mode"]))
        self.terminated = bool(state["terminated"])
        self.rng = np.random.default_rng()
        self.rng.bit_generator.state = deepcopy(state["rng"])

