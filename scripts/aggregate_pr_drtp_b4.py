"""Apply the frozen PR-DRTP B4 population-level feasibility gate."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
from pr_drtp_b4_common import (  # noqa: E402
    ARMS, ENDPOINTS, FAILURE_CONDITIONS, OUTCOME_CONDITIONS, PROTOCOL,
    catastrophic, dispersion, endpoint_cell, mean, sha256,
)


FREEZE = ROOT / "configs" / "pr_drtp_b4_feasibility_freeze.json"
SELECTOR_TAPE = ROOT / "configs" / "pr_drtp_b4_selector_tape.json"
OUTCOME_TAPE = ROOT / "configs" / "pr_drtp_b4_outcome_tape.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("--execute required")
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    epsilon = float(freeze["epsilon_J"])
    selector_tape = json.loads(SELECTOR_TAPE.read_text(encoding="utf-8"))
    outcome_tape = json.loads(OUTCOME_TAPE.read_text(encoding="utf-8"))
    selection_path = args.output_root / "selector" / "SELECTION_DECISIONS.json"
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    evaluation_manifest = json.loads(
        (args.output_root / "EVALUATION_MANIFEST.json").read_text(encoding="utf-8")
    )
    asset_manifest = json.loads(
        (args.asset_root / "ASSET_MANIFEST.json").read_text(encoding="utf-8")
    )
    selector_rows = list(csv.DictReader(
        (args.output_root / "selector" / "condition_summary.csv").open(
            newline="", encoding="utf-8"
        )
    ))
    outcome_rows = list(csv.DictReader(
        (args.output_root / "outcome" / "condition_summary.csv").open(
            newline="", encoding="utf-8"
        )
    ))
    seeds = sorted(int(row["seed"]) for row in freeze["checkpoints"])
    selector_conditions = {row["name"] for row in selector_tape["conditions"]}
    outcome_conditions = {row["name"] for row in outcome_tape["conditions"]}
    integrity = (
        selection.get("protocol") == PROTOCOL
        and selection.get("outcome_tape_loaded_during_selection") is False
        and evaluation_manifest.get("protocol") == PROTOCOL
        and evaluation_manifest.get("status") == "evaluation_complete"
        and evaluation_manifest.get("training_started") is False
        and evaluation_manifest.get("selector_rows") == 15 * 7 * 50
        and evaluation_manifest.get("outcome_rows") == 30 * 5 * 100
        and evaluation_manifest.get("selector_tape_sha256") == sha256(SELECTOR_TAPE)
        and evaluation_manifest.get("outcome_tape_sha256") == sha256(OUTCOME_TAPE)
        and asset_manifest.get("checkpoint_count") == 30
        and len(selector_rows) == 15 * 7
        and len(outcome_rows) == 30 * 5
        and not (set(selector_tape["episode_ids"]) & set(outcome_tape["episode_ids"]))
    )
    selector_index: dict[int, set[str]] = {}
    for row in selector_rows:
        selector_index.setdefault(int(row["train_seed"]), set()).add(row["condition"])
    integrity &= all(selector_index.get(seed) == selector_conditions for seed in seeds)
    outcome_index: dict[tuple[str, int], dict[str, dict]] = {}
    for row in outcome_rows:
        outcome_index.setdefault((row["method"], int(row["train_seed"])), {})[
            row["condition"]
        ] = row
    integrity &= all(
        set(outcome_index.get((arm, seed), {})) == outcome_conditions
        for arm in ARMS for seed in seeds
    )
    metrics = {
        arm: {seed: endpoint_cell(outcome_index[arm, seed]) for seed in seeds}
        for arm in ARMS
    }
    decisions = {row["population"]: row for row in selection["decisions"]}
    population_rows = []
    selected_condition_safety = []
    for population in freeze["populations"]:
        name = population["population"]
        decision = decisions.get(name)
        if decision is None or decision.get("members") != population["members"]:
            integrity = False
            continue
        baseline_seed = int(population["baseline_seed"])
        selected_seed = int(decision["selected_seed"])
        if selected_seed not in population["members"]:
            integrity = False
            continue
        baseline, baseline_utr = metrics["drtp_sg"][baseline_seed], metrics["utr_sg"][baseline_seed]
        selected, selected_utr = metrics["drtp_sg"][selected_seed], metrics["utr_sg"][selected_seed]
        baseline_gain = baseline["J_pert_mean"] - baseline_utr["J_pert_mean"]
        selected_gain = selected["J_pert_mean"] - selected_utr["J_pert_mean"]
        condition_safety = []
        for condition in FAILURE_CONDITIONS:
            candidate = outcome_index["drtp_sg", selected_seed][condition]
            reference = outcome_index["utr_sg", selected_seed][condition]
            row = {
                "population": name,
                "selected_seed": selected_seed,
                "condition": condition,
                "collision_delta": float(candidate["collision"]) - float(reference["collision"]),
                "timeout_delta": float(candidate["timeout"]) - float(reference["timeout"]),
                "constraint_violation": float(candidate["constraint_violation"]),
            }
            condition_safety.append(row)
            selected_condition_safety.append(row)
        population_rows.append({
            "population": name,
            "members": population["members"],
            "baseline_seed": baseline_seed,
            "selected_seed": selected_seed,
            "baseline_gain": baseline_gain,
            "selected_gain": selected_gain,
            "selected_minus_baseline": selected["J_pert_mean"] - baseline["J_pert_mean"],
            "baseline_catastrophic": catastrophic(baseline, baseline_utr, epsilon),
            "selected_catastrophic": catastrophic(selected, selected_utr, epsilon),
            "baseline": baseline,
            "selected": selected,
            "condition_safety": condition_safety,
        })
    if len(population_rows) != 5:
        integrity = False
    baseline_gains = [row["baseline_gain"] for row in population_rows]
    selected_gains = [row["selected_gain"] for row in population_rows]
    baseline_dispersion = dispersion(baseline_gains)
    selected_dispersion = dispersion(selected_gains)
    endpoint_retention = {
        endpoint: mean(row["selected"][endpoint] for row in population_rows)
        >= mean(row["baseline"][endpoint] for row in population_rows) - epsilon
        for endpoint in ENDPOINTS
    }
    upper = [row for row in population_rows if row["baseline_gain"] > epsilon]
    upper_assessable = len(upper) >= 2
    upper_retention = upper_assessable and all(
        row["selected"]["J_pert_mean"] - row["baseline"]["J_pert_mean"] >= -epsilon
        for row in upper
    )
    pooled_collision = mean(
        row["selected"]["collision"]
        - metrics["utr_sg"][row["selected_seed"]]["collision"]
        for row in population_rows
    )
    pooled_timeout = mean(
        row["selected"]["timeout"]
        - metrics["utr_sg"][row["selected_seed"]]["timeout"]
        for row in population_rows
    )
    safety = (
        pooled_collision <= 0.05
        and pooled_timeout <= 0.05
        and all(
            row["collision_delta"] <= 0.10
            and row["timeout_delta"] <= 0.10
            and row["constraint_violation"] == 0.0
            for row in selected_condition_safety
        )
    )
    criteria = {
        "advantage_retention_all_endpoints": all(endpoint_retention.values()),
        "downside_protection": (
            min(selected_gains) - min(baseline_gains) > epsilon
            and sum(row["selected_catastrophic"] for row in population_rows) == 0
            and sum(row["selected_catastrophic"] for row in population_rows)
            <= sum(row["baseline_catastrophic"] for row in population_rows)
        ),
        "seed_reliability_range_sd": (
            selected_dispersion["range"] < baseline_dispersion["range"]
            and selected_dispersion["sample_sd"] < baseline_dispersion["sample_sd"]
        ),
        "direction_consistency": sum(gain >= 0 for gain in selected_gains) >= 4,
        "upper_tail_assessable": upper_assessable,
        "upper_tail_retention": upper_retention,
        "safety": safety,
        "integrity": bool(integrity),
    }
    if not integrity:
        decision = "PR_FEASIBILITY_TECHNICAL_INVALID"
    elif all(criteria.values()):
        decision = "PR_FEASIBILITY_GO"
    else:
        decision = "PR_FEASIBILITY_NO_GO"
    result = {
        "protocol": freeze["protocol"],
        "decision": decision,
        "exploratory_only": True,
        "independent_unit": "population",
        "population_n": 5,
        "evaluation_episodes_are_technical_repetitions": True,
        "epsilon_J": epsilon,
        "criteria": criteria,
        "endpoint_retention": endpoint_retention,
        "population_results": population_rows,
        "baseline_dispersion": baseline_dispersion,
        "selected_dispersion": selected_dispersion,
        "baseline_upper_tail_population_count": len(upper),
        "pooled_safety": {"collision_delta": pooled_collision, "timeout_delta": pooled_timeout},
        "resource_accounting": {
            "original_drtp_training_trajectories_represented": 15,
            "population_training_multiplier_vs_single_start": 3,
            "original_drtp_training_environment_steps_represented": 15 * 499968,
            "paired_utr_control_training_environment_steps_represented": 15 * 499968,
            "selector_evaluation_episodes": 15 * 7 * 50,
            "outcome_evaluation_episodes": 30 * 5 * 100,
            "new_training_environment_steps": 0,
        },
        "automatic_training_or_continuation_started": False,
        "go_authorizes": freeze["go_authorizes"],
    }
    report_dir = args.output_root / "diagnostics" / "pr_b4_feasibility"
    report_dir.mkdir(parents=True, exist_ok=False)
    (report_dir / "PR_DRTP_B4_FEASIBILITY_DECISION.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    with (report_dir / "PR_DRTP_B4_POPULATION_RESULTS.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        fields = [
            "population", "members", "baseline_seed", "selected_seed", "baseline_gain",
            "selected_gain", "selected_minus_baseline", "baseline_catastrophic",
            "selected_catastrophic",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in population_rows:
            writer.writerow({key: row[key] for key in fields})
    table = "\n".join(
        f"| {row['population']} | {row['baseline_seed']} | {row['selected_seed']} | "
        f"{row['baseline_gain']:.3f} | {row['selected_gain']:.3f} | "
        f"{row['selected_minus_baseline']:.3f} | {row['selected_catastrophic']} |"
        for row in population_rows
    )
    report = f"""# PR-DRTP B4 zero-training population feasibility

**Decision:** `{decision}`.

This is a retrospective exploratory feasibility audit. The independent unit is
the frozen three-member population (`n=5`); evaluation episodes are paired
technical repetitions and are not independent samples.

| Population | Baseline seed | Selected seed | G baseline | G selected | Selected-baseline Jpert mean | Selected catastrophic |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
{table}

```json
{json.dumps(criteria, indent=2)}
```

No training, continuation, population regrouping, selector tuning, ensemble or
distillation was started. A GO would authorize only a new prospective contract.
"""
    (report_dir / "PR_DRTP_B4_FEASIBILITY_REPORT.md").write_text(report, encoding="utf-8")
    print(json.dumps({
        "decision": decision,
        "report": str(report_dir / "PR_DRTP_B4_FEASIBILITY_REPORT.md"),
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
