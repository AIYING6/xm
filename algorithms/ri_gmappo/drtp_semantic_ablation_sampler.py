"""Reset-side semantic and adaptive ablations for the frozen DRTP sampler.

The classes here are deliberately isolated from the actor, critic, reward,
observation, action, and PPO code.  They are not wired into the maintained
learner.  A future, separately frozen ablation package may import them only
after source-provenance preflight passes.
"""
from __future__ import annotations

import hashlib
import json
import math
import random

from algorithms.ri_gmappo.drtp_topology_sampler import (
    ADAPT_INTERVAL,
    ALL_GROUPS,
    DIFFICULTY_MAX,
    EMA_KAPPA,
    EPSILON,
    FAILURE_GROUPS,
    NOMINAL_GROUP,
    SMOOTHING_BETA,
    TEMPERATURE_ETA,
    UNIFORM_Q,
    WARMUP_UPDATES,
    DRTPTopologySampler,
    _bounded_simplex_projection,
)


MODES = {"random_drtp", "fixed_drtp"}
PERMUTATION_SALT = 0x5E6A_2026


class SemanticAblationTopologySampler(DRTPTopologySampler):
    """DRTP with exactly one ablated reset-side mechanism.

    ``random_drtp`` uses a deterministic, seed-bound permutation from target
    topology group to observed difficulty group at every update.  It retains
    online updates, bounds and the original reset condition library.

    ``fixed_drtp`` uses the semantic difficulty estimate at the first eligible
    post-warmup update, then freezes that feasible q for the remaining budget.
    It does not consult a development endpoint or any evaluation data.
    """

    def __init__(self, mode: str, seed: int, total_updates: int):
        if mode not in MODES:
            raise ValueError(f"unsupported semantic-ablation mode: {mode}")
        super().__init__("drtp", seed, total_updates)
        self.mode = mode
        shuffled = list(FAILURE_GROUPS)
        random.Random(self.seed ^ PERMUTATION_SALT).shuffle(shuffled)
        self.semantic_permutation = dict(zip(FAILURE_GROUPS, shuffled))
        self.fixed_q_initialized = False
        self.last_observed_difficulty = {group: 0.0 for group in FAILURE_GROUPS}

    def state_dict(self) -> dict:
        state = super().state_dict()
        state.update({
            "mode": self.mode,
            "semantic_permutation": dict(self.semantic_permutation),
            "fixed_q_initialized": self.fixed_q_initialized,
            "last_observed_difficulty": dict(self.last_observed_difficulty),
        })
        return state

    def load_state_dict(self, state: dict) -> None:
        super().load_state_dict(state)
        if state.get("semantic_permutation") != self.semantic_permutation:
            raise ValueError("semantic-ablation runtime state has a different frozen permutation")
        self.fixed_q_initialized = bool(state.get("fixed_q_initialized", False))
        self.last_observed_difficulty = {
            group: float(state.get("last_observed_difficulty", {}).get(group, 0.0))
            for group in FAILURE_GROUPS
        }

    def maybe_update(self, update: int) -> dict | None:
        update = int(update)
        if update % ADAPT_INTERVAL != 0:
            return None
        counts = {group: len(values) for group, values in self.window_returns.items()}
        self._refresh_ema()
        adapted = False
        if self.mode == "fixed_drtp" and self.fixed_q_initialized:
            reason = "fixed_q_after_first_eligible_semantic_update"
        elif update <= WARMUP_UPDATES:
            reason = "warmup"
        elif not self._ema_ready():
            reason = "ema_not_ready"
        else:
            nominal = float(self.ema[NOMINAL_GROUP])
            observed = {
                group: min(DIFFICULTY_MAX, max(0.0, (nominal - float(self.ema[group])) / max(abs(nominal), EPSILON)))
                for group in FAILURE_GROUPS
            }
            effective = (
                {group: observed[self.semantic_permutation[group]] for group in FAILURE_GROUPS}
                if self.mode == "random_drtp" else observed
            )
            mean_difficulty = sum(effective.values()) / len(FAILURE_GROUPS)
            logits = {
                group: self.q[group] * math.exp(TEMPERATURE_ETA * (effective[group] - mean_difficulty))
                for group in FAILURE_GROUPS
            }
            normalizer = sum(logits.values())
            candidate = [logits[group] / normalizer for group in FAILURE_GROUPS]
            smoothed = [
                (1.0 - SMOOTHING_BETA) * self.q[group] + SMOOTHING_BETA * candidate[index]
                for index, group in enumerate(FAILURE_GROUPS)
            ]
            projected = _bounded_simplex_projection(smoothed)
            self.q = dict(zip(FAILURE_GROUPS, projected))
            self.last_observed_difficulty = observed
            self.last_difficulty = effective
            self.last_adaptive_target = dict(zip(FAILURE_GROUPS, smoothed))
            self.last_projected_target = dict(zip(FAILURE_GROUPS, projected))
            self.last_anchored_target = dict(zip(FAILURE_GROUPS, projected))
            self.last_target_l1 = self.last_pre_tr_l1 = self.last_q_step_l1 = 0.0
            self.last_trust_region_active = False
            self.adaptation_count += 1
            self.fixed_q_initialized = self.mode == "fixed_drtp"
            adapted = True
            reason = "randomized_semantic_mapping_update" if self.mode == "random_drtp" else "first_eligible_semantic_update_then_fixed"
        self.window_returns = {group: [] for group in ALL_GROUPS}
        return self.update_row(update, counts, adapted, reason)

    def manifest(self) -> dict:
        payload = super().manifest()
        payload.pop("sampler_hash", None)
        payload.update({
            "mode": self.mode,
            "semantic_permutation": dict(self.semantic_permutation),
            "permutation_salt": PERMUTATION_SALT,
            "adaptation_rule": (
                "continue_with_permuted_group_difficulty" if self.mode == "random_drtp"
                else "freeze_after_first_eligible_semantic_update"
            ),
            "actor_or_critic_condition_input": False,
        })
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return {**payload, "sampler_hash": hashlib.sha256(encoded).hexdigest()}
