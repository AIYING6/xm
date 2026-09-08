"""Independent 6-UAV task adapter with policy-controlled relay forwarding.

The legacy redundant-topology task intentionally makes relays automatic
forwarders.  This V3 adapter is a separate task family: a relay chooses which
objective to forward in each limited-capacity time slot, while terminals need
fresh legal support to advance.  It does not modify the legacy environment or
any completed DRTP evidence chain.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from envs.redundant_topology_uav_env import (
    ROLE_RELAY,
    ROLE_SCOUT,
    ROLE_TERMINAL,
    RedundantTopologyConfig,
    RedundantTopologyUAVEnv,
)


@dataclass(frozen=True)
class SustainedSupportTopologyConfig:
    """Frozen V3 task semantics, separate from learner and sampler settings."""

    base: RedundantTopologyConfig
    scout_x: float = 0.0
    relay_x: float = 35.0
    terminal_x: float = 70.0
    objective_x: float = 100.0
    relay_packet_capacity: int = 1
    support_max_age: int = 0
    fault_transition: int = 2

    def __post_init__(self) -> None:
        if self.base.scouts != 2 or self.base.relays != 2 or self.base.terminals != 2:
            raise ValueError("V3 Q0 freezes the 2-scout/2-relay/2-terminal task")
        if self.base.num_objectives != 2:
            raise ValueError("V3 Q0 freezes two objectives")
        if self.relay_packet_capacity != 1:
            raise ValueError("V3 Q0 freezes one packet per relay time slot")
        if self.support_max_age != 0:
            raise ValueError("V3 Q0 requires same-transition support")
        if self.fault_transition < 2 or self.fault_transition >= self.base.deadline_steps:
            raise ValueError("fault must occur after task start and before deadline")


class SustainedSupportTopologyUAVEnv(RedundantTopologyUAVEnv):
    """Same reset/step interface with legal, capacity-limited relay decisions.

    All agents retain the common discrete action alphabet ``0, 1, 2``:
    scouts sense an objective, relays forward an objective, and terminals
    attempt their assigned objective.  Failure masks remain hidden from actor
    feature values; agents see only their legal graph/action availability.
    """

    runtime_format = "sustained_support_topology_uav_runtime_v3"

    def __init__(self, config: SustainedSupportTopologyConfig):
        self.semantic_config = config
        super().__init__(config.base)

    def _role_lanes(self, count: int, x: float) -> np.ndarray:
        return self._spaced(count, x)

    def reset(self, seed_env: int | None = None):
        super().reset(seed_env=seed_env)
        cfg = self.semantic_config
        self.positions = np.concatenate(
            (
                self._role_lanes(self.config.scouts, cfg.scout_x),
                self._role_lanes(self.config.relays, cfg.relay_x),
                self._role_lanes(self.config.terminals, cfg.terminal_x),
            ),
            axis=0,
        )
        self.objective_positions = self._spaced(self.k, cfg.objective_x)
        terminal_order = self.terminal_ids[np.argsort(self.positions[self.terminal_ids, 1])]
        scout_order = self.scout_ids[np.argsort(self.positions[self.scout_ids, 1])]
        objective_order = np.argsort(self.objective_positions[:, 1])
        self.terminal_assignment = {int(t): int(o) for t, o in zip(terminal_order, objective_order)}
        self.scout_assignment = {int(s): int(o) for s, o in zip(scout_order, objective_order)}
        self.event_log.append({"event": "v3_reset", "relay_packet_capacity": cfg.relay_packet_capacity, "support_max_age": cfg.support_max_age})
        return self.actor_observation(), self.critic_observation(), self.graph_observation()

    def _fresh_token(self, terminal: int, objective: int) -> dict[str, Any] | None:
        token = self.caches[terminal].get(objective)
        if token is None:
            return None
        token["age"] = self.step_count - token["t_sense"]
        return token if token["valid"] and token["age"] <= self.semantic_config.support_max_age else None

    def support_action_mask(self, agent: int) -> np.ndarray:
        mask = np.zeros(self.action_dim, dtype=np.int8)
        mask[0] = 1
        role = int(self.roles[agent])
        if role == ROLE_SCOUT:
            objective = self.scout_assignment[int(agent)]
            if not self.completed[objective]:
                mask[objective + 1] = 1
            return mask
        if role == ROLE_RELAY:
            task = self.task_adjacency(True)
            for objective in range(self.k):
                terminal = next(t for t, assigned in self.terminal_assignment.items() if assigned == objective)
                upstream = any(task[int(agent), int(s)] for s, assigned in self.scout_assignment.items() if assigned == objective)
                downstream = bool(task[int(terminal), int(agent)])
                mask[objective + 1] = int(not self.completed[objective] and upstream and downstream)
            return mask
        if role == ROLE_TERMINAL and agent not in self.failed_nodes:
            objective = self.terminal_assignment[int(agent)]
            mask[objective + 1] = int(not self.completed[objective] and self._fresh_token(int(agent), objective) is not None)
        return mask

    def _sense_and_route(self, actions: np.ndarray, active: np.ndarray) -> list[dict[str, Any]]:
        """Forward at most one selected objective per relay on a legal route."""
        packets: list[dict[str, Any]] = []
        for scout in self.scout_ids:
            objective = int(actions[scout]) - 1
            if scout in self.failed_nodes or objective < 0 or objective >= self.k:
                continue
            if objective != self.scout_assignment[int(scout)]:
                continue
            if np.linalg.norm(self.positions[scout] - self.objective_positions[objective]) > self.config.scout_sense_range:
                continue
            packets.append({"objective_id": objective, "estimated_target_state": self.objective_positions[objective].copy(), "source_scout": int(scout), "t_sense": self.step_count, "valid": True})

        delivered: list[dict[str, Any]] = []
        for relay in self.relay_ids:
            objective = int(actions[relay]) - 1
            if relay in self.failed_nodes or objective < 0 or objective >= self.k:
                continue
            terminal = next(t for t, assigned in self.terminal_assignment.items() if assigned == objective)
            candidates = [packet for packet in packets if packet["objective_id"] == objective and active[int(relay), packet["source_scout"]] and active[int(terminal), int(relay)]]
            if not candidates:
                continue
            packet = min(candidates, key=lambda value: value["source_scout"])
            msg = {**packet, "relay_id": int(relay), "route": (packet["source_scout"], int(relay), int(terminal)), "t_receive": self.step_count, "age": 0}
            self.caches[int(terminal)][objective] = msg
            delivered.append(msg)
            self.event_log.append({"event": "v3_forward", "step": self.step_count, "relay": int(relay), "objective": objective, "route": msg["route"]})

        if delivered and self.recovery_times["message"] is None and self.recovery_times["failure"] is not None:
            self.recovery_times["message"] = self.step_count
        return delivered

    def graph_observation(self) -> dict[str, np.ndarray]:
        graph = super().graph_observation()
        graph["action_masks"] = np.stack([self.support_action_mask(agent) for agent in range(self.n)])
        return graph

    def telemetry_records(self) -> dict[str, Any]:
        records = super().telemetry_records()
        records["v3_semantics"] = {
            "relay_packet_capacity": self.semantic_config.relay_packet_capacity,
            "support_max_age": self.semantic_config.support_max_age,
            "fault_transition": self.semantic_config.fault_transition,
        }
        return records
