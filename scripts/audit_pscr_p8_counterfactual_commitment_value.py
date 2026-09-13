"""Paired, zero-training counterfactual audit for the P8 commitment decision.

Each matched pair uses the standard P8 environment, the same reset seed and
the same public reliability band.  The two branches differ only in the legal
team allocation selected at the public commitment window.  Future geometry
and urgency are never accessed by the pre-arrival controller; they are only
recorded after rollout to verify that the paired branches shared an identical
exogenous realization.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.pscr_search_prefix_env import P8SearchPrefixConfig, PSCRSearchPrefixEnv
from envs.pscr_full_team_commitment_env import PSCRFullTeamCommitmentEnv
from envs.pscr_service_reconfiguration_env import FORECAST_STAGE, FUTURE_SERVICE, PRIMARY_SERVICE


PROTOCOL = "PSCR-P8-COUNTERFACTUAL-COMMITMENT-VALUE-AUDIT-V1"
RELIABILITIES = (0.1, 0.9)
PLANS = ("maintain_primary", "stage_forecast")
MARGIN = 0.05


def actions_for(env: PSCRSearchPrefixEnv, plan: str, stage_mode: str) -> np.ndarray:
    """Return a fixed legal plan without inspecting unrealized future truth."""
    if env.future_active:
        return np.full(env.num_agents, FUTURE_SERVICE, dtype=np.int64)
    if env._commitment_active() and plan == "stage_forecast":
        if stage_mode == "full_team":
            return np.full(env.num_agents, FORECAST_STAGE, dtype=np.int64)
        return np.asarray((FORECAST_STAGE, FORECAST_STAGE, PRIMARY_SERVICE), dtype=np.int64)
    return np.full(env.num_agents, PRIMARY_SERVICE, dtype=np.int64)


def rollout(seed: int, reliability: float, plan: str, stage_mode: str, full_team_contract: bool) -> dict[str, Any]:
    env_class = PSCRFullTeamCommitmentEnv if full_team_contract else PSCRSearchPrefixEnv
    env = env_class(P8SearchPrefixConfig(seed=seed, forecast_reliability_choices=(reliability,)))
    env.reset()
    initial_public_context = env.public_commitment_context().tolist()
    total_return = 0.0
    timeout = collision_or_constraint = 0.0
    commitment_actions: list[int] | None = None
    while not env.done:
        action = actions_for(env, plan, stage_mode)
        if env._commitment_active() and commitment_actions is None:
            commitment_actions = action.tolist()
        _, _, _, rewards, _, info = env.step(action)
        total_return += float(rewards[0, 0])
        timeout = max(timeout, float(env.step_count >= env.config.horizon))
        collision_or_constraint = max(collision_or_constraint, float(info["collision"] or info["constraint_violation"]))
    if commitment_actions is None:
        raise RuntimeError("episode finished before the public commitment window")
    summary = env.terminal_summary()
    future_y = float(env.future_position[1])
    return {
        "episode_seed": seed,
        "reliability": reliability,
        "plan": plan,
        "public_context_at_reset": json.dumps(initial_public_context),
        "commitment_actions": json.dumps(commitment_actions),
        # These realized fields are audit records after the rollout, never plan inputs.
        "realized_forecast_sector": int(env.forecast_sector),
        "realized_future_sector": int(np.sign(future_y)),
        "realized_future_aligned": float(np.sign(future_y) == env.forecast_sector),
        "realized_future_urgent": float(env.future_urgent),
        "realized_future_x": float(env.future_position[0]),
        "return": total_return,
        "weighted_service_value": float(summary["weighted_service_value"]),
        "primary_completed": float(summary["primary_completed"]),
        "future_completed": float(summary["future_completed"]),
        "future_localized": float(summary["future_localized"]),
        "timeout": timeout,
        "collision_or_constraint": collision_or_constraint,
        "energy_used": float(summary["energy_used"]),
    }


def mean(values: list[float]) -> float:
    return float(np.mean(values)) if values else float("nan")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--episodes", type=int, default=64)
    parser.add_argument("--stage-mode", choices=("scout_relay", "full_team"), default="scout_relay")
    parser.add_argument("--full-team-contract", action="store_true", help="use the distinct P9 full-team commitment environment; required for --stage-mode full_team")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("refusing without --execute")
    if args.episodes <= 0:
        raise ValueError("episodes must be positive")
    if args.stage_mode == "full_team" and not args.full_team_contract:
        raise ValueError("full_team stage mode requires --full-team-contract; P8 preserves executor primary service by design")
    if args.output_root.exists():
        raise FileExistsError(f"refusing to overwrite {args.output_root}")

    rows: list[dict[str, Any]] = []
    paired_rows: list[dict[str, Any]] = []
    paired_exact = True
    realization_fields = (
        "public_context_at_reset", "realized_forecast_sector", "realized_future_sector",
        "realized_future_aligned", "realized_future_urgent", "realized_future_x",
    )
    for band_index, reliability in enumerate(RELIABILITIES):
        for episode_index in range(args.episodes):
            seed = 981_000 + 1_000 * band_index + episode_index
            branch = {plan: rollout(seed, reliability, plan, args.stage_mode, args.full_team_contract) for plan in PLANS}
            rows.extend(branch.values())
            maintain, stage = branch["maintain_primary"], branch["stage_forecast"]
            paired_exact = paired_exact and all(maintain[field] == stage[field] for field in realization_fields)
            paired_rows.append({
                "episode_seed": seed,
                "reliability": reliability,
                **{f"maintain_{key}": maintain[key] for key in maintain if key not in {"episode_seed", "reliability", "plan"}},
                **{f"stage_{key}": stage[key] for key in stage if key not in {"episode_seed", "reliability", "plan"}},
                "delta_stage_minus_maintain_return": float(stage["return"] - maintain["return"]),
                "delta_stage_minus_maintain_weighted_service_value": float(stage["weighted_service_value"] - maintain["weighted_service_value"]),
                "delta_stage_minus_maintain_future_completed": float(stage["future_completed"] - maintain["future_completed"]),
                "delta_stage_minus_maintain_energy_used": float(stage["energy_used"] - maintain["energy_used"]),
            })

    summaries: list[dict[str, Any]] = []
    for reliability in RELIABILITIES:
        subset = [row for row in paired_rows if row["reliability"] == reliability]
        deltas = [float(row["delta_stage_minus_maintain_weighted_service_value"]) for row in subset]
        summaries.append({
            "reliability": reliability,
            "matched_episode_pairs": len(subset),
            "mean_delta_stage_minus_maintain_weighted_service_value": mean(deltas),
            "sample_sd_delta_weighted_service_value": float(np.std(deltas, ddof=1)) if len(deltas) > 1 else 0.0,
            "stage_better_fraction": mean([float(delta > MARGIN) for delta in deltas]),
            "maintain_better_fraction": mean([float(delta < -MARGIN) for delta in deltas]),
            "tie_or_small_difference_fraction": mean([float(abs(delta) <= MARGIN) for delta in deltas]),
            "mean_delta_stage_minus_maintain_return": mean([float(row["delta_stage_minus_maintain_return"]) for row in subset]),
            "mean_delta_stage_minus_maintain_future_completed": mean([float(row["delta_stage_minus_maintain_future_completed"]) for row in subset]),
            "mean_delta_stage_minus_maintain_energy_used": mean([float(row["delta_stage_minus_maintain_energy_used"]) for row in subset]),
        })
    by_band = {float(row["reliability"]): row for row in summaries}
    checks = {
        "all_paired_branches_share_realization": paired_exact,
        "high_reliability_stage_mean_advantage": by_band[0.9]["mean_delta_stage_minus_maintain_weighted_service_value"] > MARGIN,
        "low_reliability_maintain_mean_advantage": by_band[0.1]["mean_delta_stage_minus_maintain_weighted_service_value"] < -MARGIN,
        "high_reliability_stage_direction_support": by_band[0.9]["stage_better_fraction"] >= 0.6,
        "low_reliability_maintain_direction_support": by_band[0.1]["maintain_better_fraction"] >= 0.6,
    }
    report = {
        "protocol": PROTOCOL,
        "diagnostic_only": True,
        "episodes_per_reliability": args.episodes,
        "stage_mode": args.stage_mode,
        "task_contract": "P9_full_team_commitment" if args.full_team_contract else "P8_role_preserving_commitment",
        "plans": list(PLANS),
        "checks": checks,
        "summary_by_reliability": summaries,
        "verdict": "PSCR_P8_COUNTERFACTUAL_COMMITMENT_VALUE_PASS" if all(checks.values()) else "PSCR_P8_COUNTERFACTUAL_COMMITMENT_VALUE_FAIL",
        "interpretation": "A pass means that legal public commitment plans have a paired, reliability-dependent simulator value difference under the standard P8 interface. It does not show that a learning algorithm can exploit this signal, prove a policy mechanism, or establish a paper claim.",
    }
    args.output_root.mkdir(parents=True)
    with (args.output_root / "P8_COUNTERFACTUAL_COMMITMENT_VALUE_ROWS.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    with (args.output_root / "P8_COUNTERFACTUAL_COMMITMENT_VALUE_PAIRED_DELTAS.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(paired_rows[0])); writer.writeheader(); writer.writerows(paired_rows)
    with (args.output_root / "P8_COUNTERFACTUAL_COMMITMENT_VALUE_SUMMARY.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summaries[0])); writer.writeheader(); writer.writerows(summaries)
    (args.output_root / "P8_COUNTERFACTUAL_COMMITMENT_VALUE_REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
