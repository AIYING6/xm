"""Original-DRTP reset sampler adapted to the frozen six-UAV group interface.

It operates solely at reset: UTR draws uniformly over the seven validated
groups; DRTP holds nominal mass at 1/7 and adapts the conditional distribution
over the six frozen non-nominal groups from completed training returns.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import random


NOMINAL_GROUP = "nominal"
FAILURE_GROUPS = ("R_upstream", "R_downstream", "C_relay_node", "C_balanced", "C_cross", "C_same_relay")
ALL_GROUPS = (NOMINAL_GROUP, *FAILURE_GROUPS)
NOMINAL_MASS = 1.0 / len(ALL_GROUPS)
UNIFORM_Q = 1.0 / len(FAILURE_GROUPS)
WARMUP_UPDATES = 128
ADAPT_INTERVAL = 32
EMA_KAPPA = 0.20
SMOOTHING_BETA = 0.50
TEMPERATURE_ETA = 1.00
DIFFICULTY_MAX = 2.00
EPSILON = 1e-8
Q_MIN, Q_MAX = 0.05, 0.35


@dataclass(frozen=True)
class SixUAVDRTPSelection:
    group: str


def _project(values: list[float]) -> list[float]:
    low, high = min(value - Q_MAX for value in values), max(value - Q_MIN for value in values)
    for _ in range(100):
        midpoint = (low + high) / 2.0
        if sum(min(Q_MAX, max(Q_MIN, value - midpoint)) for value in values) > 1.0:
            low = midpoint
        else:
            high = midpoint
    projected = [min(Q_MAX, max(Q_MIN, value - high)) for value in values]
    residual = 1.0 - sum(projected)
    for index, value in enumerate(projected):
        if abs(residual) <= 1e-12:
            break
        room = Q_MAX - value if residual > 0.0 else value - Q_MIN
        delta = math.copysign(min(abs(residual), max(0.0, room)), residual)
        projected[index] += delta
        residual -= delta
    if not math.isclose(sum(projected), 1.0, rel_tol=0.0, abs_tol=1e-10):
        raise AssertionError("six-UAV DRTP projection lost probability mass")
    return projected


class SixUAVDRTPTopologySampler:
    """Deterministic UTR or Original-DRTP sampler for the validated six-UAV task."""

    def __init__(self, mode: str, seed: int, total_updates: int):
        self.mode = str(mode).lower()
        if self.mode not in {"utr", "drtp"}:
            raise ValueError("six-UAV sampler mode must be utr or drtp")
        self.seed, self.total_updates = int(seed), int(total_updates)
        self.q = {group: UNIFORM_Q for group in FAILURE_GROUPS}
        self.ema = {group: None for group in ALL_GROUPS}
        self.window_returns = {group: [] for group in ALL_GROUPS}
        self.adaptation_count = 0

    def _rng(self, update: int, env_index: int, episode_index: int) -> random.Random:
        return random.Random(self.seed * 1_000_003 + int(update) * 97_003 + int(env_index) * 10_007 + int(episode_index) * 101)

    def select(self, update: int, env_index: int, episode_index: int) -> SixUAVDRTPSelection:
        rng = self._rng(update, env_index, episode_index)
        if self.mode == "utr":
            return SixUAVDRTPSelection(ALL_GROUPS[rng.randrange(len(ALL_GROUPS))])
        if rng.random() < NOMINAL_MASS:
            return SixUAVDRTPSelection(NOMINAL_GROUP)
        draw, cursor = rng.random(), 0.0
        for group in FAILURE_GROUPS:
            cursor += self.q[group]
            if draw < cursor:
                return SixUAVDRTPSelection(group)
        return SixUAVDRTPSelection(FAILURE_GROUPS[-1])

    def record_completed_return(self, selection: SixUAVDRTPSelection, episode_return: float) -> None:
        if selection.group not in ALL_GROUPS or not math.isfinite(float(episode_return)):
            raise ValueError("invalid six-UAV DRTP completed return")
        self.window_returns[selection.group].append(float(episode_return))

    def maybe_update(self, update: int) -> dict | None:
        if self.mode == "utr" or int(update) % ADAPT_INTERVAL != 0:
            return None
        for group in ALL_GROUPS:
            values = self.window_returns[group]
            if values:
                observed = sum(values) / len(values)
                self.ema[group] = observed if self.ema[group] is None else (1.0 - EMA_KAPPA) * self.ema[group] + EMA_KAPPA * observed
        reason = "warmup_or_missing_group_evidence"
        adapted = False
        if int(update) > WARMUP_UPDATES and all(self.ema[group] is not None for group in ALL_GROUPS):
            nominal = float(self.ema[NOMINAL_GROUP])
            difficulty = {group: min(DIFFICULTY_MAX, max(0.0, (nominal - float(self.ema[group])) / max(abs(nominal), EPSILON))) for group in FAILURE_GROUPS}
            center = sum(difficulty.values()) / len(FAILURE_GROUPS)
            logits = {group: self.q[group] * math.exp(TEMPERATURE_ETA * (difficulty[group] - center)) for group in FAILURE_GROUPS}
            normalizer = sum(logits.values())
            target = [logits[group] / normalizer for group in FAILURE_GROUPS]
            self.q = dict(zip(FAILURE_GROUPS, _project([(1.0 - SMOOTHING_BETA) * self.q[group] + SMOOTHING_BETA * target[index] for index, group in enumerate(FAILURE_GROUPS)])))
            self.adaptation_count += 1
            reason, adapted = "bounded_exponentiated_gradient", True
        counts = {group: len(self.window_returns[group]) for group in ALL_GROUPS}
        self.window_returns = {group: [] for group in ALL_GROUPS}
        return {"update": int(update), "adapted": adapted, "reason": reason, "adaptation_count": self.adaptation_count, **{f"q_{group}": self.q[group] for group in FAILURE_GROUPS}, **{f"window_count_{group}": counts[group] for group in ALL_GROUPS}}

    def state_dict(self) -> dict:
        return {"format": "six_uav_drtp_sampler_runtime_state_v1", "mode": self.mode, "seed": self.seed, "total_updates": self.total_updates, "q": dict(self.q), "ema": dict(self.ema), "window_returns": {group: list(values) for group, values in self.window_returns.items()}, "adaptation_count": self.adaptation_count}

    def load_state_dict(self, state: dict) -> None:
        if state.get("format") != "six_uav_drtp_sampler_runtime_state_v1" or str(state.get("mode")) != self.mode or int(state.get("seed")) != self.seed:
            raise ValueError("incompatible six-UAV DRTP sampler runtime state")
        self.q = {group: float(state["q"][group]) for group in FAILURE_GROUPS}
        self.ema = {group: None if state["ema"][group] is None else float(state["ema"][group]) for group in ALL_GROUPS}
        self.window_returns = {group: [float(value) for value in state["window_returns"][group]] for group in ALL_GROUPS}
        self.adaptation_count = int(state["adaptation_count"])
        if not math.isclose(sum(self.q.values()), 1.0, rel_tol=0.0, abs_tol=1e-10):
            raise ValueError("six-UAV DRTP runtime q has invalid mass")

    def manifest(self) -> dict:
        return {"protocol": "DRTP-6UAV-CROSS-SCALE-FORMAL-TRAINING-FREEZE-V1", "mode": self.mode, "groups": list(ALL_GROUPS), "nominal_mass": NOMINAL_MASS, "uniform_q": UNIFORM_Q, "warmup_updates": WARMUP_UPDATES, "adapt_interval": ADAPT_INTERVAL, "actor_or_critic_condition_input": False, "reward_or_ppo_objective_change": False}
