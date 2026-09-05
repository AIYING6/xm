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
# Frozen by DRTP-STABILIZATION-S0-V1 from label-free pooled, post-projection
# original-DRTP q movements.  These are method constants, not sweep options.
DRTP_TRUST_REGION_L1 = 0.02513300038143937
CONSERVATIVE_UNIFORM_ANCHOR = 0.20
EGTR_CONFIDENCE_KAPPA = 0.20
EGTR_REQUIRED_SAMPLES = 8.0
EGTR_TRUST_REGION_L1 = 0.10
EGTR_MAD_SCALE = 1.4826


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
        if self.mode not in {"utr", "drtp", "pp_drtp", "r_drtp", "egtr", "anchored_egtr", "drtp_tr", "conservative_drtp"}:
            raise ValueError("unsupported DRTP sampler mode")
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
        self.last_target_l1 = 0.0
        self.last_q_step_l1 = 0.0
        self.last_trust_region_active = False
        # Read-only S2 audit state.  These vectors never enter observations,
        # rewards, PPO, or the selection RNG; they expose the exact frozen
        # target -> projection -> optional anchor -> final-TR sequence.
        self.last_adaptive_target = {group: UNIFORM_Q for group in FAILURE_GROUPS}
        self.last_projected_target = {group: UNIFORM_Q for group in FAILURE_GROUPS}
        self.last_anchored_target = {group: UNIFORM_Q for group in FAILURE_GROUPS}
        self.last_pre_tr_l1 = 0.0
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
            "last_target_l1": float(self.last_target_l1),
            "last_q_step_l1": float(self.last_q_step_l1),
            "last_trust_region_active": bool(self.last_trust_region_active),
            "last_adaptive_target": {group: float(self.last_adaptive_target[group]) for group in FAILURE_GROUPS},
            "last_projected_target": {group: float(self.last_projected_target[group]) for group in FAILURE_GROUPS},
            "last_anchored_target": {group: float(self.last_anchored_target[group]) for group in FAILURE_GROUPS},
            "last_pre_tr_l1": float(self.last_pre_tr_l1),
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
        self.last_target_l1 = float(state.get("last_target_l1", 0.0))
        self.last_q_step_l1 = float(state.get("last_q_step_l1", 0.0))
        self.last_trust_region_active = bool(state.get("last_trust_region_active", False))
        self.last_adaptive_target = {group: float(state.get("last_adaptive_target", {}).get(group, UNIFORM_Q)) for group in FAILURE_GROUPS}
        self.last_projected_target = {group: float(state.get("last_projected_target", {}).get(group, UNIFORM_Q)) for group in FAILURE_GROUPS}
        self.last_anchored_target = {group: float(state.get("last_anchored_target", {}).get(group, UNIFORM_Q)) for group in FAILURE_GROUPS}
        self.last_pre_tr_l1 = float(state.get("last_pre_tr_l1", 0.0))
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
        if self.mode in {"drtp", "r_drtp", "drtp_tr", "conservative_drtp"} and update > WARMUP_UPDATES:
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
                        # Reach full count confidence once the frozen minimum
                        # sample count is met; otherwise R-DRTP would never
                        # be able to recover the original DRTP update exactly.
                        count_confidence = min(1.0, len(values) / RDRTP_N0)
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
                self.last_adaptive_target = dict(zip(FAILURE_GROUPS, smoothed))
                self.last_projected_target = dict(zip(FAILURE_GROUPS, projected))
                self.last_anchored_target = dict(zip(FAILURE_GROUPS, projected))
                self.last_target_l1 = 0.0
                self.last_pre_tr_l1 = 0.0
                self.last_q_step_l1 = 0.0
                self.last_trust_region_active = False
                if self.mode in {"drtp_tr", "conservative_drtp"}:
                    # S1: DRTP target -> bounded-simplex projection -> final
                    # L1 trust region.  S2 blends its uniform anchor into the
                    # target before that same final bound, so no post-TR step
                    # can invalidate the frozen L1 guarantee.
                    if self.mode == "conservative_drtp":
                        projected = [
                            (1.0 - CONSERVATIVE_UNIFORM_ANCHOR) * value
                            + CONSERVATIVE_UNIFORM_ANCHOR * UNIFORM_Q
                            for value in projected
                        ]
                    self.last_anchored_target = dict(zip(FAILURE_GROUPS, projected))
                    current = [self.q[group] for group in FAILURE_GROUPS]
                    self.last_target_l1 = sum(abs(left - right) for left, right in zip(projected, current))
                    self.last_pre_tr_l1 = self.last_target_l1
                    scale = 1.0 if self.last_target_l1 <= DRTP_TRUST_REGION_L1 else DRTP_TRUST_REGION_L1 / self.last_target_l1
                    projected = [left + scale * (right - left) for left, right in zip(current, projected)]
                    self.last_q_step_l1 = sum(abs(left - right) for left, right in zip(projected, current))
                    self.last_trust_region_active = scale < 1.0
                    if self.last_q_step_l1 > DRTP_TRUST_REGION_L1 + 1e-10:
                        raise AssertionError("DRTP-TR final q movement violated frozen L1 bound")
                    if not math.isclose(sum(projected), 1.0, rel_tol=0.0, abs_tol=1e-10):
                        raise AssertionError("DRTP-TR final q lost simplex mass")
                    if any(value < Q_MIN - 1e-12 or value > Q_MAX + 1e-12 for value in projected):
                        raise AssertionError("DRTP-TR final q violated floor/cap")
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
            "drtp_trust_region_l1": DRTP_TRUST_REGION_L1,
            "conservative_uniform_anchor": CONSERVATIVE_UNIFORM_ANCHOR,
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
        fields += ["confidence", "alpha", "target_l1", "q_step_l1", "trust_region_active"]
        fields += [f"adaptive_target_{group}" for group in FAILURE_GROUPS]
        fields += [f"projected_target_{group}" for group in FAILURE_GROUPS]
        fields += [f"anchored_target_{group}" for group in FAILURE_GROUPS]
        fields += ["pre_tr_l1"]
        fields += [f"dispersion_{group}" for group in FAILURE_GROUPS]
        return fields

    def _state_row(self) -> dict:
        row = {f"q_{group}": self.q[group] for group in FAILURE_GROUPS}
        row.update({f"ema_{group}": "" if self.ema[group] is None else self.ema[group] for group in ALL_GROUPS})
        row.update({f"difficulty_{group}": self.last_difficulty[group] for group in FAILURE_GROUPS})
        row.update({f"window_count_{group}": len(self.window_returns[group]) for group in ALL_GROUPS})
        row["confidence"] = self.last_confidence
        row["alpha"] = self.last_alpha
        row["target_l1"] = self.last_target_l1
        row["q_step_l1"] = self.last_q_step_l1
        row["trust_region_active"] = self.last_trust_region_active
        row.update({f"adaptive_target_{group}": self.last_adaptive_target[group] for group in FAILURE_GROUPS})
        row.update({f"projected_target_{group}": self.last_projected_target[group] for group in FAILURE_GROUPS})
        row.update({f"anchored_target_{group}": self.last_anchored_target[group] for group in FAILURE_GROUPS})
        row["pre_tr_l1"] = self.last_pre_tr_l1
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


