"""Frozen TP-0 topology-perturbation curriculum for the SG backbone.

This module only selects already-defined environment conditions.  It does not
alter the policy architecture, reward, observation boundary, or evaluation
semantics.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import random


FTRAIN_ONSETS = (36, 44, 52)
FTRAIN_DURATIONS = (60, 80, 100)
FTRAIN_POOL = tuple(
    (onset, duration)
    for onset in FTRAIN_ONSETS
    for duration in FTRAIN_DURATIONS
    if (onset, duration) != (44, 80)
)

SCHEDULES = {
    "A": {
        "breakpoints": (0.20, 0.60, 1.00),
        "weights": ((0.80, 0.20, 0.00), (0.55, 0.25, 0.20), (0.40, 0.25, 0.35)),
    },
    "B": {
        "breakpoints": (0.30, 0.70, 1.00),
        "weights": ((0.90, 0.10, 0.00), (0.70, 0.20, 0.10), (0.55, 0.20, 0.25)),
    },
    "C": {
        "breakpoints": (0.15, 0.50, 1.00),
        "weights": ((0.75, 0.25, 0.00), (0.50, 0.25, 0.25), (0.30, 0.25, 0.45)),
    },
}


@dataclass(frozen=True)
class ConditionSelection:
    condition: str
    failure_start_step: int
    failure_duration_steps: int
    failed_blue_agent: int = 1


def schedule_payload(schedule: str) -> dict:
    schedule = schedule.upper()
    if schedule not in SCHEDULES:
        raise ValueError(f"unknown TP schedule: {schedule}")
    return {
        "schedule": schedule,
        "breakpoints": list(SCHEDULES[schedule]["breakpoints"]),
        "weights": [list(row) for row in SCHEDULES[schedule]["weights"]],
        "ftrain_onsets": list(FTRAIN_ONSETS),
        "ftrain_durations": list(FTRAIN_DURATIONS),
        "ftrain_pool_excluding_canonical": [list(pair) for pair in FTRAIN_POOL],
        "canonical_f0": {"failure_start_step": 44, "failure_duration_steps": 80},
    }


def schedule_hash(schedule: str) -> str:
    payload = json.dumps(schedule_payload(schedule), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class TopologyCurriculum:
    """Deterministic per-episode sampler for a pre-frozen schedule."""

    def __init__(self, schedule: str, seed: int, total_updates: int):
        self.schedule = schedule.upper()
        self.enabled = self.schedule != "NONE"
        if self.enabled and self.schedule not in SCHEDULES:
            raise ValueError(f"schedule must be NONE, A, B, or C; got {schedule}")
        self.seed = int(seed)
        self.total_updates = int(total_updates)
        if self.total_updates <= 0:
            raise ValueError("total_updates must be positive")
        self.hash = schedule_hash(self.schedule) if self.enabled else None

    def progress(self, update: int) -> float:
        return min(1.0, max(0.0, float(update) / float(self.total_updates)))

    def weights(self, update: int) -> dict[str, float]:
        if not self.enabled:
            return {"nominal": 1.0, "f0": 0.0, "ftrain": 0.0}
        p = self.progress(update)
        spec = SCHEDULES[self.schedule]
        index = 0 if p < spec["breakpoints"][0] else 1 if p < spec["breakpoints"][1] else 2
        nominal, f0, ftrain = spec["weights"][index]
        return {"nominal": nominal, "f0": f0, "ftrain": ftrain}

    def _rng(self, update: int, env_index: int, episode_index: int) -> random.Random:
        # Stateless arithmetic makes the sequence independent of telemetry I/O.
        key = (self.seed * 1_000_003 + int(update) * 97_003
               + int(env_index) * 10_007 + int(episode_index) * 101)
        return random.Random(key)

    def select(self, update: int, env_index: int, episode_index: int) -> ConditionSelection:
        if not self.enabled:
            return ConditionSelection("nominal", -1, 0, -1)
        rng = self._rng(update, env_index, episode_index)
        u = rng.random()
        weights = self.weights(update)
        if u < weights["nominal"]:
            return ConditionSelection("nominal", -1, 0, -1)
        if u < weights["nominal"] + weights["f0"]:
            return ConditionSelection("f0", 44, 80, 1)
        onset, duration = FTRAIN_POOL[rng.randrange(len(FTRAIN_POOL))]
        return ConditionSelection(f"ftrain_{onset}_{duration}", onset, duration, 1)

    @staticmethod
    def apply(env, selection: ConditionSelection) -> None:
        env.config.failed_blue_agent = selection.failed_blue_agent
        env.config.node_failure_start_step = selection.failure_start_step
        env.config.node_failure_duration_steps = selection.failure_duration_steps

    def manifest(self) -> dict:
        return {
            "protocol": "PHASE-TP-0-CTP-SG-V1",
            "schedule": self.schedule,
            "schedule_hash": self.hash,
            "seed": self.seed,
            "total_updates": self.total_updates,
            "payload": schedule_payload(self.schedule) if self.enabled else None,
        }

    def row(self, update: int, env_index: int, episode_index: int,
            selection: ConditionSelection) -> dict:
        weights = self.weights(update)
        return {
            "update": int(update), "progress": self.progress(update),
            "env_index": int(env_index), "episode_index": int(episode_index),
            "condition": selection.condition,
            "failed_blue_agent": int(selection.failed_blue_agent),
            "failure_start_step": int(selection.failure_start_step),
            "failure_duration_steps": int(selection.failure_duration_steps),
            "nominal_probability": weights["nominal"],
            "f0_probability": weights["f0"],
            "ftrain_probability": weights["ftrain"],
            "schedule": self.schedule, "schedule_hash": self.hash or "",
        }
