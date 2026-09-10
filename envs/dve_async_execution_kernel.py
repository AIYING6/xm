"""Two-phase execution kernel for latency-aware policy/admission separation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SnapshotState:
    own_x: float
    own_v: float
    target_x: float
    corridor_open: bool


@dataclass(frozen=True)
class CompletionState:
    elapsed_ms: float
    own_x: float
    target_x: float
    corridor_reserved: bool


class DVEAsyncExecutionKernel:
    """Separates slow proposal inference from lightweight completion admission.

    The proposal observation is immutable after reset. Completion-time variables
    are exposed only through ``admission_observation`` after a proposal is frozen.
    """

    def __init__(self, snapshot: SnapshotState, completion: CompletionState) -> None:
        self.snapshot = snapshot
        self._completion = completion
        self._proposal: int | None = None
        self._phase = "snapshot"

    def reset(self):
        self._proposal = None
        self._phase = "snapshot"
        obs = self.proposal_observation()
        share_obs = obs.copy()
        graph_obs = {
            "node_features": obs.reshape(1, -1),
            "edge_index": np.empty((2, 0), dtype=np.int64),
        }
        return obs, share_obs, graph_obs

    def proposal_observation(self) -> np.ndarray:
        return np.asarray(
            [
                self.snapshot.own_x,
                self.snapshot.own_v,
                self.snapshot.target_x,
                float(self.snapshot.corridor_open),
            ],
            dtype=np.float32,
        )

    def begin_inference(self, proposal: int) -> None:
        if self._phase != "snapshot":
            raise RuntimeError("proposal can only be frozen once after reset")
        if proposal not in (0, 1):
            raise ValueError("proposal must be fallback(0) or corridor maneuver(1)")
        self._proposal = proposal
        self._phase = "completion"

    def admission_observation(self) -> np.ndarray:
        if self._phase != "completion" or self._proposal is None:
            raise RuntimeError("freeze a proposal before reading completion state")
        relative_error = abs(self._completion.target_x - self._completion.own_x)
        return np.asarray(
            [
                self._completion.elapsed_ms / 100.0,
                relative_error,
                float(self._completion.corridor_reserved),
                float(self._proposal),
            ],
            dtype=np.float32,
        )

    def step(self, admission_action: int):
        if self._phase != "completion" or self._proposal is None:
            raise RuntimeError("begin_inference must precede admission")
        if admission_action not in (0, 1):
            raise ValueError("admission action must reject(0) or accept(1)")
        executed = self._proposal if admission_action else 0
        relative_error = abs(self._completion.target_x - self._completion.own_x)
        task_valid = relative_error <= 2.0
        team_valid = not self._completion.corridor_reserved
        stale_accept = bool(executed == 1 and not (task_valid and team_valid))
        if stale_accept:
            value = -6.0 if team_valid else -10.0
        elif executed == 1:
            value = 8.0
        else:
            value = 3.0
        self._phase = "done"
        obs = self.proposal_observation()
        share_obs = obs.copy()
        graph_obs = {
            "node_features": obs.reshape(1, -1),
            "edge_index": np.empty((2, 0), dtype=np.int64),
        }
        rewards = np.asarray([value], dtype=np.float32)
        dones = np.asarray([True])
        infos = [{
            "proposal": self._proposal,
            "executed": executed,
            "task_valid": task_valid,
            "team_valid": team_valid,
            "stale_accept": stale_accept,
        }]
        return obs, share_obs, graph_obs, rewards, dones, infos

