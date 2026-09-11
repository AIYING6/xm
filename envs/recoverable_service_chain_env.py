"""Minimal non-learning environment for the P41 recoverable service-chain audit.

The environment models a benign emergency-service workflow: a scout confirms a
request, a relay forwards that confirmation, and a service UAV commits to a
time-limited response.  It exists only to test task decision structure before
any learning method is proposed.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class ServiceRequest:
    site: int
    release: int
    deadline: int
    value: float


@dataclass(frozen=True)
class P41Scenario:
    name: str
    requests: tuple[ServiceRequest, ...]
    outage_site: int
    outage_start: int
    outage_duration: int


P41_SCENARIOS: tuple[P41Scenario, ...] = (
    P41Scenario(
        "early_deadline",
        (ServiceRequest(0, 0, 5, 5.0), ServiceRequest(1, 2, 9, 9.0)),
        outage_site=1,
        outage_start=3,
        outage_duration=2,
    ),
    P41Scenario(
        "late_high_value",
        (ServiceRequest(0, 0, 9, 4.0), ServiceRequest(1, 2, 6, 10.0)),
        outage_site=0,
        outage_start=3,
        outage_duration=2,
    ),
    P41Scenario(
        "reroute_recovery",
        (ServiceRequest(0, 0, 7, 7.0), ServiceRequest(1, 1, 8, 8.0)),
        outage_site=0,
        outage_start=2,
        outage_duration=3,
    ),
)


class RecoverableServiceChainEnv:
    """Three-agent, two-site P41 task with legal local observations.

    Agent order is scout, relay, service.  Each agent chooses 0 (idle/hold),
    1 (site 0), or 2 (site 1).  A scout observation contains only currently
    released requests.  The service agent sees only messages that have been
    successfully routed.  The relay sees only its own location and current
    outage flag; neither it nor the scout sees future requests.
    """

    num_agents = 3
    num_sites = 2
    action_dim = 3
    deadline_steps = 10
    service_duration = 2
    message_ttl = 2

    def __init__(self, scenario: P41Scenario):
        self.scenario = scenario
        self.reset()

    def reset(self) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray]]:
        self.step_count = 0
        self.done = False
        self.relay_site = 0
        self.relay_moving = False
        self.service_site: int | None = None
        self.service_finish: int | None = None
        self.completed: set[int] = set()
        self.expired: set[int] = set()
        self.cache: dict[int, tuple[int, ServiceRequest]] = {}
        self.events: list[dict[str, Any]] = []
        return self.actor_observation(), self.critic_observation(), self.graph_observation()

    def _request(self, site: int) -> ServiceRequest:
        return next(request for request in self.scenario.requests if request.site == site)

    def _released(self, request: ServiceRequest) -> bool:
        return self.step_count >= request.release and request.site not in self.completed and request.site not in self.expired

    def _outage_active(self, site: int) -> bool:
        return site == self.scenario.outage_site and self.scenario.outage_start <= self.step_count < self.scenario.outage_start + self.scenario.outage_duration

    def _actor_rows(self) -> np.ndarray:
        rows = np.zeros((self.num_agents, 11), dtype=np.float32)
        # Scout: released local request descriptors.  No future request values.
        for request in self.scenario.requests:
            if self._released(request):
                base = request.site * 3
                rows[0, base:base + 3] = (1.0, request.value / 10.0, (request.deadline - self.step_count) / self.deadline_steps)
        # Relay: current site, movement flag, and current local outage condition.
        rows[1, 6 + self.relay_site] = 1.0
        rows[1, 8] = float(self.relay_moving)
        rows[1, 9] = float(self._outage_active(self.relay_site))
        # Service: only cached, unexpired confirmations.
        for site, (received_at, request) in self.cache.items():
            if self.step_count - received_at <= self.message_ttl and self._released(request):
                rows[2, site] = 1.0
                rows[2, 2 + site] = request.value / 10.0
                rows[2, 4 + site] = (request.deadline - self.step_count) / self.deadline_steps
        rows[2, 10] = float(self.service_site is not None)
        return rows

    def actor_observation(self) -> np.ndarray:
        return self._actor_rows()

    def critic_observation(self) -> np.ndarray:
        request_rows = []
        for request in self.scenario.requests:
            request_rows.extend((float(self._released(request)), request.value / 10.0, (request.deadline - self.step_count) / self.deadline_steps))
        return np.asarray(request_rows + [float(self.relay_site), float(self.service_site is not None), float(self.step_count) / self.deadline_steps], dtype=np.float32)

    def graph_observation(self) -> dict[str, np.ndarray]:
        active = np.zeros((self.num_agents, self.num_agents), dtype=np.int8)
        if not self.relay_moving and not self._outage_active(self.relay_site):
            active[1, 0] = 1
            active[2, 1] = 1
        return {
            "node_features": self.actor_observation(),
            "active_adj": active,
            "roles": np.asarray((0, 1, 2), dtype=np.int64),
            "action_masks": np.ones((self.num_agents, self.action_dim), dtype=np.int8),
        }

    def _expire_requests(self) -> None:
        for request in self.scenario.requests:
            if request.site not in self.completed and self.step_count > request.deadline:
                self.expired.add(request.site)

    def step(self, actions: np.ndarray | list[int]) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray], np.ndarray, np.ndarray, dict[str, Any]]:
        if self.done:
            raise RuntimeError("reset required after terminal episode")
        scout_action, relay_action, service_action = np.clip(np.asarray(actions, dtype=np.int64).reshape(self.num_agents), 0, self.action_dim - 1)
        prior_value = sum(self._request(site).value for site in self.completed)

        # Relay reconfiguration consumes this entire step; it intentionally
        # exposes an opportunity cost instead of granting instantaneous recovery.
        desired_site = self.relay_site if relay_action == 0 else int(relay_action - 1)
        self.relay_moving = desired_site != self.relay_site
        if self.relay_moving:
            self.relay_site = desired_site
            self.events.append({"event": "relay_reconfigure", "step": self.step_count, "site": desired_site})

        sensed_site = None if scout_action == 0 else int(scout_action - 1)
        if sensed_site is not None:
            request = self._request(sensed_site)
            if self._released(request) and not self.relay_moving and self.relay_site == sensed_site and not self._outage_active(sensed_site):
                self.cache[sensed_site] = (self.step_count, request)
                self.events.append({"event": "confirmation_delivered", "step": self.step_count, "site": sensed_site})

        if self.service_site is None and service_action != 0:
            site = int(service_action - 1)
            message = self.cache.get(site)
            if message is not None and self.step_count - message[0] <= self.message_ttl and self._released(message[1]):
                self.service_site = site
                self.service_finish = self.step_count + self.service_duration
                self.events.append({"event": "service_committed", "step": self.step_count, "site": site})

        self.step_count += 1
        if self.service_site is not None and self.service_finish is not None and self.step_count >= self.service_finish:
            request = self._request(self.service_site)
            if self.step_count <= request.deadline + 1 and self.service_site not in self.expired:
                self.completed.add(self.service_site)
                self.events.append({"event": "service_completed", "step": self.step_count, "site": self.service_site})
            self.service_site = None
            self.service_finish = None

        self._expire_requests()
        self.done = self.step_count >= self.deadline_steps or len(self.completed | self.expired) == self.num_sites
        current_value = sum(self._request(site).value for site in self.completed)
        reward = float(current_value - prior_value) - 0.05 * float(self.relay_moving)
        info = {
            "completed_value": current_value,
            "completed": sorted(self.completed),
            "expired": sorted(self.expired),
            "outage_active": self._outage_active(self.relay_site),
            "events": list(self.events),
            "service_busy": self.service_site is not None,
        }
        rewards = np.full((self.num_agents, 1), reward, dtype=np.float32)
        dones = np.full((self.num_agents, 1), self.done, dtype=np.float32)
        return self.actor_observation(), self.critic_observation(), self.graph_observation(), rewards, dones, info

    def terminal_summary(self) -> dict[str, Any]:
        completed_value = sum(self._request(site).value for site in self.completed)
        return {
            "scenario": self.scenario.name,
            "completed_value": completed_value,
            "completed_count": len(self.completed),
            "expired_count": len(self.expired),
            "reconfigurations": sum(event["event"] == "relay_reconfigure" for event in self.events),
            "events": list(self.events),
        }
