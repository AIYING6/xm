"""Transparent PSCR grid: quantify whether commitment timing creates information value."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.pscr_adversarial_service_env import PSCRConfig
from envs.pscr_contingency_service_env import CONTINGENCY_STAGE, PSCRContingencyServiceEnv
from envs.pscr_service_reconfiguration_env import FORECAST_STAGE, FUTURE_SERVICE, PRIMARY_SERVICE, SAFE_HOLD


INTENTS = {"forecast": FORECAST_STAGE, "contingency": CONTINGENCY_STAGE, "defer": SAFE_HOLD, "primary": PRIMARY_SERVICE}


def rollout(seed: int, reliability: float, commitment: str, commit_step: int) -> dict[str, object]:
    env = PSCRContingencyServiceEnv(PSCRConfig(seed=seed, adversary_profile="bounded_mixture", forecast_reliability=reliability, future_deadline_urgent_step=100))
    env.reset()
    while not env.done:
        if env.future_active:
            intent = FUTURE_SERVICE
        elif env.step_count < commit_step:
            intent = PRIMARY_SERVICE
        else:
            intent = INTENTS[commitment]
        env.step(np.full(env.num_agents, intent, dtype=np.int64))
    return {"seed": seed, "reliability": reliability, "commitment": commitment, "commit_step": commit_step, **env.terminal_summary()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--episodes", type=int, default=32)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("refusing without --execute")
    if args.output.exists():
        raise FileExistsError(args.output)
    arms = [("forecast", step) for step in (0, 20, 36, 48)] + [("contingency", step) for step in (0, 20, 36, 48)] + [("primary", 58), ("defer", 0)]
    rows = [rollout(99800 + episode, reliability, commitment, step) for reliability in (0.90, 0.50) for commitment, step in arms for episode in range(args.episodes)]
    summary = []
    for reliability in (0.90, 0.50):
        for commitment, step in arms:
            subset = [row for row in rows if row["reliability"] == reliability and row["commitment"] == commitment and row["commit_step"] == step]
            summary.append({"reliability": reliability, "commitment": commitment, "commit_step": step, **{metric: float(np.mean([float(row[metric]) for row in subset])) for metric in ("weighted_service_value", "primary_completed", "future_completed", "energy_used")}})
    args.output.mkdir(parents=True)
    for name, data in (("PSCR_COMMITMENT_TIMING_ROWS.csv", rows), ("PSCR_COMMITMENT_TIMING_SUMMARY.csv", summary)):
        with (args.output / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(data[0])); writer.writeheader(); writer.writerows(data)
    (args.output / "PSCR_COMMITMENT_TIMING_MANIFEST.json").write_text(json.dumps({"protocol": "PSCR-COMMITMENT-TIMING-Q0", "diagnostic_only": True, "episodes_per_condition": args.episodes, "interpretation": "Transparent timing grid only; it measures task-level decision structure, not learning or a method."}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
