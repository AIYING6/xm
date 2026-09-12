"""Issue the pre-registered development decision for RC-PSCR M1."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite {args.output}")

    endpoint = rows(args.root / "diagnostics/m1_endpoint/PSCR_RC_M1_PER_SEED_ENDPOINTS.csv")
    action_rows: list[dict[str, str]] = []
    for arm in ("full", "phase_control", "permuted_reliability"):
        for seed in (99901, 99902, 99903):
            for row in rows(args.root / arm / f"action_audit_seed{seed}" / "action_fractions.csv"):
                action_rows.append({"arm": arm, **row})

    # Per-seed mean over the two frozen reliability bands. Training seeds,
    # rather than episode rows, remain the decision unit.
    service: dict[tuple[str, int], float] = {}
    for arm in ("full", "phase_control", "permuted_reliability"):
        for seed in (99901, 99902, 99903):
            values = [float(row["weighted_service_value"]) for row in endpoint if row["arm"] == arm and int(row["training_seed"]) == seed]
            service[(arm, seed)] = sum(values) / len(values)
    paired_wins = {
        control: sum(service[("full", seed)] > service[(control, seed)] for seed in (99901, 99902, 99903))
        for control in ("phase_control", "permuted_reliability")
    }

    def action_mean(band: str, phase: str, intent: str) -> float:
        values = [float(row["action_fraction"]) for row in action_rows if row["arm"] == "full" and row["reliability_band"] == band and row["phase"] == phase and row["intent"] == intent]
        return sum(values) / len(values)

    high_forecast = action_mean("r0.90", "pre_arrival", "forecast_stage")
    low_forecast = action_mean("r0.25", "pre_arrival", "forecast_stage")
    low_contingency = action_mean("r0.25", "pre_arrival", "contingency_stage")
    high_contingency = action_mean("r0.90", "pre_arrival", "contingency_stage")
    post_future = (action_mean("r0.25", "post_arrival", "future_service") + action_mean("r0.90", "post_arrival", "future_service")) / 2.0

    # The M1 contract requires both a matched-control advantage and behavior
    # compatible with the reliability hypothesis. Strict inequalities avoid
    # calling indistinguishable action fractions a mechanism effect.
    control_gate = max(paired_wins.values()) >= 2
    direction_gate = high_forecast > low_forecast and low_contingency > high_contingency
    release_gate = post_future > 0.0
    verdict = "M1_MECHANISM_SIGNAL_PASS" if control_gate and direction_gate and release_gate else "M1_MECHANISM_SIGNAL_NOT_ESTABLISHED"
    report = {
        "protocol": "PSCR-RC-COMMITMENT-RELEASE-MAPPO-M1-V1",
        "verdict": verdict,
        "independent_unit": "training_seed",
        "control_wins_full_over": paired_wins,
        "mechanism_actions_full": {
            "high_reliability_pre_forecast": high_forecast,
            "low_reliability_pre_forecast": low_forecast,
            "low_reliability_pre_contingency": low_contingency,
            "high_reliability_pre_contingency": high_contingency,
            "mean_post_arrival_future_service": post_future,
        },
        "gates": {"matched_control": control_gate, "reliability_direction": direction_gate, "post_arrival_release": release_gate},
        "interpretation_boundary": "This is a development M1 decision. It does not establish formal performance or support manuscript claims.",
    }
    args.output.mkdir(parents=True)
    (args.output / "PSCR_RC_M1_DECISION.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (args.output / "PSCR_RC_M1_DECISION.md").write_text(
        "# PSCR RC M1 decision\n\n"
        f"`{verdict}`\n\n"
        f"Matched-control wins: phase-control={paired_wins['phase_control']}/3; permuted-reliability={paired_wins['permuted_reliability']}/3.\n\n"
        f"Full pre-arrival forecast: high={high_forecast:.4f}, low={low_forecast:.4f}.  "
        f"Full pre-arrival contingency: low={low_contingency:.4f}, high={high_contingency:.4f}.  "
        f"Post-arrival future-service={post_future:.4f}.\n\n"
        "This development decision uses training seeds as independent units and does not constitute a formal paper result.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
