"""Synchronized fixed-exposure sampler for TGTR-PPO mechanism audits.

The sampler has no return-dependent state.  Environment streams are assigned
once to a topology group and to either the design or certificate split.  The
assignment is training metadata only and is never appended to observations.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from algorithms.ri_gmappo.drtp_topology_sampler import (
    FAILURE_GROUPS,
    GROUP_MEMBERS,
    NOMINAL_GROUP,
    DRTPSelection,
)


TGTR_SAMPLER_FORMAT = "tgtr_synchronized_topology_sampler_v1"
TGTR_NUM_ENVS = 24
TGTR_DESIGN = "design"
TGTR_CERTIFICATE = "certificate"
NOMINAL_STREAMS = tuple(range(12))
FAILURE_STREAMS = tuple(range(12, 24))


class SynchronizedTopologyGroupSampler:
    """Fixed 12 nominal + two-per-failure-group stream assignment."""

    uses_completed_return_feedback = False

    def __init__(self, seed: int, num_envs: int = TGTR_NUM_ENVS):
        if int(num_envs) != TGTR_NUM_ENVS:
            raise ValueError(f"TGTR synchronized sampler requires exactly {TGTR_NUM_ENVS} environments")
        self.seed = int(seed)
        self.num_envs = int(num_envs)

    @staticmethod
    def apply(env: Any, selection: DRTPSelection) -> None:
        env.config.failed_blue_agent = selection.failed_blue_agent
        env.config.node_failure_start_step = selection.failure_start_step
        env.config.node_failure_duration_steps = selection.failure_duration_steps

    @staticmethod
    def group_for_env(env_index: int) -> str:
        index = int(env_index)
        if index in NOMINAL_STREAMS:
            return NOMINAL_GROUP
        if index not in FAILURE_STREAMS:
            raise ValueError(f"invalid TGTR environment index: {index}")
        return FAILURE_GROUPS[(index - 12) // 2]

    @staticmethod
    def split_for_env(env_index: int) -> str:
        index = int(env_index)
        if index in NOMINAL_STREAMS:
            return TGTR_DESIGN if index < 6 else TGTR_CERTIFICATE
        if index not in FAILURE_STREAMS:
            raise ValueError(f"invalid TGTR environment index: {index}")
        return TGTR_DESIGN if (index - 12) % 2 == 0 else TGTR_CERTIFICATE

    def select(self, update: int, env_index: int, episode_index: int) -> DRTPSelection:
        del update
        group = self.group_for_env(env_index)
        members = GROUP_MEMBERS[group]
        member_index = (self.seed + int(env_index) * 17 + int(episode_index)) % len(members)
        condition, onset, duration = members[member_index]
        return DRTPSelection(
            group=group,
            condition=condition,
            failure_start_step=onset,
            failure_duration_steps=duration,
            failed_blue_agent=-1 if group == NOMINAL_GROUP else 1,
        )

    def record_completed_return(self, selection: DRTPSelection, episode_return: float) -> None:
        del selection, episode_return

    def maybe_update(self, update: int) -> None:
        del update
        return None

    def state_dict(self) -> dict:
        return {"format": TGTR_SAMPLER_FORMAT, "seed": self.seed, "num_envs": self.num_envs}

    def load_state_dict(self, state: dict) -> None:
        if state != self.state_dict():
            raise ValueError("TGTR synchronized sampler state does not match configuration")

    def manifest(self) -> dict:
        assignments = [
            {"env_index": index, "group": self.group_for_env(index), "split": self.split_for_env(index)}
            for index in range(self.num_envs)
        ]
        payload = {
            "protocol": "TGTR-PPO-C1-SYNCHRONIZED-FIXED-EXPOSURE-V1",
            "format": TGTR_SAMPLER_FORMAT,
            "seed": self.seed,
            "num_envs": self.num_envs,
            "nominal_mass": 0.5,
            "failure_group_mass": {group: 1.0 / 12.0 for group in FAILURE_GROUPS},
            "assignments": assignments,
            "return_adaptive_state": False,
            "actor_or_critic_condition_input": False,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return {**payload, "sampler_hash": hashlib.sha256(encoded).hexdigest()}

    @staticmethod
    def log_fields() -> list[str]:
        return [
            "record_type", "update", "env_index", "episode_index", "group", "split",
            "condition", "failed_blue_agent", "failure_start_step", "failure_duration_steps", "reason",
        ]

    def selection_row(self, update: int, env_index: int, episode_index: int, selection: DRTPSelection) -> dict:
        return {
            "record_type": "selection",
            "update": int(update),
            "env_index": int(env_index),
            "episode_index": int(episode_index),
            "group": selection.group,
            "split": self.split_for_env(env_index),
            "condition": selection.condition,
            "failed_blue_agent": int(selection.failed_blue_agent),
            "failure_start_step": int(selection.failure_start_step),
            "failure_duration_steps": int(selection.failure_duration_steps),
            "reason": "tgtr_fixed_stream_assignment",
        }

    def split_matrix(self, rollout_steps: int):
        import numpy as np

        row = np.asarray([self.split_for_env(index) for index in range(self.num_envs)], dtype="<U11")
        return np.repeat(row[None, :], int(rollout_steps), axis=0)