class PairedProbeTopologySampler(DRTPTopologySampler):
    """DRTP whose sampler evidence comes from balanced paired probe rollouts.

    Training selections still use ``q`` exactly as in DRTP.  The only semantic
    change is that completed training returns are never used to update the
    group EMAs.  Instead, a caller supplies an equal-count, common-base-id
    probe batch immediately before each post-warm-up adaptation boundary.
    """

    uses_completed_return_feedback = False

    def __init__(self, seed: int, total_updates: int, probe_count: int = 4):
        super().__init__("pp_drtp", seed, total_updates)
        if int(probe_count) <= 0:
            raise ValueError("PP-DRTP probe_count must be positive")
        self.probe_count = int(probe_count)
        self.pending_probe_update: int | None = None
        self.pending_probe_returns: dict[str, list[float]] = {group: [] for group in ALL_GROUPS}
        self.pending_probe_base_ids: tuple[int, ...] = ()
        self.last_probe_counts = {group: 0 for group in ALL_GROUPS}
        self.last_probe_base_id_count = 0
        self.last_probe_returns: dict[str, float | None] = {group: None for group in ALL_GROUPS}
        self.last_probe_gaps = {group: 0.0 for group in FAILURE_GROUPS}

    @staticmethod
    def _median(values: list[float]) -> float:
        if not values:
            raise ValueError("median requires at least one value")
        ordered = sorted(float(value) for value in values)
        midpoint = len(ordered) // 2
        return ordered[midpoint] if len(ordered) % 2 else (ordered[midpoint - 1] + ordered[midpoint]) / 2.0

    def record_probe_batch(self, update: int, records: list[dict]) -> None:
        """Accept one complete, balanced training-only probe batch.

        Every group must have exactly ``probe_count`` records on the same base
        identifiers.  This check is intentionally strict: an incomplete probe
        batch must never silently fall back to exposure-dependent returns.
        """
        update = int(update)
        if update % ADAPT_INTERVAL != 0 or update <= WARMUP_UPDATES:
            raise ValueError("PP-DRTP probes are valid only at post-warm-up adaptation boundaries")
        if self.pending_probe_update is not None:
            raise RuntimeError("PP-DRTP already has a pending probe batch")
        grouped: dict[str, dict[int, float]] = {group: {} for group in ALL_GROUPS}
        for record in records:
            group = str(record["group"])
            base_id = int(record["base_id"])
            episode_return = float(record["episode_return"])
            if group not in grouped or not math.isfinite(episode_return):
                raise ValueError("invalid PP-DRTP probe record")
            if base_id in grouped[group]:
                raise ValueError("duplicate PP-DRTP group/base-id probe record")
            grouped[group][base_id] = episode_return
        reference_ids = None
        for group in ALL_GROUPS:
            identifiers = tuple(sorted(grouped[group]))
            if len(identifiers) != self.probe_count:
                raise ValueError("PP-DRTP probe batch has incorrect group count")
            if reference_ids is None:
                reference_ids = identifiers
            elif identifiers != reference_ids:
                raise ValueError("PP-DRTP probe groups do not share base identifiers")
        self.pending_probe_update = update
        self.pending_probe_base_ids = () if reference_ids is None else reference_ids
        self.pending_probe_returns = {
            group: [grouped[group][base_id] for base_id in self.pending_probe_base_ids]
            for group in ALL_GROUPS
        }

    def _refresh_probe_ema(self) -> None:
        for group in ALL_GROUPS:
            observed = self._median(self.pending_probe_returns[group])
            old = self.ema[group]
            self.ema[group] = observed if old is None else (1.0 - EMA_KAPPA) * old + EMA_KAPPA * observed
            self.last_probe_returns[group] = observed
        nominal = float(self.last_probe_returns[NOMINAL_GROUP])
        self.last_probe_gaps = {
            group: nominal - float(self.last_probe_returns[group])
            for group in FAILURE_GROUPS
        }

    def maybe_update(self, update: int) -> dict | None:
        update = int(update)
        if update % ADAPT_INTERVAL != 0:
            return None
        counts = {group: len(self.pending_probe_returns[group]) for group in ALL_GROUPS}
        adapted = False
        reason = "warmup"
        if update > WARMUP_UPDATES:
            if self.pending_probe_update != update:
                raise RuntimeError("PP-DRTP requires a complete probe batch before every adaptation")
            self._refresh_probe_ema()
            nominal = float(self.ema[NOMINAL_GROUP])
            raw_difficulty = {
                group: min(
                    DIFFICULTY_MAX,
                    max(0.0, (nominal - float(self.ema[group])) / max(abs(nominal), EPSILON)),
                )
                for group in FAILURE_GROUPS
            }
            mean_difficulty = sum(raw_difficulty.values()) / len(FAILURE_GROUPS)
            logits = {
                group: self.q[group] * math.exp(TEMPERATURE_ETA * (raw_difficulty[group] - mean_difficulty))
                for group in FAILURE_GROUPS
            }
            normalizer = sum(logits.values())
            candidate = [logits[group] / normalizer for group in FAILURE_GROUPS]
            smoothed = [
                (1.0 - SMOOTHING_BETA) * self.q[group] + SMOOTHING_BETA * candidate[index]
                for index, group in enumerate(FAILURE_GROUPS)
            ]
            projected = _bounded_simplex_projection(smoothed)
            self.last_adaptive_target = dict(zip(FAILURE_GROUPS, smoothed))
            self.last_projected_target = dict(zip(FAILURE_GROUPS, projected))
            self.last_anchored_target = dict(zip(FAILURE_GROUPS, projected))
            self.last_target_l1 = 0.0
            self.last_pre_tr_l1 = 0.0
            self.last_q_step_l1 = 0.0
            self.last_trust_region_active = False
            self.q = dict(zip(FAILURE_GROUPS, projected))
            self.last_difficulty = raw_difficulty
            self.adaptation_count += 1
            adapted = True
            reason = "paired_probe_bounded_exponentiated_gradient"
        self.last_probe_counts = dict(counts)
        self.last_probe_base_id_count = len(self.pending_probe_base_ids)
        self.pending_probe_update = None
        self.pending_probe_returns = {group: [] for group in ALL_GROUPS}
        self.pending_probe_base_ids = ()
        return self.update_row(update, counts, adapted, reason)

    def state_dict(self) -> dict:
        state = super().state_dict()
        state["format"] = "paired_probe_drtp_topology_sampler_runtime_state_v1"
        state.update({
            "probe_count": self.probe_count,
            "pending_probe_update": self.pending_probe_update,
            "pending_probe_returns": {group: list(self.pending_probe_returns[group]) for group in ALL_GROUPS},
            "pending_probe_base_ids": list(self.pending_probe_base_ids),
            "last_probe_counts": dict(self.last_probe_counts),
            "last_probe_base_id_count": self.last_probe_base_id_count,
            "last_probe_returns": dict(self.last_probe_returns),
            "last_probe_gaps": dict(self.last_probe_gaps),
        })
        return state

    def load_state_dict(self, state: dict) -> None:
        if state.get("format") != "paired_probe_drtp_topology_sampler_runtime_state_v1":
            raise ValueError("unsupported PP-DRTP sampler runtime state")
        if int(state.get("probe_count", -1)) != self.probe_count:
            raise ValueError("PP-DRTP runtime state uses another probe_count")
        base = dict(state)
        base["format"] = "drtp_topology_sampler_runtime_state_v1"
        super().load_state_dict(base)
        pending = state.get("pending_probe_returns", {})
        self.pending_probe_returns = {
            group: [float(value) for value in pending.get(group, [])]
            for group in ALL_GROUPS
        }
        if any(not math.isfinite(value) for values in self.pending_probe_returns.values() for value in values):
            raise ValueError("PP-DRTP runtime state has non-finite pending probe return")
        self.pending_probe_update = (
            None if state.get("pending_probe_update") is None else int(state["pending_probe_update"])
        )
        self.pending_probe_base_ids = tuple(int(value) for value in state.get("pending_probe_base_ids", []))
        self.last_probe_counts = {
            group: int(state.get("last_probe_counts", {}).get(group, 0))
            for group in ALL_GROUPS
        }
        self.last_probe_base_id_count = int(state.get("last_probe_base_id_count", 0))
        self.last_probe_returns = {
            group: None if state.get("last_probe_returns", {}).get(group) is None
            else float(state["last_probe_returns"][group])
            for group in ALL_GROUPS
        }
        self.last_probe_gaps = {
            group: float(state.get("last_probe_gaps", {}).get(group, 0.0))
            for group in FAILURE_GROUPS
        }

    def manifest(self) -> dict:
        payload = super().manifest()
        payload.update({
            "protocol": "PP-DRTP-SG-MAPPO-CONTRACT-V1",
            "probe_count": self.probe_count,
            "probe_estimator": "same-base-id per-group median return",
            "uses_completed_training_return_feedback": False,
        })
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return {**payload, "sampler_hash": hashlib.sha256(encoded).hexdigest()}

    @staticmethod
    def log_fields() -> list[str]:
        fields = DRTPTopologySampler.log_fields()
        fields += [f"probe_count_{group}" for group in ALL_GROUPS]
        fields += [f"probe_return_{group}" for group in ALL_GROUPS]
        fields += [f"probe_gap_{group}" for group in FAILURE_GROUPS]
        fields += ["probe_base_id_count"]
        return fields

    def _state_row(self) -> dict:
        row = super()._state_row()
        row.update({f"probe_count_{group}": self.last_probe_counts[group] for group in ALL_GROUPS})
        row.update({
            f"probe_return_{group}": "" if self.last_probe_returns[group] is None else self.last_probe_returns[group]
            for group in ALL_GROUPS
        })
        row.update({f"probe_gap_{group}": self.last_probe_gaps[group] for group in FAILURE_GROUPS})
        row["probe_base_id_count"] = self.last_probe_base_id_count
        return row


