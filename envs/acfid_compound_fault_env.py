"""Zero-training macro recovery simulator for the ACFID P0 gate.

This is an independent research-task prototype.  It models two parallel
scout--relay--interceptor mission branches and evaluates high-level recovery
actions after detected primitive degradations.  It does not modify any legacy
DRTP environment or train a policy.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

import numpy as np


FAULTS = ("sense_0", "sense_1", "relay_0", "relay_1", "act_0", "act_1")
ACTIONS = ("continue", "role_reassign", "relay_reposition", "target_reassign", "safe_abort")


@dataclass(frozen=True)
class RecoveryContext:
    demand: tuple[float, float]
    urgency: tuple[float, float]
    cross_link: float
    reserve: float


class ACFIDCompoundFaultEnv:
    """Counterfactual evaluator with common-noise action rollouts."""

    dependency_branch = {
        "sense_0": 0, "relay_0": 0, "act_0": 0,
        "sense_1": 1, "relay_1": 1, "act_1": 1,
    }

    def sample_context(self, rng: np.random.Generator) -> RecoveryContext:
        return RecoveryContext(
            demand=tuple(rng.uniform(0.65, 1.0, 2)),
            urgency=tuple(rng.uniform(0.8, 1.2, 2)),
            cross_link=float(rng.uniform(0.25, 0.65)),
            reserve=float(rng.uniform(0.15, 0.45)),
        )

    @staticmethod
    def _degraded_capacities(faults: frozenset[str]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        sensing = np.ones(2); relay = np.ones(2); act = np.ones(2)
        for index in range(2):
            if f"sense_{index}" in faults: sensing[index] *= 0.38
            if f"relay_{index}" in faults: relay[index] *= 0.28
            if f"act_{index}" in faults: act[index] *= 0.42
        return sensing, relay, act

    def value(self, context: RecoveryContext, faults: frozenset[str], action: str,
              noise: np.ndarray) -> float:
        sensing, relay, act = self._degraded_capacities(faults)
        cost = 0.0
        if action == "role_reassign":
            # Scouts share reserve sensing capacity, but reassignment costs time.
            shared = context.reserve * max(sensing)
            sensing = np.minimum(1.0, sensing + shared)
            cost = 0.12
        elif action == "relay_reposition":
            # Repositioning creates cross-branch relay support at a motion cost.
            relay = np.minimum(1.0, relay + context.cross_link * relay[::-1])
            cost = 0.15
        elif action == "target_reassign":
            # Both interceptors focus on the branch with the larger deliverable value.
            preliminary = np.minimum(np.minimum(sensing, relay), act) * np.asarray(context.urgency)
            chosen = int(np.argmax(preliminary))
            act[:] = 0.0
            act[chosen] = min(1.0, 0.72 + context.reserve)
            cost = 0.10
        elif action == "safe_abort":
            return 0.18 - 0.015 * len(faults)
        elif action != "continue":
            raise ValueError(action)

        delivered = np.minimum(np.minimum(sensing, relay), act)
        delivered = np.clip(delivered * noise, 0.0, 1.0)
        weighted = delivered * np.asarray(context.demand) * np.asarray(context.urgency)
        completed = weighted >= 0.48
        # Shared mission success requires both branches; partial completion remains useful.
        mission_bonus = 0.42 if bool(np.all(completed)) else 0.0
        timeout_penalty = 0.18 * float(np.sum(~completed))
        return float(np.sum(weighted) + mission_bonus - timeout_penalty - cost)

    def q_values(self, context: RecoveryContext, faults: frozenset[str], noise_bank: np.ndarray) -> dict[str, float]:
        output: dict[str, float] = {}
        for action in ACTIONS:
            if action == "safe_abort":
                output[action] = 0.18 - 0.015 * len(faults)
                continue
            sensing, relay, act = self._degraded_capacities(faults); cost = 0.0
            if action == "role_reassign":
                sensing = np.minimum(1.0, sensing + context.reserve * max(sensing)); cost = 0.12
            elif action == "relay_reposition":
                relay = np.minimum(1.0, relay + context.cross_link * relay[::-1]); cost = 0.15
            elif action == "target_reassign":
                preliminary = np.minimum(np.minimum(sensing, relay), act) * np.asarray(context.urgency)
                chosen = int(np.argmax(preliminary)); act[:] = 0.0; act[chosen] = min(1.0, 0.72 + context.reserve); cost = 0.10
            delivered = np.clip(noise_bank * np.minimum(np.minimum(sensing, relay), act), 0.0, 1.0)
            weighted = delivered * np.asarray(context.demand) * np.asarray(context.urgency)
            values = np.sum(weighted, axis=1) + 0.42 * np.all(weighted >= 0.48, axis=1) - 0.18 * np.sum(weighted < 0.48, axis=1) - cost
            output[action] = float(np.mean(values))
        return output

    @classmethod
    def dependency_distance(cls, first: str, second: str) -> int:
        return 1 if cls.dependency_branch[first] == cls.dependency_branch[second] else 3


def fault_sets(order: int):
    return [frozenset(values) for values in combinations(FAULTS, order)]
