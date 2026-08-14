"""Static nominal/F0 condition sampler for shared-policy reference training.

This is deliberately not a curriculum: the probability is constant at every
update and no performance signal affects the sampled condition.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import random

from algorithms.ri_gmappo.topology_curriculum import ConditionSelection


@dataclass(frozen=True)
class FixedConditionMixture:
    """Deterministic, update-invariant nominal/F0 episode sampler."""

    f0_probability: float
    seed: int

    def __post_init__(self) -> None:
        if not 0.0 <= self.f0_probability <= 1.0:
            raise ValueError("f0_probability must be in [0, 1]")

    def _rng(self, env_index: int, episode_index: int) -> random.Random:
        key = self.seed * 1_000_003 + int(env_index) * 10_007 + int(episode_index) * 101
        return random.Random(key)

    def select(self, env_index: int, episode_index: int) -> ConditionSelection:
        if self._rng(env_index, episode_index).random() < self.f0_probability:
            return ConditionSelection("f0", 44, 80, 1)
        return ConditionSelection("nominal", -1, 0, -1)

    @staticmethod
    def apply(env, selection: ConditionSelection) -> None:
        env.config.failed_blue_agent = selection.failed_blue_agent
        env.config.node_failure_start_step = selection.failure_start_step
        env.config.node_failure_duration_steps = selection.failure_duration_steps

    def manifest(self) -> dict:
        payload = {
            "protocol": "PHASE-MSR-MIXED50-V1",
            "sampler": "fixed_episode_mixture",
            "f0_probability": self.f0_probability,
            "nominal_probability": 1.0 - self.f0_probability,
            "f0": {"failed_blue_agent": 1, "failure_start_step": 44, "failure_duration_steps": 80},
            "seed": self.seed,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return {**payload, "mixture_hash": hashlib.sha256(encoded).hexdigest()}

    def row(self, update: int, env_index: int, episode_index: int,
            selection: ConditionSelection) -> dict:
        return {
            "update": int(update),
            "env_index": int(env_index),
            "episode_index": int(episode_index),
            "condition": selection.condition,
            "failed_blue_agent": int(selection.failed_blue_agent),
            "failure_start_step": int(selection.failure_start_step),
            "failure_duration_steps": int(selection.failure_duration_steps),
            "nominal_probability": 1.0 - self.f0_probability,
            "f0_probability": self.f0_probability,
        }
