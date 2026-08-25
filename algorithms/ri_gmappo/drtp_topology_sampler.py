"""Frozen DRTP/UTR topology-perturbation samplers.

The sampler is deliberately outside the policy.  It selects only an already
frozen environment condition at reset time and logs training-only summaries;
it never adds an observation feature, reward term, or PPO loss.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import random
from typing import Iterable


NOMINAL_GROUP = "N"
FAILURE_GROUPS = ("F0", "TE", "TL", "DS", "DL", "CP")
ALL_GROUPS = (NOMINAL_GROUP, *FAILURE_GROUPS)
GROUP_MEMBERS: dict[str, tuple[tuple[str, int, int], ...]] = {
    NOMINAL_GROUP: (("nominal", -1, 0),),
    "F0": (("f0", 44, 80),),
    "TE": (("te_28_80", 28, 80), ("te_36_80", 36, 80)),
    "TL": (("tl_52_80", 52, 80), ("tl_60_80", 60, 80)),
    "DS": (("ds_44_40", 44, 40), ("ds_44_60", 44, 60)),
    "DL": (("dl_44_100", 44, 100), ("dl_44_120", 44, 120)),
    "CP": (("cp_28_120", 28, 120), ("cp_60_120", 60, 120)),
}

NOMINAL_MASS = 0.50
WARMUP_UPDATES = 128
ADAPT_INTERVAL = 32
EMA_KAPPA = 0.20
TEMPERATURE_ETA = 1.00
SMOOTHING_BETA = 0.50
DIFFICULTY_MAX = 2.00
EPSILON = 1e-8
Q_MIN = 0.05
Q_MAX = 0.35
UNIFORM_Q = 1.0 / len(FAILURE_GROUPS)

# Frozen R-DRTP constants; these are selected before any R-DRTP performance.
RDRTP_N0 = 8.0
RDRTP_LAMBDA_V = 1.0
RDRTP_V_MAX = 1.0
RDRTP_ALPHA_MAX = 1.0


@dataclass(frozen=True)
class DRTPSelection:
    """Reset-time selection; all fields remain outside policy tensors."""

    group: str
    condition: str
    failure_start_step: int
    failure_duration_steps: int
    failed_blue_agent: int


def _bounded_simplex_projection(values: Iterable[float]) -> list[float]:
    """Project onto sum(q)=1 with the frozen lower/upper group bounds."""
    vector = [float(value) for value in values]
    count = len(vector)
    if count != len(FAILURE_GROUPS):
        raise ValueError("DRTP projection expects one value per failure group")
    if count * Q_MIN > 1.0 or count * Q_MAX < 1.0:
        raise ValueError("invalid frozen DRTP simplex bounds")
    low = min(value - Q_MAX for value in vector)
    high = max(value - Q_MIN for value in vector)
    for _ in range(100):
        midpoint = (low + high) / 2.0
        total = sum(min(Q_MAX, max(Q_MIN, value - midpoint)) for value in vector)
        if total > 1.0:
            low = midpoint
        else:
            high = midpoint
    projected = [min(Q_MAX, max(Q_MIN, value - high)) for value in vector]
    residual = 1.0 - sum(projected)
    if abs(residual) > 1e-12:
        for index, value in enumerate(projected):
            room = (Q_MAX - value) if residual > 0.0 else (value - Q_MIN)
            delta = math.copysign(min(abs(residual), max(0.0, room)), residual)
            projected[index] += delta
            residual -= delta
            if abs(residual) <= 1e-12:
                break
    if not math.isclose(sum(projected), 1.0, rel_tol=0.0, abs_tol=1e-10):
        raise AssertionError("bounded-simplex projection did not preserve mass")
    if any(value < Q_MIN - 1e-12 or value > Q_MAX + 1e-12 for value in projected):
        raise AssertionError("bounded-simplex projection violated frozen bounds")
    return projected


class DRTPTopologySampler:
    """Deterministic UTR or DRTP reset-time condition sampler.

    ``utr`` keeps the conditional failure distribution uniform.  ``drtp``
    starts from the same distribution and performs the contract's bounded
    exponential update using completed-episode return summaries only.
    """

    uses_completed_return_feedback = True

    def __init__(self, mode: str, seed: int, total_updates: int):
        self.mode = str(mode).lower()
        if self.mode not in {"utr", "drtp", "r_drtp"}:
            raise ValueError("DRTP sampler mode must be 'utr', 'drtp', or 'r_drtp'")
        self.seed = int(seed)
        self.total_updates = int(total_updates)
        if self.total_updates <= 0:
            raise ValueError("total_updates must be positive")
        self.q = {group: UNIFORM_Q for group in FAILURE_GROUPS}
        self.ema: dict[str, float | None] = {group: None for group in ALL_GROUPS}
        self.window_returns: dict[str, list[float]] = {group: [] for group in ALL_GROUPS}
        self.last_difficulty = {group: 0.0 for group in FAILURE_GROUPS}
        self.last_confidence = 0.0
        self.last_alpha = 0.0
        self.last_dispersion = {group: 0.0 for group in FAILURE_GROUPS}
        self.adaptation_count = 0

    def state_dict(self) -> dict:
        """Return every mutable sampler field needed for an exact continuation.

        The training-side sampler is deliberately outside the actor/critic.  It
        nevertheless has state (especially the active adaptation window) that
        affects later reset selections.  Persisting it is therefore required
        for a strict post-warm-restart continuation.
        """
        return {
            "format": "drtp_topology_sampler_runtime_state_v1",
            "mode": self.mode,
            "seed": self.seed,
            "total_updates": self.total_updates,
            "q": {group: float(self.q[group]) for group in FAILURE_GROUPS},
            "ema": {
                group: None if self.ema[group] is None else float(self.ema[group])
                for group in ALL_GROUPS
            },
            "window_returns": {
                group: [float(value) for value in self.window_returns[group]]
                for group in ALL_GROUPS
            },
            "last_difficulty": {
                group: float(self.last_difficulty[group]) for group in FAILURE_GROUPS
            },
            "last_confidence": float(self.last_confidence),
            "last_alpha": float(self.last_alpha),
            "last_dispersion": {
                group: float(self.last_dispersion[group]) for group in FAILURE_GROUPS
            },
            "adaptation_count": int(self.adaptation_count),
        }

    def load_state_dict(self, state: dict) -> None:
        """Restore a state emitted by :meth:`state_dict` with strict checks."""
        if state.get("format") != "drtp_topology_sampler_runtime_state_v1":
            raise ValueError("unsupported DRTP sampler runtime-state format")
        if str(state.get("mode")) != self.mode or int(state.get("seed")) != self.seed:
            raise ValueError("DRTP sampler runtime state is bound to a different mode or seed")
        required = {"q", "ema", "window_returns", "last_difficulty", "adaptation_count"}
        if not required.issubset(state):
            raise ValueError("incomplete DRTP sampler runtime state")
        q = {group: float(state["q"][group]) for group in FAILURE_GROUPS}
        if not math.isclose(sum(q.values()), 1.0, rel_tol=0.0, abs_tol=1e-10):
            raise ValueError("DRTP sampler runtime state has invalid q mass")
        if any(value < Q_MIN - 1e-12 or value > Q_MAX + 1e-12 for value in q.values()):
            raise ValueError("DRTP sampler runtime state violates q bounds")
        ema = {
            group: None if state["ema"][group] is None else float(state["ema"][group])
            for group in ALL_GROUPS
        }
        window_returns = {
            group: [float(value) for value in state["window_returns"][group]]
            for group in ALL_GROUPS
        }
        if any(not math.isfinite(value) for values in window_returns.values() for value in values):
            raise ValueError("DRTP sampler runtime state has non-finite window return")
        self.q = q
        self.ema = ema
        self.window_returns = window_returns
        self.last_difficulty = {
            group: float(state["last_difficulty"][group]) for group in FAILURE_GROUPS
        }
        self.last_confidence = float(state.get("last_confidence", 0.0))
        self.last_alpha = float(state.get("last_alpha", 0.0))
        self.last_dispersion = {
            group: float(state.get("last_dispersion", {}).get(group, 0.0))
            for group in FAILURE_GROUPS
        }
        self.adaptation_count = int(state["adaptation_count"])

    def _rng(self, update: int, env_index: int, episode_index: int) -> random.Random:
        key = (self.seed * 1_000_003 + int(update) * 97_003
               + int(env_index) * 10_007 + int(episode_index) * 101)
        return random.Random(key)

    @staticmethod
    def apply(env, selection: DRTPSelection) -> None:
        env.config.failed_blue_agent = selection.failed_blue_agent
        env.config.node_failure_start_step = selection.failure_start_step
        env.config.node_failure_duration_steps = selection.failure_duration_steps

    def _select_failure_group(self, rng: random.Random) -> str:
        cursor = 0.0
        draw = rng.random()
        for group in FAILURE_GROUPS:
            cursor += self.q[group]
            if draw < cursor:
                return group
        return FAILURE_GROUPS[-1]  # floating-point closure at one

    def select(self, update: int, env_index: int, episode_index: int) -> DRTPSelection:
        rng = self._rng(update, env_index, episode_index)
        group = NOMINAL_GROUP if rng.random() < NOMINAL_MASS else self._select_failure_group(rng)
        condition, onset, duration = GROUP_MEMBERS[group][rng.randrange(len(GROUP_MEMBERS[group]))]
        return DRTPSelection(
            group=group,
            condition=condition,
            failure_start_step=onset,
            failure_duration_steps=duration,
            failed_blue_agent=-1 if group == NOMINAL_GROUP else 1,
        )

    def record_completed_return(self, selection: DRTPSelection, episode_return: float) -> None:
        if selection.group not in ALL_GROUPS:
            raise ValueError(f"unknown DRTP group: {selection.group}")
        if not math.isfinite(float(episode_return)):
            raise ValueError("completed episode return must be finite")
        self.window_returns[selection.group].append(float(episode_return))

    def _refresh_ema(self) -> None:
        for group, values in self.window_returns.items():
            if not values:
                continue
            observed = sum(values) / len(values)
            old = self.ema[group]
            self.ema[group] = observed if old is None else (1.0 - EMA_KAPPA) * old + EMA_KAPPA * observed

    def _ema_ready(self) -> bool:
        return all(self.ema[group] is not None for group in ALL_GROUPS)

    def maybe_update(self, update: int) -> dict | None:
        """Apply an update only at frozen boundaries and return a log row."""
        update = int(update)
        if update % ADAPT_INTERVAL != 0:
            return None
        counts = {group: len(values) for group, values in self.window_returns.items()}
        self._refresh_ema()
        adapted = False
        reason = "utr_fixed_uniform" if self.mode == "utr" else "warmup"
        if self.mode in {"drtp", "r_drtp"} and update > WARMUP_UPDATES:
            if self._ema_ready():
                nominal = float(self.ema[NOMINAL_GROUP])
                raw_difficulty = {
                    group: min(DIFFICULTY_MAX, max(0.0, (nominal - float(self.ema[group])) / max(abs(nominal), EPSILON)))
                    for group in FAILURE_GROUPS
                }
                mean_difficulty = sum(raw_difficulty.values()) / len(FAILURE_GROUPS)
                logits = {
                    group: self.q[group] * math.exp(TEMPERATURE_ETA * (raw_difficulty[group] - mean_difficulty))
                    for group in FAILURE_GROUPS
                }
                normalizer = sum(logits.values())
                candidate = [logits[group] / normalizer for group in FAILURE_GROUPS]
                if self.mode == "r_drtp":
                    drtp_smoothed = [
                        (1.0 - SMOOTHING_BETA) * self.q[group] + SMOOTHING_BETA * candidate[index]
                        for index, group in enumerate(FAILURE_GROUPS)
                    ]
                    drtp_candidate = _bounded_simplex_projection(drtp_smoothed)
                    confidence = {}
                    dispersion = {}
                    for group in FAILURE_GROUPS:
                        values = self.window_returns[group]
                        if not values:
                            confidence[group] = 0.0
                            dispersion[group] = RDRTP_V_MAX
                            continue
                        ordered = sorted(values)
                        median = ordered[len(ordered) // 2]
                        deviations = sorted(abs(value - median) for value in values)
                        mad = deviations[len(deviations) // 2]
                        relative_dispersion = min(
                            RDRTP_V_MAX, mad / max(abs(median), EPSILON)
                        )
                        dispersion[group] = relative_dispersion
                        count_confidence = min(1.0, len(values) / (RDRTP_N0 + len(values)))
                        confidence[group] = count_confidence * math.exp(
                            -RDRTP_LAMBDA_V * relative_dispersion
                        )
                    self.last_confidence = min(confidence.values())
                    self.last_dispersion = dispersion
                    self.last_alpha = RDRTP_ALPHA_MAX * self.last_confidence
                    smoothed = [
                        (1.0 - self.last_alpha) * UNIFORM_Q
                        + self.last_alpha * drtp_candidate[index]
                        for index, group in enumerate(FAILURE_GROUPS)
                    ]
                    reason = "reliability_gated_bounded_exponential_gradient"
                else:
                    smoothed = [
                        (1.0 - SMOOTHING_BETA) * self.q[group] + SMOOTHING_BETA * candidate[index]
                        for index, group in enumerate(FAILURE_GROUPS)
                    ]
                    reason = "bounded_exponentiated_gradient"
                projected = _bounded_simplex_projection(smoothed)
                self.q = dict(zip(FAILURE_GROUPS, projected))
                self.last_difficulty = raw_difficulty
                self.adaptation_count += 1
                adapted = True
            else:
                reason = "ema_not_ready"
        self.window_returns = {group: [] for group in ALL_GROUPS}
        return self.update_row(update, counts, adapted, reason)

    def manifest(self) -> dict:
        payload = {
            "protocol": "DRTP-SG-MAPPO-CONTRACT-V1",
            "mode": self.mode,
            "seed": self.seed,
            "total_updates": self.total_updates,
            "groups": {group: [list(member) for member in GROUP_MEMBERS[group]] for group in ALL_GROUPS},
            "nominal_mass": NOMINAL_MASS,
            "failure_groups": list(FAILURE_GROUPS),
            "uniform_q": UNIFORM_Q,
            "warmup_updates": WARMUP_UPDATES,
            "adapt_interval": ADAPT_INTERVAL,
            "ema_kappa": EMA_KAPPA,
            "temperature_eta": TEMPERATURE_ETA,
            "smoothing_beta": SMOOTHING_BETA,
            "difficulty_max": DIFFICULTY_MAX,
            "epsilon": EPSILON,
            "q_min": Q_MIN,
            "q_max": Q_MAX,
            "r_drtp_n0": RDRTP_N0,
            "r_drtp_lambda_v": RDRTP_LAMBDA_V,
            "r_drtp_v_max": RDRTP_V_MAX,
            "r_drtp_alpha_max": RDRTP_ALPHA_MAX,
            "actor_or_critic_condition_input": False,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return {**payload, "sampler_hash": hashlib.sha256(encoded).hexdigest()}

    @staticmethod
    def log_fields() -> list[str]:
        fields = [
            "record_type", "update", "env_index", "episode_index", "group", "condition",
            "failed_blue_agent", "failure_start_step", "failure_duration_steps",
            "adapted", "reason", "adaptation_count",
        ]
        fields += [f"q_{group}" for group in FAILURE_GROUPS]
        fields += [f"ema_{group}" for group in ALL_GROUPS]
        fields += [f"difficulty_{group}" for group in FAILURE_GROUPS]
        fields += [f"window_count_{group}" for group in ALL_GROUPS]
        fields += ["confidence", "alpha"]
        fields += [f"dispersion_{group}" for group in FAILURE_GROUPS]
        return fields

    def _state_row(self) -> dict:
        row = {f"q_{group}": self.q[group] for group in FAILURE_GROUPS}
        row.update({f"ema_{group}": "" if self.ema[group] is None else self.ema[group] for group in ALL_GROUPS})
        row.update({f"difficulty_{group}": self.last_difficulty[group] for group in FAILURE_GROUPS})
        row.update({f"window_count_{group}": len(self.window_returns[group]) for group in ALL_GROUPS})
        row["confidence"] = self.last_confidence
        row["alpha"] = self.last_alpha
        row.update({f"dispersion_{group}": self.last_dispersion[group] for group in FAILURE_GROUPS})
        return row

    def selection_row(self, update: int, env_index: int, episode_index: int,
                      selection: DRTPSelection) -> dict:
        return {
            "record_type": "selection", "update": int(update), "env_index": int(env_index),
            "episode_index": int(episode_index), "group": selection.group,
            "condition": selection.condition, "failed_blue_agent": selection.failed_blue_agent,
            "failure_start_step": selection.failure_start_step,
            "failure_duration_steps": selection.failure_duration_steps,
            "adapted": False, "reason": "reset_selection", "adaptation_count": self.adaptation_count,
            **self._state_row(),
        }

    def update_row(self, update: int, counts: dict[str, int], adapted: bool, reason: str) -> dict:
        state = self._state_row()
        state.update({f"window_count_{group}": counts[group] for group in ALL_GROUPS})
        return {
            "record_type": "weight_update", "update": int(update), "env_index": "", "episode_index": "",
            "group": "", "condition": "", "failed_blue_agent": "", "failure_start_step": "",
            "failure_duration_steps": "", "adapted": bool(adapted), "reason": reason,
            "adaptation_count": self.adaptation_count, **state,
        }
