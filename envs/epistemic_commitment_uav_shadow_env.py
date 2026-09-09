"""Zero-training 3DOF shadow task for epistemic commitment semantics.

This adapter is deliberately not a trainable environment.  It reuses the
motion, energy, collision, and flight-envelope calculations of
``UAVIntercept3DEnv`` while adding a minimal task-level commitment event whose
receipt is private.  It is used only to test whether bilateral commitment,
unilateral commitment, defer, and fallback have distinct embodied outcomes.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass

import numpy as np

from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv


COMMIT = "commit"
DEFER = "defer"
FALLBACK = "fallback"
COMMITMENT_ACTIONS = (COMMIT, DEFER, FALLBACK)


@dataclass(frozen=True)
class CommitmentChoice:
    leader: str
    follower: str

    def __post_init__(self) -> None:
        if self.leader not in COMMITMENT_ACTIONS or self.follower not in COMMITMENT_ACTIONS:
            raise ValueError("unknown commitment action")


class EpistemicCommitmentUAVShadowEnv:
    """Minimal embodied commitment task over the existing 3DOF simulator."""

    runtime_format = "epistemic_commitment_uav_shadow_state_v1"
    leader_id = 0
    relay_id = 1
    follower_id = 2
    decision_window_steps = 16

    def __init__(self, delivered: bool, seed: int = 20260909) -> None:
        self.delivered = bool(delivered)
        self.seed = int(seed)
        config = UAVIntercept3DConfig(
            business_grounded_geometry=True,
            communication_dropout_prob=0.0,
            target_policy="straight",
            v16r_mission_mode=True,
            attack_hold_steps=300,
            min_success_step=300,
            max_steps=80,
            seed=self.seed,
        )
        self.base = UAVIntercept3DEnv(config)
        self.executed = False
        self.reset()

    def reset(self) -> np.ndarray:
        self.base.seed(self.seed)
        self.base.reset()
        # Matched geometry.  Delivery is a task message event, not a link-state
        # event, so it must not alter physical observations before the decision.
        self.base.blue_pos = np.asarray(
            [[-6_000.0, -1_000.0, 5_000.0], [-6_500.0, 0.0, 5_000.0], [-6_000.0, 1_000.0, 5_000.0]],
            dtype=np.float32,
        )
        self.base.blue_heading[:] = 0.0
        self.base.blue_gamma[:] = 0.0
        self.base.red_pos = np.asarray([[18_000.0, 0.0, 5_000.0]], dtype=np.float32)
        self.base.red_heading[:] = 0.0
        self.base._update_sensing_and_comm()
        self.executed = False
        return self.actor_observation()

    def actor_observation(self) -> np.ndarray:
        """Return local actor observations without a global delivery flag.

        Columns appended to the base observation are: decision-window open,
        locally-sent commitment, and locally-received commitment.  Therefore
        only the follower can distinguish successful delivery from message loss.
        """

        base_obs = self.base._get_obs().copy()
        private = np.zeros((self.base.num_agents, 3), dtype=np.float32)
        private[:, 0] = 1.0
        private[self.leader_id, 1] = 1.0
        private[self.follower_id, 2] = float(self.delivered)
        return np.concatenate([base_obs, private], axis=1)

    @staticmethod
    def _guidance(action: str, agent_id: int) -> np.ndarray:
        if action == COMMIT:
            return np.asarray([0.0, 0.0], dtype=np.float32)
        if action == DEFER:
            return np.asarray([1.0 if agent_id == 0 else -1.0, 0.0], dtype=np.float32)
        if action == FALLBACK:
            return np.asarray([-1.0 if agent_id == 0 else 1.0, 0.55], dtype=np.float32)
        raise ValueError(f"unknown action: {action}")

    def execute(self, choice: CommitmentChoice) -> dict:
        if self.executed:
            raise RuntimeError("P1C permits one frozen decision window per reset")
        self.executed = True
        initial_pos = self.base.blue_pos.copy()
        initial_energy = self.base.blue_energy.copy()
        infos: list[dict] = []
        for _ in range(self.decision_window_steps):
            guidance = np.zeros((self.base.num_agents, 2), dtype=np.float32)
            guidance[self.leader_id] = self._guidance(choice.leader, self.leader_id)
            guidance[self.follower_id] = self._guidance(choice.follower, self.follower_id)
            _, _, _, _, _, info = self.base.step_guidance(guidance)
            infos.append(info)
            if self.base.done:
                raise RuntimeError("base episode terminated inside the frozen decision window")

        final_pos = self.base.blue_pos.copy()
        displacement = final_pos - initial_pos
        joint_commit = choice.leader == COMMIT and choice.follower == COMMIT
        unilateral_commit = (choice.leader == COMMIT) != (choice.follower == COMMIT)
        graceful_fallback = choice.leader == FALLBACK and choice.follower == FALLBACK
        coordinated_defer = choice.leader == DEFER and choice.follower == DEFER
        leader_progress = float(displacement[self.leader_id, 0])
        follower_progress = float(displacement[self.follower_id, 0])
        leader_follower_distance = float(
            np.linalg.norm(final_pos[self.leader_id] - final_pos[self.follower_id])
        )
        supported_corridor_entry = (
            joint_commit
            and min(leader_progress, follower_progress) >= 3_500.0
            and leader_follower_distance <= 2_500.0
        )
        unsupported_corridor_entry = (
            unilateral_commit
            and max(leader_progress, follower_progress) >= 3_500.0
            and leader_follower_distance > 3_000.0
        )
        # Frozen task endpoint.  It summarizes embodied task commitment; it is
        # not the base environment's learning reward and is never used to train.
        if supported_corridor_entry:
            task_value = 10.0
            outcome = "bilateral_commitment"
        elif unsupported_corridor_entry:
            task_value = -6.0
            outcome = "unilateral_commitment"
        elif graceful_fallback:
            task_value = 2.0
            outcome = "graceful_degradation"
        elif coordinated_defer:
            task_value = 1.0
            outcome = "coordinated_defer"
        else:
            task_value = -1.0
            outcome = "miscoordinated_noncommitment"

        return {
            "outcome": outcome,
            "task_value": task_value,
            "delivered": self.delivered,
            "choice": {"leader": choice.leader, "follower": choice.follower},
            "elapsed_steps": self.decision_window_steps,
            "displacement": displacement.tolist(),
            "energy_cost": (initial_energy - self.base.blue_energy).tolist(),
            "leader_progress": leader_progress,
            "follower_progress": follower_progress,
            "leader_follower_distance": leader_follower_distance,
            "supported_corridor_entry": supported_corridor_entry,
            "unsupported_corridor_entry": unsupported_corridor_entry,
            "joint_commit": joint_commit,
            "unilateral_commit": unilateral_commit,
            "collision": any(float(info["collision"]) > 0.0 for info in infos),
            "constraint_violation": any(float(info["constraint_violation"]) > 0.0 for info in infos),
        }

    def state_dict(self) -> dict:
        return {
            "format": self.runtime_format,
            "delivered": self.delivered,
            "seed": self.seed,
            "executed": self.executed,
            "base": self.base.runtime_state_dict(),
        }

    def load_state_dict(self, state: dict) -> None:
        if state.get("format") != self.runtime_format:
            raise ValueError("incompatible commitment shadow state")
        if bool(state.get("delivered")) != self.delivered or int(state.get("seed")) != self.seed:
            raise ValueError("commitment shadow state belongs to another experiment")
        self.executed = bool(state["executed"])
        self.base.load_runtime_state_dict(deepcopy(state["base"]))
