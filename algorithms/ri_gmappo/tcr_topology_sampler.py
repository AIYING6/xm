"""Fixed-exposure topology sampler for UTR/SPC/TCR technical work.

This sampler is intentionally stateless with respect to returns: it has no
adaptive weights, EMA, difficulty, or completed-return feedback.  It assigns
two of four environment streams to nominal operation and two to uniformly
cycled failure groups, so every frozen 4x64 rollout contains 128 samples of
each condition class.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

from algorithms.ri_gmappo.drtp_topology_sampler import (
    FAILURE_GROUPS,
    GROUP_MEMBERS,
    NOMINAL_GROUP,
    DRTPSelection,
)


TCR_SAMPLER_FORMAT = "fixed_stratified_topology_sampler_v1"
NOMINAL_STREAMS = (0, 1)
FAILURE_STREAMS = (2, 3)


class FixedStratifiedTopologySampler:
    """Training-only fixed sampler for the Phase-B UTR/SPC/TCR contract."""

    uses_completed_return_feedback = False

    def __init__(self, seed: int, num_envs: int):
        if int(num_envs) != 4:
            raise ValueError("fixed stratified topology sampler requires exactly four environments")
        self.seed = int(seed)
        self.num_envs = int(num_envs)

    @staticmethod
    def apply(env: Any, selection: DRTPSelection) -> None:
        env.config.failed_blue_agent = selection.failed_blue_agent
        env.config.node_failure_start_step = selection.failure_start_step
        env.config.node_failure_duration_steps = selection.failure_duration_steps

    def _failure_group(self, env_index: int, episode_index: int) -> str:
        if env_index not in FAILURE_STREAMS:
            raise ValueError("only designated failure streams may request a failure group")
        stream_offset = FAILURE_STREAMS.index(int(env_index))
        return FAILURE_GROUPS[(self.seed + stream_offset + int(episode_index)) % len(FAILURE_GROUPS)]

    def select(self, update: int, env_index: int, episode_index: int) -> DRTPSelection:
        del update
        env_index = int(env_index)
        if env_index in NOMINAL_STREAMS:
            condition, onset, duration = GROUP_MEMBERS[NOMINAL_GROUP][0]
            return DRTPSelection(NOMINAL_GROUP, condition, onset, duration, -1)
        group = self._failure_group(env_index, episode_index)
        members = GROUP_MEMBERS[group]
        member_index = (self.seed + int(env_index) * 17 + int(episode_index)) % len(members)
        condition, onset, duration = members[member_index]
        return DRTPSelection(group, condition, onset, duration, 1)

    def record_completed_return(self, selection: DRTPSelection, episode_return: float) -> None:
        del selection, episode_return
        # Explicit no-op: fixed exposure must not depend on return history.

    def maybe_update(self, update: int) -> None:
        del update
        return None

    def state_dict(self) -> dict:
        return {"format": TCR_SAMPLER_FORMAT, "seed": self.seed, "num_envs": self.num_envs}

    def load_state_dict(self, state: dict) -> None:
        if state != self.state_dict():
            raise ValueError("fixed stratified sampler runtime state does not match configuration")

    def manifest(self) -> dict:
        payload = {
            "protocol": "TCR-SPC-PHASE-B-FIXED-EXPOSURE-V1",
            "sampler": "fixed_stratified",
            "seed": self.seed,
            "num_envs": self.num_envs,
            "nominal_streams": list(NOMINAL_STREAMS),
            "failure_streams": list(FAILURE_STREAMS),
            "nominal_mass": 0.5,
            "failure_groups": list(FAILURE_GROUPS),
            "conditional_failure_weights": {group: 1.0 / len(FAILURE_GROUPS) for group in FAILURE_GROUPS},
            "actor_or_critic_condition_input": False,
            "return_adaptive_state": False,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return {**payload, "sampler_hash": hashlib.sha256(encoded).hexdigest()}

    @staticmethod
    def log_fields() -> list[str]:
        return [
            "record_type", "update", "env_index", "episode_index", "group", "condition",
            "failed_blue_agent", "failure_start_step", "failure_duration_steps", "reason",
        ]

    def selection_row(self, update: int, env_index: int, episode_index: int, selection: DRTPSelection) -> dict:
        return {
            "record_type": "selection",
            "update": int(update),
            "env_index": int(env_index),
            "episode_index": int(episode_index),
            "group": selection.group,
            "condition": selection.condition,
            "failed_blue_agent": int(selection.failed_blue_agent),
            "failure_start_step": int(selection.failure_start_step),
            "failure_duration_steps": int(selection.failure_duration_steps),
            "reason": "fixed_stratified_reset_selection",
        }
