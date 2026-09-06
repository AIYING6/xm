"""Independent PLR-style replay over the frozen DRTP failure *groups*.

This module implements the published Prioritized Level Replay ingredients for
the existing DRTP training interface, without copying external source code.
The training level is a pre-existing DRTP failure group, not an individual
member: nominal exposure remains exactly 0.50 and the existing uniform member
draw inside each failure group is retained unchanged.  The score is the mean
absolute, unnormalised GAE from a vectorised T-step rollout fragment.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import random

import numpy as np

from algorithms.ri_gmappo.drtp_topology_sampler import (
    DRTPSelection,
    FAILURE_GROUPS,
    GROUP_MEMBERS,
    NOMINAL_GROUP,
    NOMINAL_MASS,
    UNIFORM_Q,
)


PLR_SCORE_TEMPERATURE = 0.10
PLR_STALENESS_COEFFICIENT = 0.10


class PLRTopologySampler:
    """Deterministic group-level PLR with exact runtime-state persistence."""

    uses_completed_return_feedback = False

    def __init__(self, seed: int, total_updates: int):
        self.mode = "plr"
        self.seed = int(seed)
        self.total_updates = int(total_updates)
        if self.total_updates <= 0:
            raise ValueError("total_updates must be positive")
        self.q = {group: UNIFORM_Q for group in FAILURE_GROUPS}
        self.score = {group: 0.0 for group in FAILURE_GROUPS}
        self.last_seen = {group: -1 for group in FAILURE_GROUPS}
        self.seen = {group: False for group in FAILURE_GROUPS}
        self.failure_selection_count = 0
        self.score_update_count = 0
        self.last_score_counts = {group: 0 for group in FAILURE_GROUPS}

    def _rng(self, update: int, env_index: int, episode_index: int) -> random.Random:
        return random.Random(
            self.seed * 1_000_003 + int(update) * 97_003
            + int(env_index) * 10_007 + int(episode_index) * 101
        )

    @staticmethod
    def apply(env, selection: DRTPSelection) -> None:
        env.config.failed_blue_agent = selection.failed_blue_agent
        env.config.node_failure_start_step = selection.failure_start_step
        env.config.node_failure_duration_steps = selection.failure_duration_steps

    def _refresh_q(self) -> None:
        """Published rank-priority plus staleness mixture over failure groups."""
        ordered = sorted(FAILURE_GROUPS, key=lambda group: (-self.score[group], group))
        priorities = {
            group: float((index + 1) ** (-1.0 / PLR_SCORE_TEMPERATURE))
            for index, group in enumerate(ordered)
        }
        priority_total = sum(priorities.values())
        score_q = {group: priorities[group] / priority_total for group in FAILURE_GROUPS}
        stale = {
            group: float(max(1, self.failure_selection_count - self.last_seen[group]))
            for group in FAILURE_GROUPS
        }
        stale_total = sum(stale.values())
        self.q = {
            group: (1.0 - PLR_STALENESS_COEFFICIENT) * score_q[group]
            + PLR_STALENESS_COEFFICIENT * stale[group] / stale_total
            for group in FAILURE_GROUPS
        }
        if not math.isclose(sum(self.q.values()), 1.0, rel_tol=0.0, abs_tol=1e-12):
            raise AssertionError("PLR failure-group probability lost mass")

    def _select_failure_group(self, rng: random.Random) -> tuple[str, str]:
        unseen = [group for group in FAILURE_GROUPS if not self.seen[group]]
        if unseen:
            group = unseen[rng.randrange(len(unseen))]
            reason = "unseen_group_coverage"
        else:
            self._refresh_q()
            draw, cursor = rng.random(), 0.0
            group = FAILURE_GROUPS[-1]
            for candidate in FAILURE_GROUPS:
                cursor += self.q[candidate]
                if draw < cursor:
                    group = candidate
                    break
            reason = "rank_priority_plus_staleness"
        self.failure_selection_count += 1
        self.seen[group] = True
        self.last_seen[group] = self.failure_selection_count
        return group, reason

    def select(self, update: int, env_index: int, episode_index: int) -> DRTPSelection:
        rng = self._rng(update, env_index, episode_index)
        if rng.random() < NOMINAL_MASS:
            group = NOMINAL_GROUP
        else:
            group, _ = self._select_failure_group(rng)
        condition, onset, duration = GROUP_MEMBERS[group][rng.randrange(len(GROUP_MEMBERS[group]))]
        return DRTPSelection(
            group=group,
            condition=condition,
            failure_start_step=onset,
            failure_duration_steps=duration,
            failed_blue_agent=-1 if group == NOMINAL_GROUP else 1,
        )

    def record_rollout_scores(self, advantages: np.ndarray, condition_groups: np.ndarray) -> dict:
        """Update scores from raw GAE without exposing them to PPO tensors."""
        values = np.asarray(advantages, dtype=np.float64)
        groups = np.asarray(condition_groups)
        if values.ndim != 3 or groups.shape != values.shape[:2]:
            raise ValueError("PLR requires advantages[T, env, agent] and groups[T, env]")
        if not np.isfinite(values).all():
            raise ValueError("PLR rollout advantages must be finite")
        counts = {}
        for group in FAILURE_GROUPS:
            mask = groups == group
            counts[group] = int(mask.sum())
            if counts[group]:
                self.score[group] = float(np.abs(values[mask]).mean())
        self.last_score_counts = counts
        self.score_update_count += 1
        if all(self.seen.values()):
            self._refresh_q()
        return self.update_row()

    def maybe_update(self, update: int):  # compatibility; updates happen from rollout GAE.
        return None

    def manifest(self) -> dict:
        payload = {
            "protocol": "DRTP-PLR-STYLE-EXTERNAL-COMPARATOR-V1",
            "mode": self.mode,
            "seed": self.seed,
            "total_updates": self.total_updates,
            "level_mapping": "six frozen DRTP failure groups; within-group member draw remains uniform",
            "nominal_group": NOMINAL_GROUP,
            "nominal_mass": NOMINAL_MASS,
            "failure_groups": list(FAILURE_GROUPS),
            "group_members": {group: [list(member) for member in GROUP_MEMBERS[group]] for group in FAILURE_GROUPS},
            "score": "mean absolute unnormalised GAE over vectorised T-step rollout fragments",
            "rank_priority_temperature": PLR_SCORE_TEMPERATURE,
            "staleness_coefficient": PLR_STALENESS_COEFFICIENT,
            "actor_or_critic_condition_input": False,
            "reward_or_ppo_objective_change": False,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return {**payload, "sampler_hash": hashlib.sha256(encoded).hexdigest()}

    def state_dict(self) -> dict:
        return {
            "format": "plr_topology_sampler_runtime_state_v1",
            "mode": self.mode, "seed": self.seed, "total_updates": self.total_updates,
            "q": dict(self.q), "score": dict(self.score), "last_seen": dict(self.last_seen),
            "seen": dict(self.seen), "failure_selection_count": self.failure_selection_count,
            "score_update_count": self.score_update_count, "last_score_counts": dict(self.last_score_counts),
        }

    def load_state_dict(self, state: dict) -> None:
        if state.get("format") != "plr_topology_sampler_runtime_state_v1":
            raise ValueError("unsupported PLR sampler runtime-state format")
        if str(state.get("mode")) != self.mode or int(state.get("seed")) != self.seed:
            raise ValueError("PLR sampler runtime state is bound to a different mode or seed")
        for field in ("q", "score", "last_seen", "seen", "last_score_counts"):
            if set(state.get(field, {})) != set(FAILURE_GROUPS):
                raise ValueError(f"invalid PLR sampler runtime state field: {field}")
        self.q = {group: float(state["q"][group]) for group in FAILURE_GROUPS}
        self.score = {group: float(state["score"][group]) for group in FAILURE_GROUPS}
        self.last_seen = {group: int(state["last_seen"][group]) for group in FAILURE_GROUPS}
        self.seen = {group: bool(state["seen"][group]) for group in FAILURE_GROUPS}
        self.failure_selection_count = int(state["failure_selection_count"])
        self.score_update_count = int(state["score_update_count"])
        self.last_score_counts = {group: int(state["last_score_counts"][group]) for group in FAILURE_GROUPS}
        if not math.isclose(sum(self.q.values()), 1.0, rel_tol=0.0, abs_tol=1e-10):
            raise ValueError("PLR sampler runtime state has invalid probability mass")
        if not all(math.isfinite(value) and value >= 0.0 for value in self.score.values()):
            raise ValueError("PLR sampler runtime state has invalid scores")

    @staticmethod
    def log_fields() -> list[str]:
        fields = [
            "record_type", "update", "env_index", "episode_index", "group", "condition",
            "failed_blue_agent", "failure_start_step", "failure_duration_steps", "reason",
            "failure_selection_count", "score_update_count",
        ]
        fields += [f"q_{group}" for group in FAILURE_GROUPS]
        fields += [f"score_{group}" for group in FAILURE_GROUPS]
        fields += [f"seen_{group}" for group in FAILURE_GROUPS]
        fields += [f"score_count_{group}" for group in FAILURE_GROUPS]
        return fields

    def _state_row(self) -> dict:
        row = {f"q_{group}": self.q[group] for group in FAILURE_GROUPS}
        row.update({f"score_{group}": self.score[group] for group in FAILURE_GROUPS})
        row.update({f"seen_{group}": self.seen[group] for group in FAILURE_GROUPS})
        row.update({f"score_count_{group}": self.last_score_counts[group] for group in FAILURE_GROUPS})
        return row

    def selection_row(self, update: int, env_index: int, episode_index: int, selection: DRTPSelection) -> dict:
        reason = "nominal_fixed_mass" if selection.group == NOMINAL_GROUP else (
            "unseen_group_coverage" if not all(self.seen.values()) else "rank_priority_plus_staleness"
        )
        return {
            "record_type": "selection", "update": int(update), "env_index": int(env_index),
            "episode_index": int(episode_index), "group": selection.group, "condition": selection.condition,
            "failed_blue_agent": selection.failed_blue_agent, "failure_start_step": selection.failure_start_step,
            "failure_duration_steps": selection.failure_duration_steps, "reason": reason,
            "failure_selection_count": self.failure_selection_count, "score_update_count": self.score_update_count,
            **self._state_row(),
        }

    def update_row(self) -> dict:
        return {
            "record_type": "rollout_score_update", "update": "", "env_index": "", "episode_index": "",
            "group": "", "condition": "", "failed_blue_agent": "", "failure_start_step": "",
            "failure_duration_steps": "", "reason": "raw_gae_rank_priority",
            "failure_selection_count": self.failure_selection_count, "score_update_count": self.score_update_count,
            **self._state_row(),
        }
