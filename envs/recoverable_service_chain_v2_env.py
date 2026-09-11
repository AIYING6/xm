"""P41 v2: a non-learning audit environment for recoverable service chains.

This benign emergency-service task deliberately separates an observable forecast
from the hidden realization of a future request.  One service payload can be
committed per episode.  A commitment also needs continuing confirmation support,
so a relay reconfiguration is a consequential but recoverable action.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class KnownRequest:
    site: int
    value: float
    deadline: int


@dataclass(frozen=True)
class FutureForecast:
    site: int
    probability: float
    value: float
    release: int
    deadline: int
    realized: bool  # trainer/tape-only; never emitted in actor observations


@dataclass(frozen=True)
class P41V2Scenario:
    name: str
    known: KnownRequest
    forecast: FutureForecast
    outage_site: int
    outage_start: int
    outage_duration: int


P41_V2_SCENARIOS: tuple[P41V2Scenario, ...] = (
    # The forecast looks attractive but does not materialize: early commitment
    # is correct without giving the actor future truth.
    P41V2Scenario(
        "commit_now",
        KnownRequest(site=0, value=7.0, deadline=5),
        FutureForecast(site=1, probability=0.90, value=10.0, release=2, deadline=8, realized=False),
        outage_site=1, outage_start=7, outage_duration=1,
    ),
    # Waiting for a high-probability, high-value request is correct.
    P41V2Scenario(
        "defer_for_value",
        KnownRequest(site=0, value=4.0, deadline=5),
        FutureForecast(site=1, probability=0.90, value=12.0, release=2, deadline=8, realized=True),
        outage_site=0, outage_start=7, outage_duration=1,
    ),
    # Expected future value is lower than the known request, but public outage
    # timing makes the known service chain nonviable without a proactive reroute.
    P41V2Scenario(
        "reroute_before_outage",
        KnownRequest(site=0, value=8.0, deadline=6),
        FutureForecast(site=1, probability=0.60, value=12.0, release=2, deadline=8, realized=True),
        outage_site=0, outage_start=1, outage_duration=4,
    ),
)


class RecoverableServiceChainV2Env:
    """Three-role P41 v2 environment with the standard project interface."""

    num_agents = 3  # scout, relay, service
    action_dim = 3  # idle/hold, site 0, site 1
    service_duration = 3
    horizon = 9
    message_ttl = 1

    def __init__(self, scenario: P41V2Scenario):
        self.scenario = scenario
        self.reset()

    def reset(self) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray]]:
        self.step_count = 0
        self.done = False
        self.relay_site = 0
        self.relay_moving = False
        self.cache: dict[int, int] = {}
        self.committed_site: int | None = None
        self.commit_finish: int | None = None
        self.completed_value = 0.0
        self.commit_used = False
        self.aborted = False
        self.events: list[dict[str, Any]] = []
        return self.actor_observation(), self.critic_observation(), self.graph_observation()

    def _future_released(self) -> bool:
        return self.scenario.forecast.realized and self.step_count >= self.scenario.forecast.release

    def _request_at(self, site: int) -> KnownRequest | None:
        if site == self.scenario.known.site and self.completed_value == 0.0:
            return self.scenario.known
        forecast = self.scenario.forecast
        if site == forecast.site and self._future_released() and self.completed_value == 0.0:
            return KnownRequest(site=forecast.site, value=forecast.value, deadline=forecast.deadline)
        return None

    def _outage(self, site: int) -> bool:
        return site == self.scenario.outage_site and self.scenario.outage_start <= self.step_count < self.scenario.outage_start + self.scenario.outage_duration

    def _chain_active(self, site: int) -> bool:
        return not self.relay_moving and self.relay_site == site and not self._outage(site)

    def actor_observation(self) -> np.ndarray:
        # All forecast fields are legal public advisory data.  The realization
        # flag is deliberately excluded; only a released request becomes visible.
        rows = np.zeros((3, 12), dtype=np.float32)
        known = self._request_at(self.scenario.known.site)
        if known is not None:
            rows[0, 0:3] = (1.0, known.value / 12.0, (known.deadline - self.step_count) / self.horizon)
        future = self._request_at(self.scenario.forecast.site)
        if future is not None:
            rows[0, 3:6] = (1.0, future.value / 12.0, (future.deadline - self.step_count) / self.horizon)
        forecast = self.scenario.forecast
        rows[:, 6:10] = (forecast.probability, forecast.value / 12.0, forecast.release / self.horizon, forecast.deadline / self.horizon)
        rows[1, 10] = float(self.relay_site)
        rows[1, 11] = float(self._outage(self.relay_site))
        # Service only receives validated messages; it does not see raw scout requests.
        rows[2, 0] = float(0 in self.cache and self.step_count - self.cache[0] <= self.message_ttl)
        rows[2, 1] = float(1 in self.cache and self.step_count - self.cache[1] <= self.message_ttl)
        return rows

    def critic_observation(self) -> np.ndarray:
        # Centralized-training-only state includes tape realization for audit.
        return np.asarray((
            float(self.step_count) / self.horizon,
            float(self.relay_site),
            float(self._future_released()),
            float(self.scenario.forecast.realized),
            float(self.committed_site is not None),
            float(self.commit_used),
        ), dtype=np.float32)

    def graph_observation(self) -> dict[str, np.ndarray]:
        active = np.zeros((3, 3), dtype=np.int8)
        if self._chain_active(self.relay_site):
            active[1, 0] = 1
            active[2, 1] = 1
        return {
            "node_features": self.actor_observation(),
            "active_adj": active,
            "roles": np.asarray((0, 1, 2), dtype=np.int64),
            "action_masks": np.ones((3, self.action_dim), dtype=np.int8),
        }

    def step(self, actions: np.ndarray | list[int]) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray], np.ndarray, np.ndarray, dict[str, Any]]:
        if self.done:
            raise RuntimeError("reset required after terminal episode")
        scout, relay, service = np.clip(np.asarray(actions, dtype=np.int64).reshape(3), 0, 2)
        gained = 0.0
        desired_site = self.relay_site if relay == 0 else int(relay - 1)
        self.relay_moving = desired_site != self.relay_site
        if self.relay_moving:
            self.relay_site = desired_site
            self.events.append({"event": "relay_reconfigure", "step": self.step_count, "site": desired_site})

        sensed_site = None if scout == 0 else int(scout - 1)
        request = self._request_at(sensed_site) if sensed_site is not None else None
        if request is not None and self._chain_active(sensed_site):
            self.cache[sensed_site] = self.step_count
            self.events.append({"event": "confirmation_delivered", "step": self.step_count, "site": sensed_site})

        if self.committed_site is None and not self.commit_used and service != 0:
            site = int(service - 1)
            request = self._request_at(site)
            if request is not None and site in self.cache and self.step_count - self.cache[site] <= self.message_ttl:
                self.committed_site = site
                self.commit_finish = self.step_count + self.service_duration
                self.commit_used = True
                self.events.append({"event": "service_committed", "step": self.step_count, "site": site})

        # A service chain must stay live after commitment.  This makes relay
        # movement a recoverable but consequential coordination decision.
        if self.committed_site is not None and not self._chain_active(self.committed_site):
            self.events.append({"event": "service_aborted", "step": self.step_count, "site": self.committed_site})
            self.committed_site = None
            self.commit_finish = None
            self.aborted = True

        self.step_count += 1
        if self.committed_site is not None and self.commit_finish is not None and self.step_count >= self.commit_finish:
            request = self._request_at(self.committed_site)
            if request is not None and self.step_count <= request.deadline + 1:
                gained = request.value
                self.completed_value += request.value
                self.events.append({"event": "service_completed", "step": self.step_count, "site": self.committed_site})
            self.committed_site = None
            self.commit_finish = None

        self.done = self.step_count >= self.horizon or self.completed_value > 0.0 or (self.commit_used and self.committed_site is None)
        reward = gained - 0.1 * float(self.relay_moving)
        info = {
            "completed_value": self.completed_value,
            "aborted": self.aborted,
            "outage_active": self._outage(self.relay_site),
            "events": list(self.events),
        }
        rewards = np.full((3, 1), reward, dtype=np.float32)
        dones = np.full((3, 1), self.done, dtype=np.float32)
        return self.actor_observation(), self.critic_observation(), self.graph_observation(), rewards, dones, info

    def terminal_summary(self) -> dict[str, Any]:
        return {
            "scenario": self.scenario.name,
            "completed_value": self.completed_value,
            "commit_used": self.commit_used,
            "aborted": self.aborted,
            "reconfigurations": sum(event["event"] == "relay_reconfigure" for event in self.events),
            "events": list(self.events),
        }
