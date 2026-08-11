"""Apply the frozen M2R two-seed decision rule to isolated cloud outputs."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

SEEDS = (9601, 9602)


def load_rows(root: Path) -> list[dict]:
    rows = []
    for method in ("full", "b1"):
        for seed in SEEDS:
            path = root / f"{method}_seed{seed}" / "summary.csv"
            with path.open(newline="", encoding="utf-8") as handle:
                rows.extend(csv.DictReader(handle))
    numeric = {
        "training_seed": int,
        "episodes": int,
        "evidence_episodes": int,
        "acquisition_given_evidence": float,
        "evidence_to_range_latency": float,
        "no_attack_range_acquisition_fraction": float,
        "neutralization_rate": float,
        "rmtn180": float,
        "evidence_turn_std": float,
        "evidence_climb_std": float,
        "evidence_commit_rate": float,
        "residual_abs_mean": float,
        "residual_bound_hit_fraction": float,
    }
    return [{key: numeric[key](value) if key in numeric else value for key, value in row.items()} for row in rows]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    rows = load_rows(args.root)
    by_key = {(row["method"], row["training_seed"]): row for row in rows}
    mechanism, action_health = {}, {}
    for seed in SEEDS:
        full, b1 = by_key[("full", seed)], by_key[("b1", seed)]
        mechanism[str(seed)] = (
            full["acquisition_given_evidence"] > b1["acquisition_given_evidence"]
            and full["evidence_to_range_latency"] < b1["evidence_to_range_latency"]
            and full["no_attack_range_acquisition_fraction"] < b1["no_attack_range_acquisition_fraction"]
        )
        # Prewritten engineering screen: nonconstant guidance, a nonzero but
        # unsaturated residual, and no all-zero/all-one commit collapse.
        action_health[str(seed)] = (
            full["evidence_turn_std"] > 0.01
            and full["evidence_climb_std"] > 0.01
            and full["residual_abs_mean"] > 1e-4
            and full["residual_bound_hit_fraction"] < 0.9
            and 0.02 < full["evidence_commit_rate"] < 0.98
        )
    mission = any(
        by_key[("full", seed)]["neutralization_rate"] > by_key[("b1", seed)]["neutralization_rate"]
        or by_key[("full", seed)]["rmtn180"] < by_key[("b1", seed)]["rmtn180"]
        for seed in SEEDS
    )
    if all(mechanism.values()) and all(action_health.values()) and mission:
        verdict = "M2R_PILOT_PASS__RESIDUAL_ACQUISITION_MECHANISM_SUPPORTED"
    elif any(mechanism.values()) or any(action_health.values()):
        verdict = "M2R_PILOT_PARTIAL__SIGNAL_STILL_UNSTABLE"
    else:
        verdict = "M2R_PILOT_NO_GO__ACQUISITION_RESIDUAL_MECHANISM_NOT_SUPPORTED"
    payload = {
        "verdict": verdict,
        "mechanism_improvement_by_seed": mechanism,
        "full_action_health_by_seed": action_health,
        "summary": rows,
        "performance_use_prohibited": True,
    }
    (args.root / "PILOT_VERDICT.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