class EGTRTopologySampler(DRTPTopologySampler):
    """Per-group evidence gate followed by a sampler L1 trust region."""

    def __init__(self, seed: int, total_updates: int, *, mode: str = "egtr"):
        if mode not in {"egtr", "anchored_egtr"}:
            raise ValueError("EGTR sampler mode must be egtr or anchored_egtr")
        super().__init__(mode, seed, total_updates)
        self.confidence_ema = {group: 0.0 for group in FAILURE_GROUPS}
        self.stale_duration = {group: 0 for group in FAILURE_GROUPS}
        self.last_rho = 0.0
        self.last_trust_distance = 0.0
        self.last_trust_active = False
        self.last_q_uniform_distance = 0.0
        self.last_q_step_l1 = 0.0
        self.last_q_star = [UNIFORM_Q] * len(FAILURE_GROUPS)
        self.last_evidence = {group: {"gap": 0.0, "r": 0.0} for group in FAILURE_GROUPS}

    @staticmethod
    def _median(values: list[float]) -> float:
        if not values:
            return 0.0
        ordered = sorted(float(value) for value in values)
        middle = len(ordered) // 2
        return ordered[middle] if len(ordered) % 2 else 0.5 * (ordered[middle - 1] + ordered[middle])

    @classmethod
    def _robust_se(cls, values: list[float]) -> float:
        if not values:
            return 0.0
        median = cls._median(values)
        mad = cls._median([abs(float(value) - median) for value in values])
        return EGTR_MAD_SCALE * mad / math.sqrt(max(len(values), 1))

    def _evidence(self, group: str, nominal_values: list[float]) -> tuple[float, float]:
        values = self.window_returns[group]
        n_nominal, n_group = len(nominal_values), len(values)
        m_nominal, m_group = self._median(nominal_values), self._median(values)
        s_nominal, s_group = self._robust_se(nominal_values), self._robust_se(values)
        gap = max(m_nominal - m_group, 0.0)
        availability = min(1.0, n_nominal / EGTR_REQUIRED_SAMPLES) * min(1.0, n_group / EGTR_REQUIRED_SAMPLES)
        reliability = availability * gap / (gap + math.sqrt(s_nominal ** 2 + s_group ** 2) + EPSILON)
        return gap, reliability

    def state_dict(self) -> dict:
        state = super().state_dict()
        for key in ("last_confidence", "last_alpha", "last_dispersion"):
            state.pop(key, None)
        state["format"] = "egtr_topology_sampler_runtime_state_v1"
        state.update({
            "confidence_ema": {group: float(self.confidence_ema[group]) for group in FAILURE_GROUPS},
            "stale_duration": {group: int(self.stale_duration[group]) for group in FAILURE_GROUPS},
        })
        return state

    def load_state_dict(self, state: dict) -> None:
        if state.get("format") != "egtr_topology_sampler_runtime_state_v1":
            raise ValueError("unsupported EGTR sampler runtime-state format")
        base = dict(state)
        base["format"] = "drtp_topology_sampler_runtime_state_v1"
        super().load_state_dict(base)
        self.confidence_ema = {group: float(state["confidence_ema"][group]) for group in FAILURE_GROUPS}
        self.stale_duration = {group: int(state["stale_duration"][group]) for group in FAILURE_GROUPS}
        if any(not math.isfinite(value) or not 0.0 <= value <= 1.0 for value in self.confidence_ema.values()):
            raise ValueError("EGTR confidence EMA out of bounds")
        if any(value < 0 for value in self.stale_duration.values()):
            raise ValueError("EGTR stale duration is negative")

    def _state_row(self) -> dict:
        row = super()._state_row()
        for key in ("confidence", "alpha", *[f"dispersion_{group}" for group in FAILURE_GROUPS]):
            row.pop(key, None)
        row.update({f"confidence_ema_{group}": self.confidence_ema[group] for group in FAILURE_GROUPS})
        row.update({f"stale_duration_{group}": self.stale_duration[group] for group in FAILURE_GROUPS})
        row.update({f"evidence_gap_{group}": self.last_evidence[group]["gap"] for group in FAILURE_GROUPS})
        row.update({f"evidence_r_{group}": self.last_evidence[group]["r"] for group in FAILURE_GROUPS})
        row.update({
            "rho": self.last_rho,
            "trust_region_distance": self.last_trust_distance,
            "trust_region_active": self.last_trust_active,
            "q_uniform_distance": self.last_q_uniform_distance,
            "q_step_l1": self.last_q_step_l1,
        })
        return row

    @staticmethod
    def log_fields() -> list[str]:
        fields = [
            field for field in DRTPTopologySampler.log_fields()
            if field not in {"confidence", "alpha", *[f"dispersion_{group}" for group in FAILURE_GROUPS]}
        ]
        fields += [f"confidence_ema_{group}" for group in FAILURE_GROUPS]
        fields += [f"stale_duration_{group}" for group in FAILURE_GROUPS]
        fields += [f"evidence_gap_{group}" for group in FAILURE_GROUPS]
        fields += [f"evidence_r_{group}" for group in FAILURE_GROUPS]
        fields += ["rho", "trust_region_distance", "trust_region_active", "q_uniform_distance", "q_step_l1"]
        return fields

    def maybe_update(self, update: int) -> dict | None:
        update = int(update)
        if update % ADAPT_INTERVAL != 0:
            return None
        counts = {group: len(values) for group, values in self.window_returns.items()}
        self._refresh_ema()
        nominal_values = self.window_returns[NOMINAL_GROUP]
        for group in FAILURE_GROUPS:
            gap, reliability = self._evidence(group, nominal_values)
            self.last_evidence[group] = {"gap": gap, "r": reliability}
            self.stale_duration[group] = 0 if counts[group] > 0 else self.stale_duration[group] + 1
            self.confidence_ema[group] = ((1.0 - EGTR_CONFIDENCE_KAPPA) * self.confidence_ema[group]
                                          + EGTR_CONFIDENCE_KAPPA * reliability)
        self.last_rho = sum(self.confidence_ema.values()) / len(FAILURE_GROUPS)
        previous = [self.q[group] for group in FAILURE_GROUPS]
        self.last_trust_distance = 0.0
        self.last_trust_active = False
        self.last_q_step_l1 = 0.0
        adapted = False
        reason = "warmup"
        egtr_ready = (
            update > WARMUP_UPDATES
            and self.ema[NOMINAL_GROUP] is not None
            and any(self.ema[group] is not None for group in FAILURE_GROUPS)
        )
        if egtr_ready:
            nominal = float(self.ema[NOMINAL_GROUP])
            difficulty = {
                group: 0.0 if self.ema[group] is None else min(
                    DIFFICULTY_MAX,
                    max(0.0, (nominal - float(self.ema[group])) / max(abs(nominal), EPSILON)),
                )
                for group in FAILURE_GROUPS
            }
            h = {group: self.confidence_ema[group] * difficulty[group] for group in FAILURE_GROUPS}
            center = sum(h.values()) / len(FAILURE_GROUPS)
            logits = {group: self.q[group] * math.exp(TEMPERATURE_ETA * (h[group] - center)) for group in FAILURE_GROUPS}
            normalizer = sum(logits.values())
            q_e = [logits[group] / normalizer for group in FAILURE_GROUPS]
            q_a = [(1.0 - self.last_rho) * UNIFORM_Q + self.last_rho * q_e[index]
                   for index in range(len(FAILURE_GROUPS))]
            z = [(1.0 - SMOOTHING_BETA) * self.q[group] + SMOOTHING_BETA * q_a[index]
                 for index, group in enumerate(FAILURE_GROUPS)]
            q_star = _bounded_simplex_projection(z)
            self.last_q_star = list(q_star)
            self.last_trust_distance = sum(abs(q_star[index] - previous[index]) for index in range(len(previous)))
            gamma = min(1.0, EGTR_TRUST_REGION_L1 / (self.last_trust_distance + EPSILON))
            self.last_trust_active = gamma < 1.0
            final_q = [previous[index] + gamma * (q_star[index] - previous[index]) for index in range(len(previous))]
            self.last_q_step_l1 = sum(abs(final_q[index] - previous[index]) for index in range(len(previous)))
            if self.last_q_step_l1 > EGTR_TRUST_REGION_L1 + 1e-10:
                raise AssertionError("EGTR final q step exceeded L1 trust region")
            self.q = dict(zip(FAILURE_GROUPS, final_q))
            self.last_difficulty = difficulty
            self.last_alpha = self.last_rho
            self.adaptation_count += 1
            adapted = True
            reason = "egtr_evidence_then_project_then_l1_trust_region"
        self.last_q_uniform_distance = sum(abs(self.q[group] - UNIFORM_Q) for group in FAILURE_GROUPS)
        self.window_returns = {group: [] for group in ALL_GROUPS}
        return self.update_row(update, counts, adapted, reason)

    def manifest(self) -> dict:
        payload = super().manifest()
        for key in ("protocol", "r_drtp_n0", "r_drtp_lambda_v", "r_drtp_v_max", "r_drtp_alpha_max"):
            payload.pop(key, None)
        payload.update({
            "protocol": "EGTR-DRTP-SG-MAPPO-CONTRACT-V1",
            "egtr_confidence_kappa": EGTR_CONFIDENCE_KAPPA,
            "egtr_required_samples": EGTR_REQUIRED_SAMPLES,
            "egtr_trust_region_l1": EGTR_TRUST_REGION_L1,
            "egtr_mad_scale": EGTR_MAD_SCALE,
            "trust_region_after_projection": True,
        })
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return {**payload, "sampler_hash": hashlib.sha256(encoded).hexdigest()}


