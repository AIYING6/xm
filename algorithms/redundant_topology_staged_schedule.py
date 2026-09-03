"""Frozen static topology curriculum for the 6-UAV P3 candidate.

The scheduler is deliberately outside the learner: it selects an existing
environment fault group only. It has no access to returns, gradients, policy
parameters, evaluation episodes, or future trajectory information.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Protocol

GROUPS = ("nominal", "R_upstream", "R_downstream", "C_relay_node", "C_balanced", "C_cross", "C_same_relay")
TIER_R = ("R_upstream", "R_downstream")
TOTAL_UPDATES = 3907
STAGES = ((0, 977, ("nominal",)), (977, 2344, TIER_R), (2344, TOTAL_UPDATES, GROUPS))


class ChoiceRNG(Protocol):
    def choice(self, values: tuple[str, ...]) -> str: ...


@dataclass(frozen=True)
class StaticTopologySchedule:
    """A static, predeclared sampler; boundaries are update indices [start,end)."""

    total_updates: int = TOTAL_UPDATES

    def groups_for_update(self, update_index: int) -> tuple[str, ...]:
        if not 0 <= update_index < self.total_updates:
            raise ValueError(f"update index outside frozen budget: {update_index}")
        for begin, end, groups in STAGES:
            if begin <= update_index < end:
                return groups
        raise AssertionError("uncovered frozen schedule")

    def sample(self, update_index: int, rng: ChoiceRNG) -> str:
        return str(rng.choice(self.groups_for_update(update_index)))

    def manifest(self) -> dict:
        payload = {"protocol": "REDUNDANT-TOPOLOGY-UAV-P3-STATIC-SCHEDULE-V1", "total_updates": self.total_updates, "stages": [{"begin": begin, "end": end, "groups": list(groups)} for begin, end, groups in STAGES], "adaptive": False, "inputs": "update_index_and_training_rng_only", "forbidden_inputs": ["return", "evaluation", "policy", "gradient", "checkpoint", "seed_outcome"]}
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return {**payload, "schedule_hash": hashlib.sha256(encoded).hexdigest()}
