"""Multi-stage 3DOF UAV task commitment under private message delivery.

This is a zero-training Q0 implementation.  Communication truth drives only
the message event scheduler and evaluator telemetry.  Actor observations expose
local send/receipt records.  Mission endpoints are reconstructed from the
closed-loop trajectory produced by ``UAVIntercept3DEnv.step_guidance``.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass

import numpy as np

from envs.uav_intercept_3d_env import UAVIntercept3DConfig, UAVIntercept3DEnv


MODE_COMMIT = 0
MODE_DEFER = 1
MODE_FALLBACK = 2
MODE_NAMES = ("commit", "defer", "fallback")

PLAN_DELIVERY = ("delivered", "lost", "delayed")
ACK_DELIVERY = ("delivered", "lost", "not_applicable")
PLAN_FRESHNESS = ("current", "stale")
LINK_PRIORS = {"low": 0.2, "middle": 0.5, "high": 0.8}
URGENCY_WINDOWS = {"relaxed": 8, "tight": 6}


@dataclass(frozen=True)
class P3CommunicationSpec:
    plan_delivery: str
    ack_delivery: str
    plan_freshness: str
    public_link_context: str = "middle"
    task_urgency: str = "relaxed"

    def __post_init__(self) -> None:
        if self.plan_delivery not in PLAN_DELIVERY:
            raise ValueError("unknown plan delivery condition")
        if self.ack_delivery not in ACK_DELIVERY:
            raise ValueError("unknown acknowledgement condition")
        if self.plan_freshness not in PLAN_FRESHNESS:
            raise ValueError("unknown plan freshness condition")
        if self.public_link_context not in LINK_PRIORS:
            raise ValueError("unknown public link context")
        if self.task_urgency not in URGENCY_WINDOWS:
            raise ValueError("unknown task urgency")
        if self.plan_delivery != "delivered" and self.ack_delivery != "not_applicable":
            raise ValueError("acknowledgement is inapplicable before plan receipt")


class EpistemicCommitmentP3Env:
    """Eight-epoch commitment task with continuous closed-loop guidance."""

    runtime_format = "epistemic_commitment_p3_runtime_v1"
    num_agents = 3
    leader_id = 0
    relay_id = 1
    follower_id = 2
    decision_epochs = 8
    physical_steps_per_epoch = 8
    base_obs_dim = 34
    private_obs_dim = 11
    obs_dim = base_obs_dim + private_obs_dim
    share_obs_dim = num_agents * obs_dim
    action_shape = (num_agents, 3)  # mode, turn residual, climb residual

    def __init__(self, spec: P3CommunicationSpec, seed: int = 20260909) -> None:
        self.spec = spec
        self.seed_value = int(seed)
        cfg = UAVIntercept3DConfig(
            business_grounded_geometry=True,
            communication_dropout_prob=0.0,
            target_policy="straight",
            v16r_mission_mode=True,
            attack_hold_steps=300,
            min_success_step=300,
            max_steps=80,
            seed=self.seed_value,
        )
        self.base = UAVIntercept3DEnv(cfg)
        self.reset()

    def reset(self):
        self.base.seed(self.seed_value)
        self.base.reset()
        self.base.blue_pos = np.asarray(
            [[-10_500.0, -1_000.0, 5_000.0], [-11_000.0, 0.0, 5_000.0], [-10_500.0, 1_000.0, 5_000.0]],
            dtype=np.float32,
        )
        self.base.blue_heading[:] = 0.0
        self.base.blue_gamma[:] = 0.0
        self.base.red_pos = np.asarray([[18_000.0, 0.0, 5_000.0]], dtype=np.float32)
        self.base.red_heading[:] = 0.0
        self.base._update_sensing_and_comm()
        self.epoch = 0
        self.done = False
        self.sent_plan_version = 1
        self.plan_route_sign = 1
        self.follower_route_sign = 0
        self.leader_ack_route_sign = 0
        self.follower_plan_version = -1
        self.leader_ack_version = -1
        self.plan_receipt_epoch = -1
        self.ack_receipt_epoch = -1
        self.previous_modes = np.full(self.num_agents, MODE_DEFER, dtype=np.int64)
        self.initial_pos = self.base.blue_pos.copy()
        self.initial_energy = self.base.blue_energy.copy()
        self.risk_entry_epoch = np.full(self.num_agents, -1, dtype=np.int64)
        self.task_entry_epoch = np.full(self.num_agents, -1, dtype=np.int64)
        self.unilateral_risk_observed = False
        self.mode_history: list[list[int]] = []
        self.trajectory: list[dict] = []
        return self._observations()

    def _deliver_events(self) -> None:
        if self.spec.plan_delivery == "delivered" and self.epoch == 2:
            self.follower_plan_version = 1 if self.spec.plan_freshness == "current" else 0
            self.follower_route_sign = (
                self.plan_route_sign if self.spec.plan_freshness == "current" else -self.plan_route_sign
            )
            self.plan_receipt_epoch = self.epoch
        elif self.spec.plan_delivery == "delayed" and self.epoch == 4:
            self.follower_plan_version = 1 if self.spec.plan_freshness == "current" else 0
            self.follower_route_sign = (
                self.plan_route_sign if self.spec.plan_freshness == "current" else -self.plan_route_sign
            )
            self.plan_receipt_epoch = self.epoch
        if (
            self.spec.plan_delivery == "delivered"
            and self.spec.ack_delivery == "delivered"
            and self.plan_receipt_epoch >= 0
            and self.epoch == self.plan_receipt_epoch + 1
        ):
            self.leader_ack_version = self.follower_plan_version
            self.leader_ack_route_sign = self.follower_route_sign
            self.ack_receipt_epoch = self.epoch

    def _private_features(self) -> np.ndarray:
        private = np.zeros((self.num_agents, self.private_obs_dim), dtype=np.float32)
        private[:, 0] = self.epoch / self.decision_epochs
        private[:, 1] = LINK_PRIORS[self.spec.public_link_context]
        private[:, 2] = max(0.0, (URGENCY_WINDOWS[self.spec.task_urgency] - self.epoch) / self.decision_epochs)
        private[self.leader_id, 3] = float(self.epoch >= 1)
        private[self.leader_id, 4] = float(self.plan_route_sign)
        if self.follower_plan_version >= 0:
            private[self.follower_id, 5] = float(self.follower_route_sign)
            private[self.follower_id, 6] = (self.follower_plan_version + 1.0) / 2.0
            private[self.follower_id, 7] = (self.epoch - self.plan_receipt_epoch) / self.decision_epochs
        if self.leader_ack_version >= 0:
            private[self.leader_id, 6] = (self.leader_ack_version + 1.0) / 2.0
            private[self.leader_id, 7] = (self.epoch - self.ack_receipt_epoch) / self.decision_epochs
        for agent_id in range(self.num_agents):
            private[agent_id, 8 + int(self.previous_modes[agent_id])] = 1.0
        return private

    def _observations(self):
        obs = np.concatenate((self.base._get_obs().copy(), self._private_features()), axis=1)
        union = obs.reshape(-1)
        share_obs = np.repeat(union[None, :], self.num_agents, axis=0).astype(np.float32)
        return obs.astype(np.float32), share_obs, self.base._get_graph_obs()

    def _mode_guidance(self, mode: int, agent_id: int) -> np.ndarray:
        if mode == MODE_COMMIT:
            route_sign = 0
            if agent_id == self.leader_id:
                route_sign = self.plan_route_sign
            elif agent_id == self.follower_id:
                # The shared route token maps to mirrored role-relative turns:
                # the leader starts below the corridor and the follower above it.
                route_sign = -self.follower_route_sign
            # Normalize for the heterogeneous turn-rate envelopes so matching
            # route tokens describe the same physical curvature.
            scale = (
                0.22
                if agent_id == self.leader_id
                else 0.22 * (0.035 / 185.0) * (205.0 / 0.052)
            )
            return np.asarray([scale * route_sign, 0.0], dtype=np.float32)
        if mode == MODE_DEFER:
            return np.asarray([0.0, 0.0], dtype=np.float32)
        if mode == MODE_FALLBACK:
            return np.asarray([-1.0 if agent_id == 0 else 1.0, 0.35], dtype=np.float32)
        raise ValueError("unknown task mode")

    def _parse_actions(self, actions) -> tuple[np.ndarray, np.ndarray]:
        value = np.asarray(actions, dtype=np.float32)
        if value.shape != self.action_shape or not np.isfinite(value).all():
            raise ValueError(f"actions must be finite with shape {self.action_shape}")
        modes = np.rint(value[:, 0]).astype(np.int64)
        if np.any(modes < 0) or np.any(modes > 2):
            raise ValueError("task mode outside [0, 2]")
        residual = np.clip(value[:, 1:3], -1.0, 1.0)
        guidance = np.zeros((self.num_agents, 2), dtype=np.float32)
        for agent_id in range(self.num_agents):
            if agent_id == self.relay_id:
                guidance[agent_id] = residual[agent_id]
            else:
                guidance[agent_id] = np.clip(
                    self._mode_guidance(int(modes[agent_id]), agent_id) + 0.25 * residual[agent_id],
                    -1.0,
                    1.0,
                )
        return modes, guidance

    def _update_crossings(self, modes: np.ndarray) -> None:
        for agent_id in (self.leader_id, self.follower_id):
            x = float(self.base.blue_pos[agent_id, 0])
            if x >= 1_000.0 and self.risk_entry_epoch[agent_id] < 0:
                self.risk_entry_epoch[agent_id] = self.epoch
            if x >= 3_500.0 and self.task_entry_epoch[agent_id] < 0:
                self.task_entry_epoch[agent_id] = self.epoch
        entered = self.risk_entry_epoch[[self.leader_id, self.follower_id]] >= 0
        if bool(entered[0] != entered[1]):
            self.unilateral_risk_observed = True
        elif bool(np.all(entered)):
            self.unilateral_risk_observed = bool(
                abs(
                    int(self.risk_entry_epoch[self.leader_id])
                    - int(self.risk_entry_epoch[self.follower_id])
                )
                > 1
            )

    def _terminal_endpoint(self) -> dict:
        leader_task = int(self.task_entry_epoch[self.leader_id])
        follower_task = int(self.task_entry_epoch[self.follower_id])
        separation = float(
            np.linalg.norm(self.base.blue_pos[self.leader_id] - self.base.blue_pos[self.follower_id])
        )
        leader_corridor_error = abs(float(self.base.blue_pos[self.leader_id, 1]) - 500.0)
        follower_corridor_error = abs(float(self.base.blue_pos[self.follower_id, 1]) + 800.0)
        corridor_aligned = leader_corridor_error <= 1_000.0 and follower_corridor_error <= 1_000.0
        joint_success = (
            leader_task >= 0
            and follower_task >= 0
            and abs(leader_task - follower_task) <= 1
            and separation <= 2_500.0
            and corridor_aligned
        )
        retreat_evidence = False
        arrested_entry_evidence = False
        if len(self.trajectory) >= 3:
            recent_x = np.asarray(
                [
                    row["positions"][[self.leader_id, self.follower_id], 0]
                    for row in self.trajectory[-3:]
                ],
                dtype=np.float32,
            )
            recent_dx = np.diff(recent_x, axis=0)
            retreat_evidence = bool(np.all(recent_dx < 0.0))
            arrested_entry_evidence = bool(
                np.all(recent_dx[:, 1] < 0.0)
                and recent_dx[1, 0] < recent_dx[0, 0]
                and recent_dx[1, 0] < 500.0
            )
        recovered = (
            self.unilateral_risk_observed
            and (
                (leader_task < 0 and follower_task < 0)
                or retreat_evidence
                or arrested_entry_evidence
            )
            and not joint_success
        )
        fallback_complete = (
            retreat_evidence
            and leader_task < 0
            and follower_task < 0
            and not self.unilateral_risk_observed
        )
        corridor_mismatch_entry = leader_task >= 0 and follower_task >= 0 and not joint_success
        unsupported = (
            self.unilateral_risk_observed or corridor_mismatch_entry
        ) and not recovered and not joint_success
        if self.base.collision:
            endpoint, task_value = "collision", -10.0
        elif self.base.constraint_violation:
            endpoint, task_value = "constraint_violation", -10.0
        elif joint_success:
            endpoint, task_value = "joint_task_success", 10.0
        elif recovered:
            endpoint, task_value = "recovery_after_mismatch", 3.0
        elif fallback_complete:
            endpoint, task_value = "graceful_fallback_completion", 2.0
        elif unsupported:
            endpoint, task_value = "unsupported_corridor_entry", -8.0
        else:
            endpoint, task_value = "timeout", 0.0
        return {
            "endpoint": endpoint,
            "task_value": task_value,
            "joint_task_success": float(joint_success),
            "unsupported_corridor_entry": float(unsupported),
            "recovery_after_mismatch": float(recovered),
            "graceful_fallback_completion": float(fallback_complete),
            "timeout": float(endpoint == "timeout"),
            "collision": float(endpoint == "collision"),
            "constraint_violation": float(endpoint == "constraint_violation"),
            "leader_task_entry_epoch": leader_task,
            "follower_task_entry_epoch": follower_task,
            "final_pair_separation": separation,
            "leader_corridor_error": leader_corridor_error,
            "follower_corridor_error": follower_corridor_error,
            "corridor_aligned": float(corridor_aligned),
        }

    def step(self, actions):
        if self.done:
            raise RuntimeError("Call reset() before stepping a completed episode")
        self._deliver_events()
        modes, guidance = self._parse_actions(actions)
        base_infos = []
        for _ in range(self.physical_steps_per_epoch):
            _, _, _, _, _, info = self.base.step_guidance(guidance)
            base_infos.append(info)
            if self.base.done:
                break
        self.previous_modes = modes.copy()
        self.mode_history.append(modes.tolist())
        self._update_crossings(modes)
        self.trajectory.append(
            {
                "epoch": self.epoch,
                "positions": self.base.blue_pos.copy(),
                "modes": modes.copy(),
                "guidance": guidance.copy(),
            }
        )
        self.epoch += 1
        self.done = bool(self.base.done or self.epoch >= self.decision_epochs)
        endpoint = self._terminal_endpoint() if self.done else {}
        task_value = float(endpoint.get("task_value", 0.0))
        rewards = np.full((self.num_agents, 1), task_value, dtype=np.float32)
        dones = np.full((self.num_agents, 1), float(self.done), dtype=np.float32)
        obs, share_obs, graph_obs = self._observations()
        info = {
            "epoch": self.epoch,
            "plan_delivery_truth": self.spec.plan_delivery,
            "ack_delivery_truth": self.spec.ack_delivery,
            "plan_freshness_truth": self.spec.plan_freshness,
            "follower_plan_version": self.follower_plan_version,
            "leader_ack_version": self.leader_ack_version,
            "unilateral_risk_observed": float(self.unilateral_risk_observed),
            "collision": float(any(float(x["collision"]) > 0 for x in base_infos)),
            "constraint_violation": float(any(float(x["constraint_violation"]) > 0 for x in base_infos)),
            "energy_cost": float(np.sum(self.initial_energy - self.base.blue_energy)),
        }
        info.update(endpoint)
        return obs, share_obs, graph_obs, rewards, dones, info

    def state_dict(self) -> dict:
        return {
            "format": self.runtime_format,
            "spec": self.spec,
            "seed_value": self.seed_value,
            "base": self.base.runtime_state_dict(),
            "epoch": self.epoch,
            "done": self.done,
            "sent_plan_version": self.sent_plan_version,
            "plan_route_sign": self.plan_route_sign,
            "follower_route_sign": self.follower_route_sign,
            "leader_ack_route_sign": self.leader_ack_route_sign,
            "follower_plan_version": self.follower_plan_version,
            "leader_ack_version": self.leader_ack_version,
            "plan_receipt_epoch": self.plan_receipt_epoch,
            "ack_receipt_epoch": self.ack_receipt_epoch,
            "previous_modes": self.previous_modes.copy(),
            "initial_pos": self.initial_pos.copy(),
            "initial_energy": self.initial_energy.copy(),
            "risk_entry_epoch": self.risk_entry_epoch.copy(),
            "task_entry_epoch": self.task_entry_epoch.copy(),
            "unilateral_risk_observed": self.unilateral_risk_observed,
            "mode_history": deepcopy(self.mode_history),
            "trajectory": deepcopy(self.trajectory),
        }

    def load_state_dict(self, state: dict) -> None:
        if state.get("format") != self.runtime_format:
            raise ValueError("incompatible P3 runtime state")
        if state.get("spec") != self.spec or int(state.get("seed_value")) != self.seed_value:
            raise ValueError("P3 runtime state belongs to another task")
        self.base.load_runtime_state_dict(deepcopy(state["base"]))
        for name in (
            "epoch",
            "done",
            "sent_plan_version",
            "plan_route_sign",
            "follower_route_sign",
            "leader_ack_route_sign",
            "follower_plan_version",
            "leader_ack_version",
            "plan_receipt_epoch",
            "ack_receipt_epoch",
            "previous_modes",
            "initial_pos",
            "initial_energy",
            "risk_entry_epoch",
            "task_entry_epoch",
            "unilateral_risk_observed",
            "mode_history",
            "trajectory",
        ):
            setattr(self, name, deepcopy(state[name]))
