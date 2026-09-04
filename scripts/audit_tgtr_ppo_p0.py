"""Zero-training static and synthetic audit for the TGTR-PPO P0 dossier."""

from __future__ import annotations

import argparse
from itertools import combinations
import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
TRAINER = ROOT / "algorithms" / "ri_gmappo" / "simple_ri_gmappo.py"
TELEMETRY = ROOT / "algorithms" / "ri_gmappo" / "group_credit_telemetry.py"
SAMPLER = ROOT / "algorithms" / "ri_gmappo" / "tcr_topology_sampler.py"
RESULT = ROOT / "docs" / "tgtr_ppo_p0_20260904" / "TGTR_PPO_P0_RESULT.json"


def project_halfspaces(anchor: np.ndarray, rows: np.ndarray, tol: float = 1e-9) -> np.ndarray:
    """Exact small active-set projection: min ||x-anchor||^2 s.t. rows @ x >= 0."""
    m = rows.shape[0]
    best = None
    best_cost = np.inf
    for size in range(m + 1):
        for active in combinations(range(m), size):
            if not active:
                candidate = anchor.copy()
                multipliers = np.empty(0)
            else:
                active_rows = rows[np.asarray(active)]
                gram = active_rows @ active_rows.T
                multipliers = np.linalg.pinv(gram) @ (-active_rows @ anchor)
                candidate = anchor + active_rows.T @ multipliers
            if np.any(multipliers < -tol):
                continue
            if np.all(rows @ candidate >= -tol):
                cost = float(np.square(candidate - anchor).sum())
                if cost < best_cost:
                    best, best_cost = candidate, cost
    if best is None:
        raise RuntimeError("zero-feasible halfspace projection unexpectedly failed")
    return best


def synthetic_projection_audit() -> dict[str, object]:
    rng = np.random.default_rng(20260904)
    trials = 64
    max_violation = 0.0
    nonexpansive = True
    for _ in range(trials):
        rows = rng.normal(size=(7, 8))
        anchor = rng.normal(size=8)
        projected = project_halfspaces(anchor, rows)
        max_violation = max(max_violation, float(np.maximum(-(rows @ projected), 0.0).max()))
        nonexpansive &= bool(
            np.linalg.norm(projected - anchor) <= np.linalg.norm(anchor) + 1e-8
        )
    return {
        "trials": trials,
        "max_constraint_violation": max_violation,
        "zero_is_always_feasible": True,
        "projection_no_farther_than_zero": nonexpansive,
    }


def audit() -> dict[str, object]:
    trainer = TRAINER.read_text(encoding="utf-8")
    telemetry = TELEMETRY.read_text(encoding="utf-8")
    sampler = SAMPLER.read_text(encoding="utf-8")
    frozen = json.loads(RESULT.read_text(encoding="utf-8"))
    proposed = frozen["proposed_batch"]
    stream_count_ok = (
        proposed["nominal_streams"]
        + 6 * proposed["failure_streams_per_group"]
        == proposed["num_envs"]
    )
    mass_ok = abs(
        proposed["nominal_mass"] + 6 * proposed["failure_group_mass"] - 1.0
    ) < 1e-12
    checks = {
        "rollout_carries_condition_group": '"condition_group": np.asarray(condition_group_buf' in trainer,
        "telemetry_builds_per_group_actor_gradients": "actor_gradients[group]" in telemetry,
        "telemetry_uses_current_training_batch": "batch[\"condition_group\"]" in telemetry,
        "actor_exposes_full_logits": "return logits, attn, intent_logits" in trainer,
        "actor_optimizer_transaction_exists": all(
            token in trainer
            for token in (
                "actor_state_before",
                "actor_optimizer_state_before",
                "_restore_optimizer_parameter_states",
                "_set_parameter_interpolation_",
            )
        ),
        "legacy_sampler_requires_four_envs": 'num_envs) != 4' in sampler,
        "legacy_sampler_has_only_two_failure_streams": "FAILURE_STREAMS = (2, 3)" in sampler,
        "proposed_stream_arithmetic_exact": stream_count_ok,
        "proposed_probability_mass_exact": mass_ok,
        "result_forbids_training": (
            frozen["environment_steps"] == 0
            and frozen["ppo_updates"] == 0
            and frozen["training_started"] is False
            and frozen["fresh_seed_training_authorized"] is False
        ),
    }
    synthetic = synthetic_projection_audit()
    passed = all(checks.values()) and synthetic["max_constraint_violation"] <= 1e-8 and synthetic["projection_no_farther_than_zero"]
    return {
        "protocol": frozen["protocol"],
        "verdict": "TGTR_P0_FEASIBLE_FOR_C1" if passed else "TGTR_P0_NO_GO",
        "checks": checks,
        "synthetic_projection": synthetic,
        "environment_steps": 0,
        "ppo_updates": 0,
        "training_started": False,
        "automatic_continuation": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = audit()
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(result["verdict"])
    if result["verdict"] != "TGTR_P0_FEASIBLE_FOR_C1":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
