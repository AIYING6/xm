"""Belief, gate, and PPO-control attribution for the P3B pilot.

The adapter is deliberately independent of the trainable task-value estimator.
Callers must supply task values computed from deployment-legal state.  A forced
macro action is marked outside actor control, so PPO cannot treat it as a
sample from the low-level actor distribution.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from algorithms.active_diagnosis.decision_relevant_probe import decision_relevant_probe_value


RECOVERABLE_INDEX = 0
HARD_FAILURE_INDEX = 1


def _entropy(probabilities: np.ndarray) -> float:
    values = np.asarray(probabilities, dtype=np.float64)
    positive = values[values > 0.0]
    return float(-np.sum(positive * np.log(positive)))


@dataclass(frozen=True)
class GateDecision:
    force_probe: bool
    force_fallback: bool
    score: float
    reason: str


class FailureBelief:
    runtime_format = "active_diagnosis_failure_belief_v1"

    def __init__(self, recoverable_prior: float, observation_kernel: np.ndarray) -> None:
        if not 0.0 < recoverable_prior < 1.0:
            raise ValueError("recoverable prior must be strictly between zero and one")
        kernel = np.asarray(observation_kernel, dtype=np.float64)
        if kernel.shape != (2, 2) or np.any(kernel < 0.0) or not np.allclose(kernel.sum(1), 1.0):
            raise ValueError("observation kernel must be a 2x2 row-stochastic matrix")
        self.initial = np.asarray([recoverable_prior, 1.0 - recoverable_prior], dtype=np.float64)
        self.kernel = kernel.copy()
        self.reset()

    def reset(self) -> None:
        self.probabilities = self.initial.copy()
        self.observation_count = 0

    def observe_ack_state(self, ack_state: float) -> np.ndarray:
        if ack_state not in (-1.0, 1.0):
            raise ValueError("belief updates require a completed ACK outcome")
        observation = 0 if ack_state > 0.0 else 1
        likelihood = self.kernel[:, observation]
        normalizer = float(np.dot(self.probabilities, likelihood))
        if normalizer <= 0.0:
            raise RuntimeError("observation has zero probability under the frozen model")
        self.probabilities = self.probabilities * likelihood / normalizer
        self.observation_count += 1
        return self.probabilities.copy()

    def state_dict(self) -> dict:
        return {
            "format": self.runtime_format,
            "initial": self.initial.copy(),
            "kernel": self.kernel.copy(),
            "probabilities": self.probabilities.copy(),
            "observation_count": self.observation_count,
        }

    def load_state_dict(self, state: dict) -> None:
        if state.get("format") != self.runtime_format:
            raise ValueError("incompatible belief state")
        if not np.array_equal(state["initial"], self.initial) or not np.array_equal(state["kernel"], self.kernel):
            raise ValueError("belief state uses another frozen prior or observation model")
        self.probabilities = np.asarray(state["probabilities"], dtype=np.float64).copy()
        self.observation_count = int(state["observation_count"])


def expected_entropy_reduction(belief: np.ndarray, kernel: np.ndarray) -> float:
    belief = np.asarray(belief, dtype=np.float64)
    kernel = np.asarray(kernel, dtype=np.float64)
    observation_probabilities = belief @ kernel
    posterior_entropy = 0.0
    for observation, probability in enumerate(observation_probabilities):
        if probability <= 0.0:
            continue
        posterior = belief * kernel[:, observation] / probability
        posterior_entropy += float(probability) * _entropy(posterior)
    return _entropy(belief) - posterior_entropy


class ProbeGate:
    """Episode-local gate sharing one belief model across objective variants."""

    def __init__(self, mode: str, belief: FailureBelief, probe_cost: float) -> None:
        if mode not in {"entropy", "decision_relevant"}:
            raise ValueError(mode)
        self.mode = mode
        self.belief = belief
        self.probe_cost = float(probe_cost)
        self.reset()

    def reset(self) -> None:
        self.belief.reset()
        self.decided = False
        self.last_ack_state = 0.0

    def initial_decision(self, task_values: np.ndarray | None = None) -> GateDecision:
        if self.decided:
            raise RuntimeError("initial gate decision is one-shot")
        self.decided = True
        if self.mode == "entropy":
            score = expected_entropy_reduction(self.belief.probabilities, self.belief.kernel) - self.probe_cost
        else:
            if task_values is None:
                raise ValueError("decision-relevant gate requires deployment-legal task values")
            score = decision_relevant_probe_value(
                self.belief.probabilities,
                task_values,
                self.belief.kernel,
                self.probe_cost,
            ).net_value
        return GateDecision(
            force_probe=score > 0.0,
            force_fallback=score <= 0.0,
            score=float(score),
            reason=f"{self.mode}_positive" if score > 0.0 else f"{self.mode}_nonpositive",
        )

    def completed_probe_decision(self, ack_state: float) -> GateDecision:
        if ack_state == self.last_ack_state:
            return GateDecision(False, False, 0.0, "no_new_probe_outcome")
        self.last_ack_state = float(ack_state)
        self.belief.observe_ack_state(ack_state)
        return GateDecision(False, ack_state < 0.0, 0.0, "ack_continue" if ack_state > 0.0 else "no_ack_fallback")

    def state_dict(self) -> dict:
        return {
            "mode": self.mode,
            "probe_cost": self.probe_cost,
            "decided": self.decided,
            "last_ack_state": self.last_ack_state,
            "belief": self.belief.state_dict(),
        }

    def load_state_dict(self, state: dict) -> None:
        if state.get("mode") != self.mode or float(state.get("probe_cost")) != self.probe_cost:
            raise ValueError("incompatible gate state")
        self.decided = bool(state["decided"])
        self.last_ack_state = float(state["last_ack_state"])
        self.belief.load_state_dict(state["belief"])


def policy_action_masks(
    environment_masks: np.ndarray,
    probe_action: int,
    fallback_action: int,
    neutral_action: int = 13,
) -> np.ndarray:
    """Remove gate options while keeping a finite shadow policy distribution.

    During a forced option the environment may expose only that option for one
    agent.  The low-level actor receives a neutral singleton mask for that
    agent, and its actor-control weight is zero.  This avoids undefined logits
    without attributing the forced action to PPO.
    """
    masks = np.asarray(environment_masks, dtype=np.float32).copy()
    masks[:, probe_action] = 0.0
    masks[:, fallback_action] = 0.0
    empty = np.flatnonzero(masks.sum(axis=1) <= 0.0)
    if not 0 <= neutral_action < probe_action:
        raise ValueError("neutral action must belong to the low-level flight alphabet")
    masks[empty, neutral_action] = 1.0
    return masks


def apply_forced_options(
    sampled_actions: np.ndarray,
    decision: GateDecision,
    relay_id: int,
    attacker_id: int,
    probe_action: int,
    fallback_action: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Return executed actions and per-agent PPO actor-control indicators."""
    actions = np.asarray(sampled_actions, dtype=np.int64).copy()
    control = np.ones(actions.shape, dtype=np.float32)
    if decision.force_probe and decision.force_fallback:
        raise ValueError("one gate decision cannot force both options")
    if decision.force_probe:
        actions[relay_id] = probe_action
        control[relay_id] = 0.0
    if decision.force_fallback:
        actions[attacker_id] = fallback_action
        control[attacker_id] = 0.0
    return actions, control
