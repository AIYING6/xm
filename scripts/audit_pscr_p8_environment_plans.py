"""Verify that P8's Q0 direction survives the actual training interface.

The scripted policies only use legal macro intents.  They never inspect a
future branch, future position, or urgency before the request activates.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.pscr_search_prefix_env import P8SearchPrefixConfig, PSCRSearchPrefixEnv
from envs.pscr_service_reconfiguration_env import FORECAST_STAGE, FUTURE_SERVICE, PRIMARY_SERVICE


def run_episode(seed: int, reliability: float, plan: str, urgent_deadline: int) -> dict[str, float | int]:
    env = PSCRSearchPrefixEnv(P8SearchPrefixConfig(seed=seed, forecast_reliability_choices=(reliability,), future_deadline_urgent_step=urgent_deadline))
    env.reset()
    while not env.done:
        if env.future_active:
            intent = FUTURE_SERVICE
        elif env._commitment_active() and plan == "stage":
            intent = FORECAST_STAGE
        else:
            intent = PRIMARY_SERVICE
        env.step(np.full(env.num_agents, intent, dtype=np.int64))
    result = env.terminal_summary()
    return {
        "weighted_service_value": float(result["weighted_service_value"]),
        "primary_completed": float(result["primary_completed"]),
        "future_completed": float(result["future_completed"]),
        "future_localized": float(result["future_localized"]),
        "future_localization_step": int(result["future_localization_step"]),
        "timeout": float(env.step_count >= env.config.horizon),
        "collision_or_constraint": float(env.base._has_collision() or env.base._has_constraint_violation()),
        "energy_used": float(result["energy_used"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--episodes", type=int, default=64)
    parser.add_argument("--urgent-deadline", type=int, default=120)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("refusing without --execute")
    if args.output.exists():
        raise FileExistsError(args.output)
    rows: list[dict[str, object]] = []
    for reliability in (0.9, 0.1):
        for plan in ("maintain", "stage"):
            for episode in range(args.episodes):
                row = {"reliability": reliability, "plan": plan, "episode_seed": 99_000 + episode, "urgent_deadline": args.urgent_deadline}
                row.update(run_episode(99_000 + episode, reliability, plan, args.urgent_deadline))
                rows.append(row)
    means: dict[tuple[float, str], float] = {}
    for reliability in (0.9, 0.1):
        for plan in ("maintain", "stage"):
            values = [float(r["weighted_service_value"]) for r in rows if r["reliability"] == reliability and r["plan"] == plan]
            means[(reliability, plan)] = float(np.mean(values))
    report = {
        "protocol": "PSCR-P8-ENVIRONMENT-PLAN-AUDIT-V1",
        "diagnostic_only": True,
        "episodes_per_condition": args.episodes,
        "urgent_deadline": args.urgent_deadline,
        "means": {f"r{r}_{p}": value for (r, p), value in means.items()},
        "high_reliability_stage_preferred": means[(0.9, "stage")] > means[(0.9, "maintain")] + 0.05,
        "low_reliability_maintain_preferred": means[(0.1, "maintain")] > means[(0.1, "stage")] + 0.05,
        "verdict": "PSCR_P8_INTERFACE_DIRECTION_PASS" if means[(0.9, "stage")] > means[(0.9, "maintain")] + 0.05 and means[(0.1, "maintain")] > means[(0.1, "stage")] + 0.05 else "PSCR_P8_INTERFACE_DIRECTION_FAIL",
        "boundary": "This is a scripted-plan interface audit, not policy learning or method evidence.",
    }
    args.output.mkdir(parents=True)
    with (args.output / "PSCR_P8_INTERFACE_PLAN_ROWS.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (args.output / "PSCR_P8_INTERFACE_PLAN_REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
