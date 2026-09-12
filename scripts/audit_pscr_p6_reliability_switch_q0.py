"""Targeted Q0 validation for the P6 public-reliability action switch.

This audit validates one measured candidate cell only.  It treats the public
forecast reliability as a belief over generated future-request branches, not
as access to the parent episode's hidden future location or urgency.
"""
from __future__ import annotations

import argparse
import copy
import csv
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.pscr_adversarial_service_env import PSCRConfig
from envs.pscr_contingency_service_env import CONTINGENCY_STAGE, PSCRContingencyServiceEnv
from envs.pscr_service_reconfiguration_env import FORECAST_STAGE, FUTURE_SERVICE, PRIMARY_SERVICE, SAFE_HOLD


CELL = {"primary_forward": 8_500.0, "future_forward": 12_000.0, "future_lateral": 13_000.0, "arrival": 84, "commit": 60}
INTENTS = {"primary": PRIMARY_SERVICE, "forecast": FORECAST_STAGE, "contingency": CONTINGENCY_STAGE, "defer": SAFE_HOLD}
X_OFFSETS = (-1_000.0, 0.0, 1_000.0)
URGENT_PROBABILITY = 0.55
MARGIN = 0.05


def state_at_commit(seed: int, reliability: float) -> PSCRContingencyServiceEnv:
    env = PSCRContingencyServiceEnv(
        PSCRConfig(
            seed=seed,
            primary_forward_distance=CELL["primary_forward"],
            future_forward_distance=CELL["future_forward"],
            future_lateral_distance=CELL["future_lateral"],
            contingency_forward_distance=11_000.0,
            future_arrival_step=CELL["arrival"],
            future_deadline_urgent_step=CELL["arrival"] + 33,
            forecast_reliability_choices=(reliability,),
            adversary_profile="bounded_mixture",
        )
    )
    env.reset()
    while env.step_count < CELL["commit"]:
        env.step(np.full(env.num_agents, PRIMARY_SERVICE, dtype=np.int64))
    return env


def branch_value(state: PSCRContingencyServiceEnv, intent: int, sector: int, urgent: bool, x_offset: float) -> float:
    env = copy.deepcopy(state)
    env.future_position = np.asarray((CELL["future_forward"] + x_offset, sector * CELL["future_lateral"], 5_000.0), dtype=np.float32)
    env.future_urgent = urgent
    env.future_active = env.future_completed = env.future_expired = False
    env.future_hold = env._chain_steps["future"] = 0
    while not env.done:
        action = FUTURE_SERVICE if env.future_active else intent
        env.step(np.full(env.num_agents, action, dtype=np.int64))
    return float(env.terminal_summary()["weighted_service_value"])


def posterior_values(state: PSCRContingencyServiceEnv, reliability: float) -> dict[str, float]:
    values = {name: 0.0 for name in INTENTS}
    for aligned, sector_probability in ((True, reliability), (False, 1.0 - reliability)):
        sector = state.forecast_sector if aligned else -state.forecast_sector
        for urgent, urgency_probability in ((True, URGENT_PROBABILITY), (False, 1.0 - URGENT_PROBABILITY)):
            for x_offset in X_OFFSETS:
                for name, intent in INTENTS.items():
                    values[name] += sector_probability * urgency_probability / len(X_OFFSETS) * branch_value(state, intent, sector, urgent, x_offset)
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

    rows: list[dict[str, object]] = []
    means = {(reliability, name): [] for reliability in (0.9, 0.1) for name in INTENTS}
    primary_incomplete = []
    for reliability in (0.9, 0.1):
        for offset in range(args.states):
            seed = 96_000 + offset
            state = state_at_commit(seed, reliability)
            incomplete = not bool(state.primary_completed)
            primary_incomplete.append(incomplete)
            for name, value in posterior_values(state, reliability).items():
                means[(reliability, name)].append(value)
                rows.append({"seed": seed, "reliability": reliability, "intent": name, "public_posterior_value": value, "primary_incomplete_at_commit": incomplete})

    summary = {f"r{reliability}_{name}": float(np.mean(means[(reliability, name)])) for reliability in (0.9, 0.1) for name in INTENTS}
    high_forecast = summary["r0.9_forecast"] > max(summary["r0.9_primary"], summary["r0.9_contingency"], summary["r0.9_defer"]) + MARGIN
    low_contingency = summary["r0.1_contingency"] > max(summary["r0.1_primary"], summary["r0.1_forecast"], summary["r0.1_defer"]) + MARGIN
    report = {
        "protocol": "PSCR-P6-RELIABILITY-SWITCH-Q0",
        "diagnostic_only": True,
        "cell": CELL,
        "states_per_reliability": args.states,
        "all_primary_incomplete_at_commit": bool(all(primary_incomplete)),
        "high_reliability_forecast_preferred": high_forecast,
        "low_reliability_contingency_preferred": low_contingency,
        "public_action_switch_established": bool(high_forecast and low_contingency),
        "hidden_parent_future_used": False,
        "summary": summary,
        "verdict": "PSCR_P6_RELIABILITY_SWITCH_PASS" if all(primary_incomplete) and high_forecast and low_contingency else "PSCR_P6_RELIABILITY_SWITCH_FAIL",
        "interpretation": "A pass establishes a legal public-belief action switch in the frozen task cell, not learned-policy efficacy or generalization.",
    }
    args.output.mkdir(parents=True)
    with (args.output / "PSCR_P6_SWITCH_ROWS.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (args.output / "PSCR_P6_SWITCH_REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
