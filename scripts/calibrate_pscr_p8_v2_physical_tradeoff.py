"""Select a P8-v2 physical contract before any policy training.

The calibration is intentionally small and finite: it varies only timing and
localization geometry needed to make the already-defined public commitment
decision consequential.  Every candidate uses paired, identical exogenous
branches and the standard P8 interface.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict
from itertools import product
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.pscr_search_prefix_env import P8SearchPrefixConfig, PSCRSearchPrefixEnv
from envs.pscr_service_reconfiguration_env import FORECAST_STAGE, FUTURE_SERVICE, PRIMARY_SERVICE


PROTOCOL = "PSCR-P8-V2-PHYSICAL-CALIBRATION-V1"
RELIABILITIES = (0.1, 0.9)
PLANS = ("maintain_primary", "stage_forecast")
MARGIN = 0.05


def candidate_configs() -> list[P8SearchPrefixConfig]:
    values: list[P8SearchPrefixConfig] = []
    for start, deadline, radius in product((24, 36), (104, 112), (3000.0, 4000.0)):
        arrival = 84
        values.append(P8SearchPrefixConfig(
            commitment_start_step=start,
            commitment_lock_steps=arrival - start,
            future_deadline_urgent_step=deadline,
            localization_radius=radius,
        ))
    return values


def actions_for(env: PSCRSearchPrefixEnv, plan: str) -> np.ndarray:
    if env.future_active:
        return np.full(env.num_agents, FUTURE_SERVICE, dtype=np.int64)
    if env._commitment_active() and plan == "stage_forecast":
        actions = np.full(env.num_agents, PRIMARY_SERVICE, dtype=np.int64)
        actions[env.scout] = FORECAST_STAGE
        actions[env.relay] = FORECAST_STAGE
        return actions
    return np.full(env.num_agents, PRIMARY_SERVICE, dtype=np.int64)


def rollout(config: P8SearchPrefixConfig, seed: int, reliability: float, plan: str) -> dict[str, Any]:
    cfg = P8SearchPrefixConfig(**{**asdict(config), "seed": seed, "forecast_reliability_choices": (reliability,)})
    env = PSCRSearchPrefixEnv(cfg)
    env.reset()
    total_return = 0.0
    timeout = collision_or_constraint = 0.0
    while not env.done:
        _, _, _, rewards, _, info = env.step(actions_for(env, plan))
        total_return += float(rewards[0, 0])
        timeout = max(timeout, float(env.step_count >= env.config.horizon))
        collision_or_constraint = max(collision_or_constraint, float(info["collision"] or info["constraint_violation"]))
    terminal = env.terminal_summary()
    return {
        "forecast_sector": int(env.forecast_sector),
        "future_sector": int(np.sign(float(env.future_position[1]))),
        "future_urgent": float(env.future_urgent),
        "future_x": float(env.future_position[0]),
        "weighted_service_value": float(terminal["weighted_service_value"]),
        "future_completed": float(terminal["future_completed"]),
        "future_localized": float(terminal["future_localized"]),
        "primary_completed": float(terminal["primary_completed"]),
        "return": total_return,
        "timeout": timeout,
        "collision_or_constraint": collision_or_constraint,
        "energy_used": float(terminal["energy_used"]),
    }


def summarize(candidate_id: int, cfg: P8SearchPrefixConfig, pairs_per_band: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    exact = True
    for band_index, reliability in enumerate(RELIABILITIES):
        for episode_index in range(pairs_per_band):
            seed = 982_000 + candidate_id * 10_000 + band_index * 1_000 + episode_index
            maintain = rollout(cfg, seed, reliability, "maintain_primary")
            stage = rollout(cfg, seed, reliability, "stage_forecast")
            exact = exact and all(maintain[key] == stage[key] for key in ("forecast_sector", "future_sector", "future_urgent", "future_x"))
            rows.append({
                "candidate_id": candidate_id, "episode_seed": seed, "reliability": reliability,
                "commitment_start_step": cfg.commitment_start_step,
                "future_deadline_urgent_step": cfg.future_deadline_urgent_step,
                "localization_radius": cfg.localization_radius,
                "delta_stage_minus_maintain_weighted_service_value": stage["weighted_service_value"] - maintain["weighted_service_value"],
                "delta_stage_minus_maintain_return": stage["return"] - maintain["return"],
                "delta_stage_minus_maintain_future_completed": stage["future_completed"] - maintain["future_completed"],
                "stage_future_completed": stage["future_completed"],
                "maintain_future_completed": maintain["future_completed"],
                "stage_timeout": stage["timeout"], "maintain_timeout": maintain["timeout"],
                "stage_collision_or_constraint": stage["collision_or_constraint"],
                "maintain_collision_or_constraint": maintain["collision_or_constraint"],
            })
    bands: dict[float, dict[str, float]] = {}
    for reliability in RELIABILITIES:
        subset = [row for row in rows if row["reliability"] == reliability]
        delta = [float(row["delta_stage_minus_maintain_weighted_service_value"]) for row in subset]
        bands[reliability] = {
            "mean_delta": float(np.mean(delta)),
            "stage_better_fraction": float(np.mean([value > MARGIN for value in delta])),
            "maintain_better_fraction": float(np.mean([value < -MARGIN for value in delta])),
            "stage_future_completion": float(np.mean([row["stage_future_completed"] for row in subset])),
            "maintain_future_completion": float(np.mean([row["maintain_future_completed"] for row in subset])),
        }
    high, low = bands[0.9], bands[0.1]
    checks = {
        "paired_realizations_exact": exact,
        "high_stage_mean_advantage": high["mean_delta"] > 0.15,
        "low_maintain_mean_advantage": low["mean_delta"] < -0.15,
        "high_direction_support": high["stage_better_fraction"] >= 0.4,
        "low_direction_support": low["maintain_better_fraction"] >= 0.4,
        "high_stage_noncollapse": high["stage_future_completion"] >= 0.2,
    }
    score = high["mean_delta"] - low["mean_delta"] + 0.3 * (high["stage_better_fraction"] + low["maintain_better_fraction"])
    return rows, {
        "candidate_id": candidate_id,
        "commitment_start_step": cfg.commitment_start_step,
        "future_deadline_urgent_step": cfg.future_deadline_urgent_step,
        "localization_radius": cfg.localization_radius,
        "screening_pairs_per_band": pairs_per_band,
        "high_mean_delta_stage_minus_maintain": high["mean_delta"],
        "low_mean_delta_stage_minus_maintain": low["mean_delta"],
        "high_stage_better_fraction": high["stage_better_fraction"],
        "low_maintain_better_fraction": low["maintain_better_fraction"],
        "high_stage_future_completion": high["stage_future_completion"],
        "screening_score": score,
        "passes_all_screening_checks": all(checks.values()),
        **{f"check_{key}": value for key, value in checks.items()},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--screening-pairs", type=int, default=16)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("refusing without --execute")
    if args.output_root.exists():
        raise FileExistsError(f"refusing to overwrite {args.output_root}")
    all_rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for candidate_id, cfg in enumerate(candidate_configs()):
        rows, summary = summarize(candidate_id, cfg, args.screening_pairs)
        all_rows.extend(rows); summaries.append(summary)
    ranked = sorted(summaries, key=lambda row: (bool(row["passes_all_screening_checks"]), float(row["screening_score"])), reverse=True)
    winner = ranked[0]
    report = {
        "protocol": PROTOCOL, "diagnostic_only": True, "screening_pairs_per_band": args.screening_pairs,
        "candidate_count": len(summaries), "selected_candidate": winner,
        "verdict": "PSCR_P8_V2_PHYSICAL_CONTRACT_SELECTED" if winner["passes_all_screening_checks"] else "PSCR_P8_V2_PHYSICAL_CONTRACT_NOT_SELECTED",
        "boundary": "Screening selects only a candidate task contract. A selected contract still requires a fresh 64-pair confirmation before any policy training, and does not establish a method claim.",
    }
    args.output_root.mkdir(parents=True)
    with (args.output_root / "P8_V2_PHYSICAL_CALIBRATION_PAIRED_ROWS.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(all_rows[0])); writer.writeheader(); writer.writerows(all_rows)
    with (args.output_root / "P8_V2_PHYSICAL_CALIBRATION_CANDIDATES.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summaries[0])); writer.writeheader(); writer.writerows(summaries)
    (args.output_root / "P8_V2_PHYSICAL_CALIBRATION_REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
