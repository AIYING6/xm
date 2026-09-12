"""Zero-training search for an identifiable reliability--commitment task cell.

Unlike the retired P4 gate, the candidate set includes continuing primary
service.  A cell is eligible only when public-posterior values make forecast
commitment strictly preferable at high reliability and primary preservation
strictly preferable at low reliability.
"""
from __future__ import annotations

import argparse
import copy
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


INTENTS = {"primary": PRIMARY_SERVICE, "forecast": FORECAST_STAGE, "contingency": CONTINGENCY_STAGE, "defer": SAFE_HOLD}
X_OFFSETS = (-1_000.0, 0.0, 1_000.0)
URGENT_PROBABILITY = 0.55


def config(seed: int, r: float, cell: tuple[float, float, int]) -> PSCRConfig:
    future_forward, lateral, arrival = cell
    return PSCRConfig(
        seed=seed,
        primary_forward_distance=4_500.0,
        future_forward_distance=future_forward,
        future_lateral_distance=lateral,
        contingency_forward_distance=11_000.0,
        future_arrival_step=arrival,
        future_deadline_urgent_step=arrival + 33,
        forecast_reliability_choices=(r,),
        adversary_profile="bounded_mixture",
    )


def state_at_commit(seed: int, r: float, cell: tuple[float, float, int]) -> PSCRContingencyServiceEnv:
    env = PSCRContingencyServiceEnv(config(seed, r, cell)); env.reset()
    commit_step = cell[2] - 18
    while env.step_count < commit_step:
        env.step(np.full(env.num_agents, PRIMARY_SERVICE, dtype=np.int64))
    return env


def utility(state: PSCRContingencyServiceEnv, intent: int, sector: int, urgent: bool, x_offset: float) -> float:
    branch = copy.deepcopy(state)
    branch.future_position = np.asarray((branch.config.future_forward_distance + x_offset, sector * branch.config.future_lateral_distance, 5_000.0), dtype=np.float32)
    branch.future_urgent = urgent; branch.future_active = False
    branch.future_completed = branch.future_expired = False; branch.future_hold = 0; branch._chain_steps["future"] = 0
    while not branch.done:
        branch.step(np.full(branch.num_agents, FUTURE_SERVICE if branch.future_active else intent, dtype=np.int64))
    return float(branch.terminal_summary()["weighted_service_value"])


def posterior(state: PSCRContingencyServiceEnv, r: float) -> dict[str, float]:
    values = {name: 0.0 for name in INTENTS}
    for aligned, p_sector in ((True, r), (False, 1.0 - r)):
        sector = state.forecast_sector if aligned else -state.forecast_sector
        for urgent, p_urgent in ((True, URGENT_PROBABILITY), (False, 1.0 - URGENT_PROBABILITY)):
            for offset in X_OFFSETS:
                weight = p_sector * p_urgent / len(X_OFFSETS)
                for name, intent in INTENTS.items(): values[name] += weight * utility(state, intent, sector, urgent, offset)
    return values


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--states", type=int, default=2)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute: raise SystemExit("refusing without --execute")
    if args.output.exists(): raise FileExistsError(args.output)
    grid = tuple(itertools.product((12_000.0, 14_000.0), (13_000.0, 16_000.0), (84, 96)))
    rows: list[dict[str, object]] = []
    summaries: list[dict[str, object]] = []
    for cell in grid:
        values: dict[tuple[float, str], list[float]] = {(r, name): [] for r in (0.90, 0.10) for name in INTENTS}
        for r in (0.90, 0.10):
            for offset in range(args.states):
                outcome = posterior(state_at_commit(93_000 + offset, r, cell), r)
                for name, value in outcome.items():
                    values[(r, name)].append(value)
                    rows.append({"future_forward": cell[0], "lateral": cell[1], "arrival": cell[2], "reliability": r, "state_seed": 93_000 + offset, "intent": name, "public_posterior_value": value})
        mean = {(r, name): float(np.mean(values[(r, name)])) for r in (0.90, 0.10) for name in INTENTS}
        record: dict[str, object] = {"future_forward": cell[0], "lateral": cell[1], "arrival": cell[2], "commit_step": cell[2] - 18}
        for r in (0.90, 0.10):
            for name in INTENTS: record[f"r{r}_{name}"] = mean[(r, name)]
        record["high_forecast_preferred"] = mean[(0.90, "forecast")] > max(mean[(0.90, "primary")], mean[(0.90, "contingency")], mean[(0.90, "defer")]) + 0.05
        record["low_primary_preferred"] = mean[(0.10, "primary")] > max(mean[(0.10, "forecast")], mean[(0.10, "contingency")], mean[(0.10, "defer")]) + 0.05
        record["gate_pass"] = bool(record["high_forecast_preferred"] and record["low_primary_preferred"])
        summaries.append(record)
    passing = [row for row in summaries if row["gate_pass"]]
    args.output.mkdir(parents=True)
    for name, data in (("PSCR_P5_PUBLIC_POSTERIOR_ROWS.csv", rows), ("PSCR_P5_PUBLIC_POSTERIOR_SUMMARY.csv", summaries)):
        with (args.output / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(data[0])); writer.writeheader(); writer.writerows(data)
    report = {"protocol": "PSCR-P5-RELIABILITY-PRIMARY-GRID-Q0", "diagnostic_only": True, "states_per_reliability": args.states, "grid_cells": len(grid), "passing_cells": passing, "verdict": "PSCR_P5_IDENTIFIABILITY_PASS" if passing else "PSCR_P5_IDENTIFIABILITY_FAIL", "interpretation": "Pass establishes public-posterior decision relevance only; it does not establish learning or method efficacy."}
    (args.output / "PSCR_P5_PUBLIC_POSTERIOR_REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__": main()
