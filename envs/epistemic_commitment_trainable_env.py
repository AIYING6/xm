"""Minimal two-stage trainable contract for epistemic task commitment.

This environment is a pre-PPO interface prototype.  It exposes a public link
reliability cue at stage 0, a private message-receipt event at stage 1, and a
single embodied commitment decision.  Physical execution is delegated to the
3DOF shadow adapter.  The actor never receives the global delivery truth.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from envs.epistemic_commitment_uav_shadow_env import (
    COMMIT,
    DEFER,
    FALLBACK,
    CommitmentChoice,
    EpistemicCommitmentUAVShadowEnv,
)


ACTION_COMMIT = 0
ACTION_DEFER = 1
ACTION_FALLBACK = 2
ACTION_TO_NAME = {ACTION_COMMIT: COMMIT, ACTION_DEFER: DEFER, ACTION_FALLBACK: FALLBACK}

RELIABILITY_CONTEXTS = {
    "low": 0.15,
    "middle": 0.45,
    "high": 0.85,
}


@dataclass(frozen=True)
class EpistemicCommitmentEpisodeSpec:
    episode_id: int
    context: str
    delivered: bool

    def __post_init__(self) -> None:
        if self.context not in RELIABILITY_CONTEXTS:
            raise ValueError(f"unknown reliability context: {self.context}")


class EpistemicCommitmentTrainableEnv:
    """Two-stage environment with the repository's standard MARL interface."""

    num_agents = 3
    action_dim = 3
    base_obs_dim = 34
    private_obs_dim = 5
    obs_dim = base_obs_dim + private_obs_dim
    share_obs_dim = num_agents * obs_dim
    leader_id = 0
    relay_id = 1
    follower_id = 2

    def __init__(self, seed: int = 20260909, episode_spec: EpistemicCommitmentEpisodeSpec | None = None) -> None:
        self.seed_value = int(seed)
        self.rng = np.random.default_rng(self.seed_value)
        self.forced_spec = episode_spec
        self.episode_counter = 0
        self.phase = 0
        self.done = False
        self.spec: EpistemicCommitmentEpisodeSpec
        self.shadow: EpistemicCommitmentUAVShadowEnv
        self.reset()

    def seed(self, seed: int) -> None:
        self.seed_value = int(seed)
        self.rng = np.random.default_rng(self.seed_value)

    def _sample_spec(self) -> EpistemicCommitmentEpisodeSpec:
        if self.forced_spec is not None:
            return self.forced_spec
        context = tuple(RELIABILITY_CONTEXTS)[int(self.rng.integers(0, len(RELIABILITY_CONTEXTS)))]
        delivered = bool(self.rng.random() < RELIABILITY_CONTEXTS[context])
        return EpistemicCommitmentEpisodeSpec(self.episode_counter, context, delivered)

    def reset(self) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray]]:
        self.spec = self._sample_spec()
        self.episode_counter += 1
        shadow_seed = self.seed_value + int(self.spec.episode_id) * 17
        self.shadow = EpistemicCommitmentUAVShadowEnv(self.spec.delivered, shadow_seed)
        self.phase = 0
        self.done = False
        return self._observations()

    def _actor_obs(self) -> np.ndarray:
        base = self.shadow.base._get_obs().copy()
        private = np.zeros((self.num_agents, self.private_obs_dim), dtype=np.float32)
        private[:, 0] = float(self.phase == 0)
        private[:, 1] = float(self.phase == 1)
        if self.phase == 0:
            private[:, 2] = RELIABILITY_CONTEXTS[self.spec.context]
        else:
            private[self.leader_id, 3] = 1.0  # locally sent
            private[self.follower_id, 4] = float(self.spec.delivered)  # locally received
        return np.concatenate((base, private), axis=1)

    def _observations(self) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray]]:
        obs = self._actor_obs()
        # CTDE critic input is composed only from the union of legal local
        # observations; no additional global delivery flag is appended.
        flat = obs.reshape(-1)
        share_obs = np.repeat(flat[None, :], self.num_agents, axis=0).astype(np.float32)
        graph_obs = self.shadow.base._get_graph_obs()
        return obs, share_obs, graph_obs

    def step(
        self, actions: np.ndarray | list[int]
    ) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray], np.ndarray, np.ndarray, dict]:
        if self.done:
            raise RuntimeError("Call reset() before stepping a completed episode")
        action_array = np.asarray(actions, dtype=np.int64).reshape(self.num_agents)
        if np.any(action_array < 0) or np.any(action_array >= self.action_dim):
            raise ValueError("commitment action outside [0, 2]")

        if self.phase == 0:
            self.phase = 1
            obs, share_obs, graph_obs = self._observations()
            rewards = np.zeros((self.num_agents, 1), dtype=np.float32)
            dones = np.zeros((self.num_agents, 1), dtype=np.float32)
            return obs, share_obs, graph_obs, rewards, dones, self._info(stage="cue")

        leader_name = ACTION_TO_NAME[int(action_array[self.leader_id])]
        follower_requested = ACTION_TO_NAME[int(action_array[self.follower_id])]
        # A commitment token contains the task-compatible execution plan.  If
        # it was not received, a requested commit executes the stale local plan
        # and becomes physically incompatible with the leader's commitment.
        follower_effective = follower_requested
        stale_token_commit = follower_requested == COMMIT and not self.spec.delivered
        if stale_token_commit:
            follower_effective = FALLBACK
        physical = self.shadow.execute(CommitmentChoice(leader_name, follower_effective))

        if leader_name == COMMIT and follower_requested == COMMIT and self.spec.delivered:
            task_value = 10.0
            endpoint = "compatible_bilateral_commitment"
        elif leader_name == COMMIT or follower_requested == COMMIT:
            task_value = -8.0
            endpoint = "incompatible_or_unilateral_commitment"
        elif leader_name == DEFER and follower_requested == DEFER:
            task_value = 5.0 if self.spec.delivered else 1.0
            endpoint = "coordinated_defer"
        elif leader_name == FALLBACK and follower_requested == FALLBACK:
            task_value = 2.0
            endpoint = "graceful_fallback"
        else:
            task_value = -1.0
            endpoint = "miscoordinated_noncommitment"

        self.done = True
        obs, share_obs, graph_obs = self._observations()
        rewards = np.full((self.num_agents, 1), task_value, dtype=np.float32)
        dones = np.ones((self.num_agents, 1), dtype=np.float32)
        info = self._info(stage="decision")
        info.update(
            {
                "endpoint": endpoint,
                "task_value": task_value,
                "leader_action": leader_name,
                "follower_requested_action": follower_requested,
                "follower_effective_action": follower_effective,
                "stale_token_commit": float(stale_token_commit),
                "single_sided_commitment": float(endpoint == "incompatible_or_unilateral_commitment"),
                "bilateral_commitment_success": float(endpoint == "compatible_bilateral_commitment"),
                "fallback": float(endpoint == "graceful_fallback"),
                "defer": float(endpoint == "coordinated_defer"),
                "collision": float(physical["collision"]),
                "constraint_violation": float(physical["constraint_violation"]),
                "energy_cost": float(sum(physical["energy_cost"])),
                "physical_outcome": physical["outcome"],
            }
        )
        return obs, share_obs, graph_obs, rewards, dones, info

    def _info(self, stage: str) -> dict:
        return {
            "episode_id": int(self.spec.episode_id),
            "context": self.spec.context,
            "reliability_prior": RELIABILITY_CONTEXTS[self.spec.context],
            "stage": stage,
            # Evaluation telemetry only.  This dictionary is not an actor input.
            "delivered": float(self.spec.delivered),
        }


def make_balanced_evaluation_tape(start_episode_id: int = 910_000) -> list[EpistemicCommitmentEpisodeSpec]:
    """Create 300 frozen episodes with exact context-level delivery rates."""

    specs: list[EpistemicCommitmentEpisodeSpec] = []
    episode_id = int(start_episode_id)
    for context, probability in RELIABILITY_CONTEXTS.items():
        delivered_count = int(round(100 * probability))
        for index in range(100):
            specs.append(EpistemicCommitmentEpisodeSpec(episode_id, context, index < delivered_count))
            episode_id += 1
    return specs
