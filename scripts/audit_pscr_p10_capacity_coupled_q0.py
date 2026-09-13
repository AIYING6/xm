"""Paired zero-training G0 for the P10 capacity-coupled task contract."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.pscr_capacity_coupled_service_env import P10CapacityCoupledConfig, PSCRCapacityCoupledServiceEnv
from envs.pscr_service_reconfiguration_env import FORECAST_STAGE, FUTURE_SERVICE, PRIMARY_SERVICE


RELIABILITIES = (0.1, 0.9)
MARGIN = 0.10


def action(env: PSCRCapacityCoupledServiceEnv, plan: str) -> np.ndarray:
    if env.future_active:
        return np.full(env.num_agents, FUTURE_SERVICE, dtype=np.int64)
    if env._commitment_active() and plan == "stage_full_team":
        return np.full(env.num_agents, FORECAST_STAGE, dtype=np.int64)
    return np.full(env.num_agents, PRIMARY_SERVICE, dtype=np.int64)


def rollout(seed: int, reliability: float, plan: str) -> dict[str, Any]:
    env = PSCRCapacityCoupledServiceEnv(P10CapacityCoupledConfig(seed=seed, forecast_reliability_choices=(reliability,)))
    env.reset()
    total_return = 0.0
    while not env.done:
        _, _, _, rewards, _, _ = env.step(action(env, plan))
        total_return += float(rewards[0, 0])
    terminal = env.terminal_summary()
    return {
        "forecast_sector": int(env.forecast_sector), "future_sector": int(np.sign(float(env.future_position[1]))),
        "future_x": float(env.future_position[0]), "future_urgent": float(env.future_urgent),
        "return": total_return, **terminal,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--episodes", type=int, default=64)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("refusing without --execute")
    if args.output_root.exists():
        raise FileExistsError(f"refusing to overwrite {args.output_root}")
    rows: list[dict[str, Any]] = []
    pairs: list[dict[str, Any]] = []
    exact = True
    for band_index, reliability in enumerate(RELIABILITIES):
        for episode_index in range(args.episodes):
            seed = 983_000 + band_index * 1_000 + episode_index
            maintain = rollout(seed, reliability, "maintain_primary")
            stage = rollout(seed, reliability, "stage_full_team")
            exact = exact and all(maintain[key] == stage[key] for key in ("forecast_sector", "future_sector", "future_x", "future_urgent"))
            for plan, result in (("maintain_primary", maintain), ("stage_full_team", stage)):
                rows.append({"episode_seed": seed, "reliability": reliability, "plan": plan, **result})
            pairs.append({
                "episode_seed": seed, "reliability": reliability,
                "delta_stage_minus_maintain_utility": float(stage["mission_utility"] - maintain["mission_utility"]),
                "delta_stage_minus_maintain_return": float(stage["return"] - maintain["return"]),
                "delta_stage_minus_maintain_backlog_area": float(stage["primary_backlog_area"] - maintain["primary_backlog_area"]),
                "delta_stage_minus_maintain_future_completed": float(stage["future_completed"] - maintain["future_completed"]),
                "stage_future_completed": stage["future_completed"], "maintain_future_completed": maintain["future_completed"],
            })
    summary: list[dict[str, Any]] = []
    for reliability in RELIABILITIES:
        subset = [row for row in pairs if row["reliability"] == reliability]
        delta = [float(row["delta_stage_minus_maintain_utility"]) for row in subset]
        summary.append({
            "reliability": reliability, "matched_pairs": len(subset),
            "mean_delta_stage_minus_maintain_utility": float(np.mean(delta)),
            "sample_sd_delta_utility": float(np.std(delta, ddof=1)),
            "stage_better_fraction": float(np.mean([value > MARGIN for value in delta])),
            "maintain_better_fraction": float(np.mean([value < -MARGIN for value in delta])),
            "mean_delta_future_completed": float(np.mean([row["delta_stage_minus_maintain_future_completed"] for row in subset])),
            "mean_delta_backlog_area": float(np.mean([row["delta_stage_minus_maintain_backlog_area"] for row in subset])),
        })
    b = {float(row["reliability"]): row for row in summary}
    checks = {
        "paired_realizations_exact": exact,
        "high_reliability_stage_advantage": b[0.9]["mean_delta_stage_minus_maintain_utility"] > MARGIN and b[0.9]["stage_better_fraction"] >= 0.6,
        "low_reliability_maintain_advantage": b[0.1]["mean_delta_stage_minus_maintain_utility"] < -MARGIN and b[0.1]["maintain_better_fraction"] >= 0.6,
        "future_task_nonsaturated": bool(0.05 < float(np.mean([row["stage_future_completed"] for row in pairs])) < 0.95),
    }
    report = {
        "protocol": "PSCR-P10-CAPACITY-COUPLED-Q0-V1", "diagnostic_only": True, "episodes_per_band": args.episodes,
        "checks": checks, "summary_by_reliability": summary,
        "verdict": "PSCR_P10_G0_PASS" if all(checks.values()) else "PSCR_P10_G0_FAIL",
        "boundary": "A pass only establishes a paired task-level choice reversal under the frozen P10 contract. It does not train or validate C3-MAPPO.",
    }
    args.output_root.mkdir(parents=True)
    for filename, data in (("P10_Q0_ROWS.csv", rows), ("P10_Q0_PAIRED_DELTAS.csv", pairs), ("P10_Q0_SUMMARY.csv", summary)):
        with (args.output_root / filename).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(data[0])); writer.writeheader(); writer.writerows(data)
    (args.output_root / "P10_Q0_REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
