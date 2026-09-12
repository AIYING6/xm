"""Zero-training audit of public-posterior counterfactual commitment labels.

At the public commitment time, this tool branches the *same physical state*
over all outcomes allowed by the frozen public request generator.  It then
weights branch utilities by the disclosed reliability, rather than reading the
hidden outcome sampled in the parent episode.  The result is a training-only
label candidate, not a policy evaluation or a paper result.
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
from envs.pscr_contingency_service_env import CONTINGENCY_STAGE, PSCRContingencyServiceEnv
from envs.pscr_service_reconfiguration_env import FORECAST_STAGE, FUTURE_SERVICE, PRIMARY_SERVICE, SAFE_HOLD
from scripts.run_pscr_p4_reliability_endpoint import p4_config


INTENTS = {"primary": PRIMARY_SERVICE, "forecast": FORECAST_STAGE, "contingency": CONTINGENCY_STAGE, "defer": SAFE_HOLD}
URGENT_PROBABILITY = 0.55
COMMIT_STEP = 66
# Deterministic quadrature for the frozen public generator's ±1 km longitudinal
# future-location uncertainty.  These are not sampled parent truths.
FUTURE_X_OFFSETS = (-1_000.0, 0.0, 1_000.0)


def reach_public_commit_state(seed: int, reliability: float) -> PSCRContingencyServiceEnv:
    env = PSCRContingencyServiceEnv(p4_config(seed, reliability))
    env.reset()
    while env.step_count < COMMIT_STEP:
        env.step(np.full(env.num_agents, PRIMARY_SERVICE, dtype=np.int64))
    assert not env.future_active
    return env


def set_public_branch(env: PSCRContingencyServiceEnv, *, sector: int, urgent: bool, x_offset: float) -> None:
    """Set a hypothetical future drawn from the public generator, not parent truth."""
    env.future_position = np.asarray((env.config.future_forward_distance + x_offset, sector * env.config.future_lateral_distance, 5_000.0), dtype=np.float32)
    env.future_urgent = urgent
    env.future_active = False
    env.future_completed = False
    env.future_expired = False
    env.future_hold = 0
    env._chain_steps["future"] = 0


def branch_value(state: PSCRContingencyServiceEnv, intent: int, *, sector: int, urgent: bool, x_offset: float) -> float:
    branch = copy.deepcopy(state)
    set_public_branch(branch, sector=sector, urgent=urgent, x_offset=x_offset)
    while not branch.done:
        action = FUTURE_SERVICE if branch.future_active else intent
        branch.step(np.full(branch.num_agents, action, dtype=np.int64))
    return float(branch.terminal_summary()["weighted_service_value"])


def posterior_values(state: PSCRContingencyServiceEnv, reliability: float) -> dict[str, float]:
    values = {name: 0.0 for name in INTENTS}
    for aligned, sector_probability in ((True, reliability), (False, 1.0 - reliability)):
        sector = state.forecast_sector if aligned else -state.forecast_sector
        for urgent, urgency_probability in ((True, URGENT_PROBABILITY), (False, 1.0 - URGENT_PROBABILITY)):
            for x_offset in FUTURE_X_OFFSETS:
                weight = sector_probability * urgency_probability / len(FUTURE_X_OFFSETS)
                for name, intent in INTENTS.items():
                    values[name] += weight * branch_value(state, intent, sector=sector, urgent=urgent, x_offset=x_offset)
    return values


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--states", type=int, default=8)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("refusing without --execute")
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite {args.output}")
    rows: list[dict[str, object]] = []
    invariance = []
    for reliability in (0.90, 0.25):
        for offset in range(args.states):
            state = reach_public_commit_state(91_000 + offset, reliability)
            values = posterior_values(state, reliability)
            for intent, value in values.items():
                rows.append({"state_seed": 91_000 + offset, "reliability": reliability, "intent": intent, "public_posterior_value": value})
            altered = copy.deepcopy(state)
            # This changes parent hidden fields to an impossible-looking value.
            # ``posterior_values`` must remain identical because it overwrites
            # all branch futures from public probabilities.
            altered.future_position = np.asarray((-90_000.0, 90_000.0, 0.0), dtype=np.float32)
            altered.future_urgent = not state.future_urgent
            invariance.append(values == posterior_values(altered, reliability))
    summary: dict[float, dict[str, float]] = {}
    for reliability in (0.90, 0.25):
        summary[reliability] = {intent: float(np.mean([float(row["public_posterior_value"]) for row in rows if row["reliability"] == reliability and row["intent"] == intent])) for intent in INTENTS}
    checks = {
        "high_reliability_forecast_preferred": summary[0.90]["forecast"] > summary[0.90]["contingency"],
        "low_reliability_contingency_preferred": summary[0.25]["contingency"] > summary[0.25]["forecast"],
        "hidden_parent_truth_invariant": all(invariance),
    }
    verdict = "PSCR_P4_PUBLIC_COUNTERFACTUAL_LABEL_PASS" if all(checks.values()) else "PSCR_P4_PUBLIC_COUNTERFACTUAL_LABEL_FAIL"
    args.output.mkdir(parents=True)
    with (args.output / "PSCR_P4_PUBLIC_COUNTERFACTUAL_ROWS.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    report = {"protocol": "PSCR-P4-PUBLIC-COUNTERFACTUAL-Q1-V1", "diagnostic_only": True, "commit_step": COMMIT_STEP, "states_per_reliability": args.states, "public_outcome_model": {"aligned_probability": "r", "opposite_probability": "1-r", "urgent_probability": URGENT_PROBABILITY, "future_x_quadrature_offsets": FUTURE_X_OFFSETS}, "summary": summary, "checks": checks, "verdict": verdict, "interpretation_boundary": "This validates public-posterior label structure only. It does not train or establish an algorithm advantage."}
    (args.output / "PSCR_P4_PUBLIC_COUNTERFACTUAL_REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
