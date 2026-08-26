"""Frozen static-nonuniform topology sampler for the SNR mechanism control.

SNR is deliberately training-side only.  It samples one of the already frozen
topology-perturbation groups at reset time using a *fixed* conditional
distribution.  It has no completed-return feedback, EMA, difficulty estimate,
or weight-update path.
"""
from __future__ import annotations

import hashlib
import json
import math
import random

from algorithms.ri_gmappo.drtp_topology_sampler import (
    ALL_GROUPS,
    DRTPSelection,
    FAILURE_GROUPS,
    GROUP_MEMBERS,
    NOMINAL_GROUP,
    NOMINAL_MASS,
)


PROTOCOL = "DRTP-SNR-Q2-MECHANISM-COMPARATOR-V1"
RUNTIME_FORMAT = "snr_static_nonuniform_topology_sampler_runtime_state_v1"
STATIC_NONUNIFORM_Q = {
    "F0": 0.15,
    "TE": 0.20,
    "TL": 0.10,
    "DS": 0.10,
    "DL": 0.20,
    "CP": 0.25,
}


class StaticNonuniformTopologySampler:
    """Deterministic reset sampler with no training-return feedback channel."""

    uses_completed_return_feedback = False

    def __init__(self, seed: int, total_updates: int):
        self.mode = "snr"
        self.seed = int(seed)
        self.total_updates = int(total_updates)
        if self.total_updates <= 0:
            raise ValueError("total_updates must be positive")
        self.q = {group: float(STATIC_NONUNIFORM_Q[group]) for group in FAILURE_GROUPS}
        if set(self.q) != set(FAILURE_GROUPS):
            raise AssertionError("SNR weights do not cover the frozen failure-group universe")
        if not math.isclose(sum(self.q.values()), 1.0, rel_tol=0.0, abs_tol=1e-12):
            raise AssertionError("SNR conditional weights must sum to one")

    def state_dict(self) -> dict:
        """Persist fixed identity fields only; SNR has no mutable adaptation state."""
        return {
            "format": RUNTIME_FORMAT,
            "mode": self.mode,
            "seed": self.seed,
            "total_updates": self.total_updates,
            "static_nonuniform_q": dict(self.q),
            "uses_completed_return_feedback": False,
            "ema_state": None,
            "difficulty_state": None,
            "adaptation_window": None,
        }

    def load_state_dict(self, state: dict) -> None:
        if state.get("format") != RUNTIME_FORMAT:
            raise ValueError("unsupported SNR sampler runtime-state format")
        if str(state.get("mode")) != self.mode or int(state.get("seed")) != self.seed:
            raise ValueError("SNR runtime state is bound to a different mode or seed")
        if int(state.get("total_updates")) != self.total_updates:
            raise ValueError("SNR runtime state is bound to a different training budget")
        restored = {group: float(state["static_nonuniform_q"][group]) for group in FAILURE_GROUPS}
        if restored != self.q:
            raise ValueError("SNR runtime state attempted to alter frozen static weights")
        if state.get("uses_completed_return_feedback") is not False:
            raise ValueError("SNR runtime state has an invalid feedback flag")
        if any(state.get(name) is not None for name in ("ema_state", "difficulty_state", "adaptation_window")):
            raise ValueError("SNR runtime state must not carry adaptive sampler state")

    def _rng(self, update: int, env_index: int, episode_index: int) -> random.Random:
        key = (
            self.seed * 1_000_003
            + int(update) * 97_003
            + int(env_index) * 10_007
            + int(episode_index) * 101
        )
        return random.Random(key)

    @staticmethod
    def apply(env, selection: DRTPSelection) -> None:
        env.config.failed_blue_agent = selection.failed_blue_agent
        env.config.node_failure_start_step = selection.failure_start_step
        env.config.node_failure_duration_steps = selection.failure_duration_steps

    def _select_failure_group(self, rng: random.Random) -> str:
        draw, cursor = rng.random(), 0.0
        for group in FAILURE_GROUPS:
            cursor += self.q[group]
            if draw < cursor:
                return group
        return FAILURE_GROUPS[-1]

    def select(self, update: int, env_index: int, episode_index: int) -> DRTPSelection:
        rng = self._rng(update, env_index, episode_index)
        group = NOMINAL_GROUP if rng.random() < NOMINAL_MASS else self._select_failure_group(rng)
        condition, onset, duration = GROUP_MEMBERS[group][rng.randrange(len(GROUP_MEMBERS[group]))]
        return DRTPSelection(
            group=group,
            condition=condition,
            failure_start_step=onset,
            failure_duration_steps=duration,
            failed_blue_agent=-1 if group == NOMINAL_GROUP else 1,
        )

    def record_completed_return(self, selection: DRTPSelection, episode_return: float) -> None:
        raise AssertionError("SNR must never receive completed-episode return feedback")

    def maybe_update(self, update: int) -> None:
        """SNR has no feedback-driven update path."""
        return None

    def manifest(self) -> dict:
        payload = {
            "protocol": PROTOCOL,
            "mode": self.mode,
            "seed": self.seed,
            "total_updates": self.total_updates,
            "groups": {group: [list(member) for member in GROUP_MEMBERS[group]] for group in ALL_GROUPS},
            "nominal_mass": NOMINAL_MASS,
            "failure_groups": list(FAILURE_GROUPS),
            "static_nonuniform_q": dict(self.q),
            "unconditional_failure_mass": {group: NOMINAL_MASS * self.q[group] for group in FAILURE_GROUPS},
            "uses_completed_return_feedback": False,
            "ema": "ABSENT",
            "difficulty": "ABSENT",
            "weight_updates": "ABSENT",
            "actor_or_critic_condition_input": False,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return {**payload, "sampler_hash": hashlib.sha256(encoded).hexdigest()}

    @staticmethod
    def log_fields() -> list[str]:
        fields = [
            "record_type", "update", "env_index", "episode_index", "group", "condition",
            "failed_blue_agent", "failure_start_step", "failure_duration_steps",
            "feedback_mode", "adapted", "reason",
        ]
        fields += [f"q_{group}" for group in FAILURE_GROUPS]
        return fields

    def selection_row(self, update: int, env_index: int, episode_index: int, selection: DRTPSelection) -> dict:
        return {
            "record_type": "selection",
            "update": int(update),
            "env_index": int(env_index),
            "episode_index": int(episode_index),
            "group": selection.group,
            "condition": selection.condition,
            "failed_blue_agent": selection.failed_blue_agent,
            "failure_start_step": selection.failure_start_step,
            "failure_duration_steps": selection.failure_duration_steps,
            "feedback_mode": "none",
            "adapted": False,
            "reason": "static_nonuniform_reset_selection",
            **{f"q_{group}": self.q[group] for group in FAILURE_GROUPS},
        }
