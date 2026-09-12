"""Zero-training value audit for reliability-conditioned PSCR commitment.

This audit tests whether the existing physical task can support an information
value claim before a new learner is introduced.  It compares transparent
pre-arrival staging policies and switches all of them to the revealed request
after arrival.  It is not a learning baseline or paper result.
"""
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


POLICIES = {
    "forecast_commit": FORECAST_STAGE,
    "contingency_commit": CONTINGENCY_STAGE,
    "defer": SAFE_HOLD,
    "primary_commit": PRIMARY_SERVICE,
}


def rollout(seed: int, reliability: float, policy: str) -> dict[str, object]:
    env = PSCRContingencyServiceEnv(PSCRConfig(
        seed=seed,
        adversary_profile="bounded_mixture",
        forecast_reliability=reliability,
        future_deadline_urgent_step=100,
    ))
    env.reset()
    pre_intent = POLICIES[policy]
    while not env.done:
        intent = FUTURE_SERVICE if env.future_active else pre_intent
        env.step(np.full(env.num_agents, intent, dtype=np.int64))
    return {"seed": seed, "reliability": reliability, "policy": policy, **env.terminal_summary()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--episodes", type=int, default=64)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("refusing without --execute")
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite {args.output}")
    rows = [
        rollout(99700 + episode, reliability, policy)
        for reliability in (0.90, 0.50)
        for policy in POLICIES
        for episode in range(args.episodes)
    ]
    summaries: dict[str, dict[str, float]] = {}
    for reliability in (0.90, 0.50):
        for policy in POLICIES:
            subset = [row for row in rows if row["reliability"] == reliability and row["policy"] == policy]
            summaries[f"r{reliability}_{policy}"] = {
                key: float(np.mean([float(row[key]) for row in subset]))
                for key in ("weighted_service_value", "primary_completed", "future_completed", "energy_used")
            }
    high_direct = summaries["r0.9_forecast_commit"]["weighted_service_value"]
    high_hub = summaries["r0.9_contingency_commit"]["weighted_service_value"]
    low_direct = summaries["r0.5_forecast_commit"]["weighted_service_value"]
    low_hub = summaries["r0.5_contingency_commit"]["weighted_service_value"]
    high_defer = summaries["r0.9_defer"]["weighted_service_value"]
    low_defer = summaries["r0.5_defer"]["weighted_service_value"]
    checks = {
        "high_reliability_forecast_preferred": high_direct > high_hub + 0.05,
        "low_reliability_contingency_preferred": low_hub > low_direct + 0.05,
        "defer_dominated_at_high_reliability": max(high_direct, high_hub) > high_defer + 0.05,
        "defer_dominated_at_low_reliability": max(low_direct, low_hub) > low_defer + 0.05,
    }
    verdict = "PSCR_RELIABILITY_COMMITMENT_VALUE_PASS" if all(checks.values()) else "PSCR_RELIABILITY_COMMITMENT_VALUE_FAIL"
    args.output.mkdir(parents=True)
    with (args.output / "PSCR_RELIABILITY_COMMITMENT_ROWS.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    payload = {
        "protocol": "PSCR-RELIABILITY-COMMITMENT-VALUE-Q0",
        "diagnostic_only": True,
        "episodes_per_condition": args.episodes,
        "summaries": summaries,
        "checks": checks,
        "verdict": verdict,
        "interpretation": "Transparent policy ordering tests decision relevance under the current frozen geometry. It does not establish learnability or any learned-method advantage.",
    }
    (args.output / "PSCR_RELIABILITY_COMMITMENT_VALUE_Q0.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
