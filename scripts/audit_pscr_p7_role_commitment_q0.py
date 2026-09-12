"""Zero-training identifiability audit for PSCR P7 role commitments."""
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
from envs.pscr_contingency_service_env import CONTINGENCY_STAGE
from envs.pscr_role_commitment_env import PSCRRoleCommitmentEnv
from envs.pscr_service_reconfiguration_env import FORECAST_STAGE, FUTURE_SERVICE, PRIMARY_SERVICE, SAFE_HOLD


TEMPLATES = {"maintain": PRIMARY_SERVICE, "reserve_forecast": FORECAST_STAGE, "reserve_contingency": CONTINGENCY_STAGE, "wait": SAFE_HOLD}
X_OFFSETS = (-1_000.0, 0.0, 1_000.0)
URGENT_PROBABILITY = 0.55
MARGIN = 0.05


def make_state(seed: int, reliability: float, cell: tuple[float, float, int, int]) -> PSCRRoleCommitmentEnv:
    primary, future, arrival, lock_steps = cell
    config = PSCRConfig(
        seed=seed,
        primary_forward_distance=primary,
        future_forward_distance=future,
        future_lateral_distance=13_000.0,
        contingency_forward_distance=11_000.0,
        future_arrival_step=arrival,
        future_deadline_urgent_step=arrival + 33,
        forecast_reliability_choices=(reliability,),
        commitment_start_step=arrival - 24,
        commitment_lock_steps=lock_steps,
        adversary_profile="bounded_mixture",
    )
    env = PSCRRoleCommitmentEnv(config)
    env.reset()
    while env.step_count < config.commitment_start_step:
        env.step(np.full(env.num_agents, PRIMARY_SERVICE, dtype=np.int64))
    return env


def branch_value(state: PSCRRoleCommitmentEnv, template: int, sector: int, urgent: bool, x_offset: float) -> float:
    env = copy.deepcopy(state)
    env.future_position = np.asarray((env.config.future_forward_distance + x_offset, sector * env.config.future_lateral_distance, 5_000.0), dtype=np.float32)
    env.future_urgent = urgent
    env.future_active = env.future_completed = env.future_expired = False
    env.future_hold = env._chain_steps["future"] = 0
    while not env.done:
        if env._commitment_active():
            action = template
        elif env.future_active:
            action = FUTURE_SERVICE
        else:
            action = PRIMARY_SERVICE
        env.step(np.full(env.num_agents, action, dtype=np.int64))
    return float(env.terminal_summary()["weighted_service_value"])


def posterior_values(state: PSCRRoleCommitmentEnv, reliability: float) -> dict[str, float]:
    values = {name: 0.0 for name in TEMPLATES}
    for aligned, sector_probability in ((True, reliability), (False, 1.0 - reliability)):
        sector = state.forecast_sector if aligned else -state.forecast_sector
        for urgent, urgency_probability in ((True, URGENT_PROBABILITY), (False, 1.0 - URGENT_PROBABILITY)):
            for x_offset in X_OFFSETS:
                for name, template in TEMPLATES.items():
                    values[name] += sector_probability * urgency_probability / len(X_OFFSETS) * branch_value(state, template, sector, urgent, x_offset)
    return values


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--states", type=int, default=4)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("refusing without --execute")
    if args.output.exists():
        raise FileExistsError(args.output)

    grid = tuple(itertools.product((8_500.0, 10_000.0), (12_000.0, 14_000.0), (84,), (18, 24)))
    rows: list[dict[str, object]] = []
    summary: list[dict[str, object]] = []
    for cell in grid:
        samples = {(r, name): [] for r in (0.9, 0.1) for name in TEMPLATES}
        incomplete: list[bool] = []
        directional = {(r, "reserve"): 0 for r in (0.9, 0.1)}
        for reliability in (0.9, 0.1):
            for offset in range(args.states):
                state = make_state(97_000 + offset, reliability, cell)
                incomplete.append(not bool(state.primary_completed))
                values = posterior_values(state, reliability)
                high_reserve = values["reserve_forecast"] > max(values["maintain"], values["reserve_contingency"], values["wait"]) + MARGIN
                low_avoid = max(values["maintain"], values["reserve_contingency"], values["wait"]) > values["reserve_forecast"] + MARGIN
                directional[(reliability, "reserve")] += int(high_reserve if reliability == 0.9 else low_avoid)
                for name, value in values.items():
                    samples[(reliability, name)].append(value)
                    rows.append({"primary_forward": cell[0], "future_forward": cell[1], "arrival": cell[2], "lock_steps": cell[3], "seed": 97_000 + offset, "reliability": reliability, "template": name, "public_posterior_value": value, "primary_incomplete_at_commit": not bool(state.primary_completed), "high_reserve": high_reserve, "low_avoid_reserve": low_avoid})
        means = {(r, name): float(np.mean(samples[(r, name)])) for r in (0.9, 0.1) for name in TEMPLATES}
        rec: dict[str, object] = {"primary_forward": cell[0], "future_forward": cell[1], "arrival": cell[2], "commit_step": cell[2] - 24, "lock_steps": cell[3], "all_primary_incomplete": bool(all(incomplete)), "high_reserve_state_support": directional[(0.9, "reserve")], "low_avoid_state_support": directional[(0.1, "reserve")]}
        rec.update({f"r{r}_{name}": value for (r, name), value in means.items()})
        rec["high_reserve_preferred"] = means[(0.9, "reserve_forecast")] > max(means[(0.9, "maintain")], means[(0.9, "reserve_contingency")], means[(0.9, "wait")]) + MARGIN
        rec["low_avoid_reserve"] = max(means[(0.1, "maintain")], means[(0.1, "reserve_contingency")], means[(0.1, "wait")]) > means[(0.1, "reserve_forecast")] + MARGIN
        rec["gate_pass"] = bool(rec["all_primary_incomplete"] and rec["high_reserve_preferred"] and rec["low_avoid_reserve"] and rec["high_reserve_state_support"] >= 3 and rec["low_avoid_state_support"] >= 3)
        summary.append(rec)

    args.output.mkdir(parents=True)
    for name, data in (("PSCR_P7_ROWS.csv", rows), ("PSCR_P7_SUMMARY.csv", summary)):
        with (args.output / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(data[0]))
            writer.writeheader()
            writer.writerows(data)
    passing = [record for record in summary if record["gate_pass"]]
    report = {"protocol": "PSCR-P7-ROLE-COMMITMENT-Q0", "diagnostic_only": True, "grid_cells": len(grid), "states_per_reliability": args.states, "passing_cells": passing, "verdict": "PSCR_P7_IDENTIFIABILITY_PASS" if passing else "PSCR_P7_IDENTIFIABILITY_FAIL", "interpretation": "Pass establishes a public-belief-dependent role-commitment trade-off under fixed physical dynamics. It is not a learned-policy result."}
    (args.output / "PSCR_P7_REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
