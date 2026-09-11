"""Optional LBF adapter for C1's masked-capability public benchmark.

The adapter deliberately exposes each actor's own capacity but removes its
teammate's capacity from execution-time observations.  Positions, food state,
public rewards, and legal action masks remain available.  A centralized critic
may receive the simulator state during training; that training-only signal is
identical for every future C1 arm.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class C1LBFConfig:
    seed: int
    horizon: int = 16
    field_size: tuple[int, int] = (5, 5)
    # Default-off so the completed G1 protocol stays unchanged.  The C1
    # capability-commitment pilot may expose one public receipt saying that
    # both actors requested a joint LOAD on the preceding step.  It does not
    # reveal either actor's level, the critic state, or the joint action beyond
    # that public receipt.
    emit_public_joint_load_receipt: bool = False


class C1MaskedLBFAdapter:
    """Two-player Level-Based Foraging adapter with an explicit information boundary."""

    num_agents = 2
    action_dim = 6

    def __init__(self, config: C1LBFConfig):
        # An isolated LBF virtual environment can be supplied without adding
        # optional benchmark dependencies to the maintained UAV environment.
        extra_site_packages = os.environ.get("C1_LBF_SITE_PACKAGES")
        if extra_site_packages and extra_site_packages not in sys.path:
            sys.path.append(extra_site_packages)
        try:
            from lbforaging.foraging.environment import ForagingEnv
        except ImportError as exc:  # pragma: no cover - only executed in optional env
            raise ImportError(
                "C1 requires an isolated environment with lbforaging==2.0.0; "
                "see requirements-c1-lbf.txt."
            ) from exc
        self.config = config
        self._env = ForagingEnv(
            players=2, min_player_level=1, max_player_level=3,
            min_food_level=1, max_food_level=3, field_size=config.field_size,
            max_num_food=2, sight=max(config.field_size),
            max_episode_steps=config.horizon, force_coop=False,
            normalize_reward=False, observe_agent_levels=False,
        )
        from lbforaging.foraging.environment import Action
        self._load_action_id = int(Action.LOAD.value)
        self._last_obs: tuple[np.ndarray, ...] | None = None

    def reset(self, *, seed: int | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        observations, _ = self._env.reset(seed=self.config.seed if seed is None else seed)
        self._last_obs = tuple(np.asarray(obs, dtype=np.float32) for obs in observations)
        self._last_joint_load_receipt = 0.0
        return self.actor_observation(), self.critic_observation(), self.action_masks()

    def actor_observation(self) -> np.ndarray:
        """Public LBF observation plus own level; teammate level is never appended."""
        assert self._last_obs is not None
        own = np.asarray([player.level / 3.0 for player in self._env.players], dtype=np.float32)[:, None]
        actor = np.concatenate((np.stack(self._last_obs), own), axis=1)
        if self.config.emit_public_joint_load_receipt:
            receipt = np.full((self.num_agents, 1), self._last_joint_load_receipt, dtype=np.float32)
            actor = np.concatenate((actor, receipt), axis=1)
        return actor

    def critic_observation(self) -> np.ndarray:
        """Training-only centralized state, replicated once per actor."""
        assert self._last_obs is not None
        public = np.concatenate(self._last_obs, axis=0)
        levels = np.asarray([player.level / 3.0 for player in self._env.players], dtype=np.float32)
        state = np.concatenate((public, levels), axis=0)
        return np.repeat(state[None, :], self.num_agents, axis=0)

    def action_masks(self) -> np.ndarray:
        mask = np.zeros((self.num_agents, self.action_dim), dtype=np.float32)
        for index, player in enumerate(self._env.players):
            for action in self._env._valid_actions[player]:
                mask[index, int(action.value)] = 1.0
        return mask

    def step(self, actions: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
        joint_actions = np.asarray(actions, dtype=np.int64).reshape(self.num_agents)
        # The receipt is a public coordination event: both agents asked to
        # jointly LOAD.  It intentionally contains no capacity or critic-only
        # information.  It is recorded before the transition and exposed only
        # through the next actor observation.
        self._last_joint_load_receipt = float(np.all(joint_actions == self._load_action_id))
        observations, rewards, terminated, truncated, _ = self._env.step(tuple(int(a) for a in joint_actions))
        self._last_obs = tuple(np.asarray(obs, dtype=np.float32) for obs in observations)
        done = bool(terminated or truncated)
        remaining = int(np.count_nonzero(self._env.field))
        completed = 2 - remaining
        info = {
            "completed_foods": completed,
            "completed_all": float(remaining == 0),
            "timeout": float(bool(truncated) and remaining > 0),
            "remaining_foods": remaining,
            "public_joint_load_receipt": self._last_joint_load_receipt,
        }
        return (
            self.actor_observation(), self.critic_observation(), self.action_masks(),
            np.asarray(rewards, dtype=np.float32),
            np.full((self.num_agents,), done, dtype=bool), info,
        )