class AnchoredEGTRTopologySampler(EGTRTopologySampler):
    """EGTR with a fixed global interpolation toward the UTR distribution.

    EGTR first performs its unchanged evidence, bounded-simplex and local-L1
    trust-region path.  This class then exposes the training sampler actually
    used for the next resets as ``(1-alpha) * q_UTR + alpha * q_EGTR``.  The
    latter convex interpolation preserves simplex and floor/cap feasibility
    while giving a direct absolute bound on its distance from UTR.
    """

    RUNTIME_FORMAT = "anchored_egtr_topology_sampler_runtime_state_v1"

    def __init__(self, seed: int, total_updates: int, anchor_alpha: float):
        if not math.isfinite(float(anchor_alpha)) or not 0.0 <= float(anchor_alpha) <= 1.0:
            raise ValueError("anchored-EGTR alpha must lie in [0, 1]")
        super().__init__(seed, total_updates, mode="anchored_egtr")
        self.anchor_alpha = float(anchor_alpha)
        self.last_pre_anchor_q = {group: UNIFORM_Q for group in FAILURE_GROUPS}
        self.last_post_anchor_q = {group: UNIFORM_Q for group in FAILURE_GROUPS}
        self.last_pre_anchor_uniform_l1 = 0.0
        self.last_post_anchor_uniform_l1 = 0.0
        self.last_egtr_q_step_l1 = 0.0
        self.last_anchor_active = False
        self.cumulative_exposure_deviation = {group: 0.0 for group in FAILURE_GROUPS}

    def state_dict(self) -> dict:
        state = super().state_dict()
        state["format"] = self.RUNTIME_FORMAT
        state.update({
            "anchor_alpha": self.anchor_alpha,
            "last_pre_anchor_q": {group: float(self.last_pre_anchor_q[group]) for group in FAILURE_GROUPS},
            "last_post_anchor_q": {group: float(self.last_post_anchor_q[group]) for group in FAILURE_GROUPS},
            "last_pre_anchor_uniform_l1": float(self.last_pre_anchor_uniform_l1),
            "last_post_anchor_uniform_l1": float(self.last_post_anchor_uniform_l1),
            "last_egtr_q_step_l1": float(self.last_egtr_q_step_l1),
            "last_anchor_active": bool(self.last_anchor_active),
            "cumulative_exposure_deviation": {
                group: float(self.cumulative_exposure_deviation[group]) for group in FAILURE_GROUPS
            },
        })
        return state

    def load_state_dict(self, state: dict) -> None:
        if state.get("format") != self.RUNTIME_FORMAT:
            raise ValueError("unsupported anchored-EGTR sampler runtime-state format")
        if not math.isclose(float(state.get("anchor_alpha")), self.anchor_alpha, rel_tol=0.0, abs_tol=1e-15):
            raise ValueError("anchored-EGTR runtime state belongs to a different alpha")
        base = dict(state)
        base["format"] = "egtr_topology_sampler_runtime_state_v1"
        super().load_state_dict(base)
        self.last_pre_anchor_q = {group: float(state["last_pre_anchor_q"][group]) for group in FAILURE_GROUPS}
        self.last_post_anchor_q = {group: float(state["last_post_anchor_q"][group]) for group in FAILURE_GROUPS}
        self.last_pre_anchor_uniform_l1 = float(state["last_pre_anchor_uniform_l1"])
        self.last_post_anchor_uniform_l1 = float(state["last_post_anchor_uniform_l1"])
        self.last_egtr_q_step_l1 = float(state["last_egtr_q_step_l1"])
        self.last_anchor_active = bool(state["last_anchor_active"])
        self.cumulative_exposure_deviation = {
            group: float(state["cumulative_exposure_deviation"][group]) for group in FAILURE_GROUPS
        }
        if any(not math.isfinite(value) for value in (
            *self.last_pre_anchor_q.values(), *self.last_post_anchor_q.values(),
            self.last_pre_anchor_uniform_l1, self.last_post_anchor_uniform_l1,
            self.last_egtr_q_step_l1, *self.cumulative_exposure_deviation.values(),
        )):
            raise ValueError("anchored-EGTR runtime state contains non-finite telemetry")

    def _state_row(self) -> dict:
        row = super()._state_row()
        row.update({f"pre_anchor_q_{group}": self.last_pre_anchor_q[group] for group in FAILURE_GROUPS})
        row.update({f"post_anchor_q_{group}": self.last_post_anchor_q[group] for group in FAILURE_GROUPS})
        row.update({
            "anchor_alpha": self.anchor_alpha,
            "anchor_active": self.last_anchor_active,
            "pre_anchor_uniform_l1": self.last_pre_anchor_uniform_l1,
            "post_anchor_uniform_l1": self.last_post_anchor_uniform_l1,
            "global_anchor_l1_bound": 2.0 * self.anchor_alpha,
            "egtr_q_step_l1": self.last_egtr_q_step_l1,
        })
        row.update({
            f"cumulative_exposure_deviation_{group}": self.cumulative_exposure_deviation[group]
            for group in FAILURE_GROUPS
        })
        return row

    @staticmethod
    def log_fields() -> list[str]:
        fields = EGTRTopologySampler.log_fields()
        fields += [f"pre_anchor_q_{group}" for group in FAILURE_GROUPS]
        fields += [f"post_anchor_q_{group}" for group in FAILURE_GROUPS]
        fields += [
            "anchor_alpha", "anchor_active", "pre_anchor_uniform_l1",
            "post_anchor_uniform_l1", "global_anchor_l1_bound", "egtr_q_step_l1",
        ]
        fields += [f"cumulative_exposure_deviation_{group}" for group in FAILURE_GROUPS]
        return fields

    def maybe_update(self, update: int) -> dict | None:
        previous = {group: self.q[group] for group in FAILURE_GROUPS}
        row = super().maybe_update(update)
        if row is None:
            return None
        counts = {group: int(row[f"window_count_{group}"]) for group in ALL_GROUPS}
        adapted = bool(row["adapted"])
        self.last_pre_anchor_q = {group: self.q[group] for group in FAILURE_GROUPS}
        self.last_pre_anchor_uniform_l1 = sum(
            abs(self.last_pre_anchor_q[group] - UNIFORM_Q) for group in FAILURE_GROUPS
        )
        self.last_egtr_q_step_l1 = self.last_q_step_l1
        post_anchor = {
            group: ((1.0 - self.anchor_alpha) * UNIFORM_Q + self.anchor_alpha * self.last_pre_anchor_q[group])
            for group in FAILURE_GROUPS
        }
        if not math.isclose(sum(post_anchor.values()), 1.0, rel_tol=0.0, abs_tol=1e-10):
            raise AssertionError("anchored-EGTR final q lost simplex mass")
        if any(value < Q_MIN - 1e-12 or value > Q_MAX + 1e-12 for value in post_anchor.values()):
            raise AssertionError("anchored-EGTR final q violated floor/cap")
        self.q = post_anchor
        self.last_post_anchor_q = dict(post_anchor)
        self.last_post_anchor_uniform_l1 = sum(abs(post_anchor[group] - UNIFORM_Q) for group in FAILURE_GROUPS)
        if self.last_post_anchor_uniform_l1 > 2.0 * self.anchor_alpha + 1e-10:
            raise AssertionError("anchored-EGTR violated its global UTR-distance bound")
        self.last_q_uniform_distance = self.last_post_anchor_uniform_l1
        self.last_q_step_l1 = sum(abs(post_anchor[group] - previous[group]) for group in FAILURE_GROUPS)
        self.last_anchor_active = self.anchor_alpha < 1.0 and any(
            abs(post_anchor[group] - self.last_pre_anchor_q[group]) > 1e-14 for group in FAILURE_GROUPS
        )
        for group in FAILURE_GROUPS:
            self.cumulative_exposure_deviation[group] += post_anchor[group] - UNIFORM_Q
        reason = (
            "egtr_evidence_then_project_then_l1_trust_region_then_global_utr_anchor"
            if adapted else "egtr_warmup_then_global_utr_anchor"
        )
        return self.update_row(int(update), counts, adapted, reason)

    def manifest(self) -> dict:
        payload = super().manifest()
        payload.update({
            "protocol": "GLOBAL-ANCHORED-EGTR-DRTP-SG-MAPPO-CONTRACT-V1",
            "global_anchor_alpha": self.anchor_alpha,
            "global_anchor_formula": "q_final=(1-alpha)*q_utr+alpha*q_egtr",
            "global_anchor_absolute_l1_bound": 2.0 * self.anchor_alpha,
            "egtr_local_trust_region_path_preserved_before_anchor": True,
            "anchor_after_egtr_local_trust_region": True,
        })
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return {**payload, "sampler_hash": hashlib.sha256(encoded).hexdigest()}
