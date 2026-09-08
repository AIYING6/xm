"""V3.1 sustained-support task: V3 semantics with legal dense motion progress.

V3.1 is a learnability qualification task.  It preserves V3's agents,
topology groups, information boundary, action alphabet, fault timing and relay
capacity.  Its sole task-level change is that a terminal receives progress for
legal distance reduction under fresh support, rather than only when an entire
objective is completed.
"""
from __future__ import annotations

import numpy as np

from envs.redundant_topology_uav_env import ROLE_TERMINAL
from envs.sustained_support_topology_uav_env import SustainedSupportTopologyConfig, SustainedSupportTopologyUAVEnv


class SustainedSupportTopologyV31UAVEnv(SustainedSupportTopologyUAVEnv):
    """V3 task semantics with an observable, legal terminal-progress signal."""

    runtime_format = "sustained_support_topology_uav_runtime_v31"

    def reset(self, seed_env: int | None = None):
        output = super().reset(seed_env=seed_env)
        self.initial_objective_distance = np.zeros(self.k, dtype=np.float32)
        for terminal, objective in self.terminal_assignment.items():
            self.initial_objective_distance[objective] = max(
                float(np.linalg.norm(self.objective_positions[objective] - self.positions[terminal])), 1e-6
            )
        return output

    def _move_terminals(self, actions: np.ndarray) -> None:
        """Advance only on a fresh legal token and expose normalized progress."""
        for terminal in self.terminal_ids:
            action = int(actions[terminal])
            if self.roles[terminal] != ROLE_TERMINAL or terminal in self.failed_nodes or action == 0 or action > self.k:
                continue
            objective = action - 1
            if objective != self.terminal_assignment[int(terminal)] or self.completed[objective]:
                continue
            token = self._fresh_token(int(terminal), objective)
            if token is None:
                continue
            delta = self.objective_positions[objective] - self.positions[terminal]
            distance = float(np.linalg.norm(delta))
            if distance > 0:
                self.positions[terminal] += delta * min(1.0, self.config.terminal_speed * self.config.dt / distance)
            remaining = float(np.linalg.norm(self.objective_positions[objective] - self.positions[terminal]))
            self.objective_progress[objective] = max(
                float(self.objective_progress[objective]),
                float(np.clip(1.0 - remaining / self.initial_objective_distance[objective], 0.0, 1.0)),
            )
            if remaining <= 1.0:
                self.completed[objective] = True
                self.objective_progress[objective] = 1.0
                self.event_log.append({"event": "objective_complete", "step": self.step_count, "objective": objective, "terminal": int(terminal), "route": token["route"]})
                if self.recovery_times["failure"] is not None and self.recovery_times["task"] is None:
                    self.recovery_times["task"] = self.step_count


def v31_semantic_spec(config: SustainedSupportTopologyConfig) -> dict[str, object]:
    return {
        "base_semantics": "V3 sustained support",
        "only_task_change_from_v3": "normalized legal terminal distance progress",
        "fault_transition": config.fault_transition,
        "relay_packet_capacity": config.relay_packet_capacity,
        "support_max_age": config.support_max_age,
        "completion_bonus_preserved": True,
    }
