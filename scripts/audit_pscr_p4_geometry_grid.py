"""Pre-registered transparent geometry gate for PSCR P4.

The grid asks a necessary physical question before any P4 learner is written:
does forecast reliability change the best pre-arrival commitment?  A passing
cell must make high-reliability forecast staging preferable, low-reliability
contingency staging preferable, and deferral inferior under the same dynamics.
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.pscr_adversarial_service_env import PSCRConfig
from envs.pscr_contingency_service_env import CONTINGENCY_STAGE, PSCRContingencyServiceEnv
from envs.pscr_service_reconfiguration_env import FORECAST_STAGE, FUTURE_SERVICE, PRIMARY_SERVICE, SAFE_HOLD


INTENT = {"forecast": FORECAST_STAGE, "contingency": CONTINGENCY_STAGE, "defer": SAFE_HOLD}
GRID = tuple(itertools.product((4_500.0, 6_000.0), (13_000.0, 16_000.0), (72, 84), (105, 117)))


def rollout(seed: int, reliability: float, policy: str, primary_x: float, lateral: float, arrival: int, deadline: int) -> dict[str, object]:
    env = PSCRContingencyServiceEnv(PSCRConfig(
        seed=seed, adversary_profile="bounded_mixture", forecast_reliability=reliability,
        primary_forward_distance=primary_x, future_lateral_distance=lateral,
        future_forward_distance=12_000.0, contingency_forward_distance=11_000.0,
        future_arrival_step=arrival, future_deadline_urgent_step=deadline,
    ))
    env.reset()
    # A common commitment deadline preserves initial primary service while
    # retaining a nonzero time cost for pre-positioning.
    commit_step = arrival - 18
    while not env.done:
        if env.future_active:
            intent = FUTURE_SERVICE
        elif env.step_count < commit_step:
            intent = PRIMARY_SERVICE
        else:
            intent = INTENT[policy]
        env.step(np.full(env.num_agents, intent, dtype=np.int64))
    return {"seed": seed, "reliability": reliability, "policy": policy, "primary_x": primary_x, "lateral": lateral, "arrival": arrival, "urgent_deadline": deadline, "commit_step": commit_step, **env.terminal_summary()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--episodes", type=int, default=16)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("refusing without --execute")
    if args.output.exists():
        raise FileExistsError(args.output)
    rows = [
        rollout(99900 + episode, reliability, policy, *cell)
        for cell in GRID for reliability in (0.90, 0.25) for policy in ("forecast", "contingency", "defer") for episode in range(args.episodes)
    ]
    summary: list[dict[str, object]] = []
    for cell in GRID:
        cell_rows = [row for row in rows if tuple(row[key] for key in ("primary_x", "lateral", "arrival", "urgent_deadline")) == cell]
        values: dict[tuple[float, str], float] = {}
        record: dict[str, object] = {"primary_x": cell[0], "lateral": cell[1], "arrival": cell[2], "urgent_deadline": cell[3], "commit_step": cell[2] - 18}
        for reliability in (0.90, 0.25):
            for policy in ("forecast", "contingency", "defer"):
                subset = [row for row in cell_rows if row["reliability"] == reliability and row["policy"] == policy]
                values[(reliability, policy)] = float(np.mean([float(row["weighted_service_value"]) for row in subset]))
                record[f"r{reliability}_{policy}_service"] = values[(reliability, policy)]
                record[f"r{reliability}_{policy}_primary"] = float(np.mean([float(row["primary_completed"]) for row in subset]))
                record[f"r{reliability}_{policy}_future"] = float(np.mean([float(row["future_completed"]) for row in subset]))
        record["high_forecast_better"] = values[(0.90, "forecast")] > values[(0.90, "contingency")] + 0.05
        record["low_contingency_better"] = values[(0.25, "contingency")] > values[(0.25, "forecast")] + 0.05
        record["high_defer_dominated"] = min(values[(0.90, "forecast")], values[(0.90, "contingency")]) > values[(0.90, "defer")] + 0.05
        record["low_defer_dominated"] = min(values[(0.25, "forecast")], values[(0.25, "contingency")]) > values[(0.25, "defer")] + 0.05
        record["gate_pass"] = all(record[key] for key in ("high_forecast_better", "low_contingency_better", "high_defer_dominated", "low_defer_dominated"))
        summary.append(record)
    passing = [row for row in summary if bool(row["gate_pass"])]
    args.output.mkdir(parents=True)
    for name, data in (("PSCR_P4_GEOMETRY_GRID_ROWS.csv", rows), ("PSCR_P4_GEOMETRY_GRID_SUMMARY.csv", summary)):
        with (args.output / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(data[0])); writer.writeheader(); writer.writerows(data)
    manifest = {"protocol": "PSCR-P4-GEOMETRY-IDENTIFIABILITY-Q0", "diagnostic_only": True, "episodes_per_condition": args.episodes, "grid_cells": len(GRID), "passing_cells": passing, "verdict": "PSCR_P4_GEOMETRY_GATE_PASS" if passing else "PSCR_P4_GEOMETRY_GATE_FAIL", "interpretation": "A pass establishes a transparent physical ranking only; it does not establish learning or a method advantage."}
    (args.output / "PSCR_P4_GEOMETRY_GRID_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
