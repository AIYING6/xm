"""Apply the frozen D5 high-return and seed-reliability pilot gate."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from aggregate_drtp_stable_v2_pilot import (  # noqa: E402
    average,
    catastrophic,
    dispersion,
    metric_cell,
    read_csv,
)


ARMS = ("utr_sg", "drtp_sg", "drtp_klb_sg")
SEEDS = (3201, 3202, 3203)
CONDITIONS = ("nominal", "F0_44_80", "T28_28_80", "D120_44_120", "C28_120")
FAILURES = CONDITIONS[1:]
ENDPOINTS = ("J_nominal", "J_F0", "J_pert_mean", "J_pert_worst")
EXPECTED_RAW = len(ARMS) * len(SEEDS) * len(CONDITIONS) * 100
TAPE = ROOT / "configs" / "drtp_stable_v2_d5_pilot_tape.json"
FREEZE = ROOT / "configs" / "drtp_stable_v2_d5_pilot_freeze.json"


def telemetry(output_root: Path, freeze: dict) -> dict:
    per_seed, total_triggers, total_attempts = [], 0, 0
    semantic_valid = True
    for seed in SEEDS:
        path = output_root / "runs" / "drtp_klb_sg" / f"seed{seed}" / "train_log.csv"
        rows = read_csv(path)
        if len(rows) != 1953:
            raise RuntimeError(f"incomplete D5 telemetry: seed{seed} has {len(rows)} rows")
        required = {
            "policy_guard_triggered", "policy_steps_attempted", "policy_steps_accepted",
            "policy_kl_post_step", "policy_kl_attempted_max", "policy_kl_threshold",
            "actor_attempted_update_l2", "actor_accepted_update_l2", "actor_projection_l2",
            "policy_backtrack_alpha", "policy_backtrack_iterations",
            "actor_optimizer_state_restored", "actor_optimizer_state_retained_after_projection",
            "critic_step_retained_after_policy_guard",
        }
        if not required.issubset(rows[0]):
            raise RuntimeError(f"missing D5 telemetry fields: seed{seed}")
        if any(float(row["policy_kl_threshold"]) != 0.02 for row in rows):
            raise RuntimeError(f"target KL drift: seed{seed}")
        triggers = [row for row in rows if int(float(row["policy_guard_triggered"])) == 1]
        nontriggers = [row for row in rows if int(float(row["policy_guard_triggered"])) == 0]
        trigger_semantics = all(
            0.0 < float(row["policy_backtrack_alpha"]) < 1.0
            and int(float(row["policy_backtrack_iterations"])) == int(freeze["backtrack_bisection_steps"])
            and float(row["policy_kl_attempted_max"]) > float(freeze["target_kl"])
            and float(row["policy_kl_post_step"]) <= float(freeze["target_kl"])
            and float(row["actor_accepted_update_l2"]) > 0.0
            and float(row["actor_projection_l2"]) > 0.0
            and int(float(row["actor_optimizer_state_restored"])) == 0
            and int(float(row["actor_optimizer_state_retained_after_projection"])) == 1
            and int(float(row["critic_step_retained_after_policy_guard"])) == 1
            for row in triggers
        )
        nontrigger_semantics = all(
            float(row["policy_backtrack_alpha"]) == 1.0
            and int(float(row["policy_backtrack_iterations"])) == 0
            and float(row["actor_projection_l2"]) == 0.0
            and int(float(row["actor_optimizer_state_retained_after_projection"])) == 0
            for row in nontriggers
        )
        semantic_valid = semantic_valid and trigger_semantics and nontrigger_semantics
        attempts = sum(int(float(row["policy_steps_attempted"])) for row in rows)
        total_triggers += len(triggers)
        total_attempts += attempts
        per_seed.append({
            "seed": seed,
            "triggers": len(triggers),
            "attempts": attempts,
            "intervention_rate": len(triggers) / attempts if attempts else 0.0,
            "alpha_min": min((float(row["policy_backtrack_alpha"]) for row in triggers), default=1.0),
            "alpha_max": max((float(row["policy_backtrack_alpha"]) for row in triggers), default=1.0),
            "max_attempted_kl": max(float(row["policy_kl_attempted_max"]) for row in rows),
            "semantics_valid": trigger_semantics and nontrigger_semantics,
        })
    pooled_rate = total_triggers / total_attempts if total_attempts else 0.0
    active = (
        total_triggers >= int(freeze["minimum_intervention_count"])
        and pooled_rate <= float(freeze["maximum_intervention_rate"])
        and semantic_valid
    )
    return {
        "per_seed": per_seed,
        "total_triggers": total_triggers,
        "total_attempts": total_attempts,
        "pooled_intervention_rate": pooled_rate,
        "semantics_valid": semantic_valid,
        "mechanism_activity_valid": active,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--technical-audit", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("--execute required")
    audit = json.loads(args.technical_audit.read_text(encoding="utf-8"))
    if audit.get("status") != "D4_TECHNICAL_PASS":
        raise RuntimeError("TECHNICAL_INVALID: D4 audit is not PASS")
    tape = json.loads(TAPE.read_text(encoding="utf-8"))
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    evaluation = args.output_root / "evaluations" / "final_05m"
    manifest = json.loads((evaluation / "evaluation_manifest.json").read_text(encoding="utf-8"))
    raw = read_csv(evaluation / "raw_episode_metrics.csv")
    summary = read_csv(evaluation / "per_seed_condition_summary.csv")
    expected_summary = {(arm, seed, condition) for arm in ARMS for seed in SEEDS for condition in CONDITIONS}
    found_summary = {(row["method"], int(row["train_seed"]), row["condition"]) for row in summary}
    source_runs = manifest.get("source_runs", [])
    source_valid = len(source_runs) == 9 and all(
        run.get("status") == "completed"
        and run.get("updates") == 1953
        and run.get("environment_steps") == 499968
        and run.get("parameter_count") == 116728
        and run.get("early_stopping") is False
        and run.get("checkpoint_promotion") is False
        and run.get("seed_replacement") is False
        and run.get("tape_hash") == tape["tape_hash"]
        for run in source_runs
    )
    integrity = (
        manifest.get("status") == "completed"
        and manifest.get("raw_rows") == EXPECTED_RAW
        and len(raw) == EXPECTED_RAW
        and found_summary == expected_summary
        and source_valid
    )
    if not integrity:
        raise RuntimeError("TECHNICAL_INVALID: incomplete or contract-violating D5 pilot")
    metrics = {arm: {seed: metric_cell(summary, arm, seed) for seed in SEEDS} for arm in ARMS}
    epsilon = float(freeze["epsilon_J"])
    margin = float(freeze["practical_downside_improvement_margin"])
    seed_rows = []
    for seed in SEEDS:
        utr, original, candidate = metrics["utr_sg"][seed], metrics["drtp_sg"][seed], metrics["drtp_klb_sg"][seed]
        row = {
            "seed": seed,
            "G_original": original["J_pert_mean"] - utr["J_pert_mean"],
            "G_klb": candidate["J_pert_mean"] - utr["J_pert_mean"],
            "klb_minus_original": candidate["J_pert_mean"] - original["J_pert_mean"],
            "original_catastrophic": catastrophic(original, utr, epsilon),
            "klb_catastrophic": catastrophic(candidate, utr, epsilon),
        }
        for endpoint in ENDPOINTS:
            row[f"original_{endpoint}"] = original[endpoint]
            row[f"klb_{endpoint}"] = candidate[endpoint]
            row[f"klb_minus_original_{endpoint}"] = candidate[endpoint] - original[endpoint]
        seed_rows.append(row)
    original_gains = [row["G_original"] for row in seed_rows]
    candidate_gains = [row["G_klb"] for row in seed_rows]
    original_dispersion, candidate_dispersion = dispersion(original_gains), dispersion(candidate_gains)
    endpoint_retention = {
        endpoint: average(metrics["drtp_klb_sg"][seed][endpoint] for seed in SEEDS)
        >= average(metrics["drtp_sg"][seed][endpoint] for seed in SEEDS) - epsilon
        for endpoint in ENDPOINTS
    }
    advantage_retention = all(endpoint_retention.values())
    downside_protection = (
        min(candidate_gains) - min(original_gains) > margin
        and sum(row["klb_catastrophic"] for row in seed_rows)
        <= int(freeze["candidate_catastrophic_count_max"])
    )
    seed_reliability = (
        candidate_dispersion["range"] < original_dispersion["range"]
        and candidate_dispersion["sample_sd"] < original_dispersion["sample_sd"]
    )
    direction_consistency = sum(gain < 0.0 for gain in candidate_gains) <= int(freeze["candidate_negative_gain_count_max"])
    upper_tail_rows = [row for row in seed_rows if row["G_original"] > epsilon]
    upper_tail_assessable = bool(upper_tail_rows)
    upper_tail_retention = upper_tail_assessable and all(
        row["klb_minus_original"] >= -epsilon for row in upper_tail_rows
    )
    safety_rows = []
    for seed in SEEDS:
        for condition in CONDITIONS:
            by_arm = {
                arm: next(row for row in summary if row["method"] == arm and int(row["train_seed"]) == seed and row["condition"] == condition)
                for arm in ARMS
            }
            candidate = by_arm["drtp_klb_sg"]
            for reference_arm in ("utr_sg", "drtp_sg"):
                reference = by_arm[reference_arm]
                safety_rows.append({
                    "seed": seed,
                    "condition": condition,
                    "reference": reference_arm,
                    "collision_difference": float(candidate["collision"]) - float(reference["collision"]),
                    "timeout_difference": float(candidate["timeout"]) - float(reference["timeout"]),
                    "constraint_difference": float(candidate["constraint_violation"]) - float(reference["constraint_violation"]),
                })
    failure_safety = [row for row in safety_rows if row["condition"] in FAILURES]
    safety = (
        all(
            average(row[key] for row in failure_safety if row["reference"] == reference) <= float(freeze["pooled_safety_margin"])
            for reference in ("utr_sg", "drtp_sg") for key in ("collision_difference", "timeout_difference")
        )
        and all(
            row["collision_difference"] <= float(freeze["seed_condition_safety_margin"])
            and row["timeout_difference"] <= float(freeze["seed_condition_safety_margin"])
            and row["constraint_difference"] <= 0.0
            for row in safety_rows
        )
    )
    guard = telemetry(args.output_root, freeze)
    criteria = {
        "advantage_retention_all_four_endpoints": advantage_retention,
        "downside_protection_zero_catastrophic": downside_protection,
        "seed_reliability_range_and_sd": seed_reliability,
        "all_candidate_gains_nonnegative": direction_consistency,
        "upper_tail_retention": upper_tail_retention,
        "upper_tail_assessable": upper_tail_assessable,
        "safety_vs_utr_and_original": safety,
        "mechanism_activity_and_semantics": guard["mechanism_activity_valid"],
        "integrity": integrity,
    }
    non_upper_required = (
        "advantage_retention_all_four_endpoints", "downside_protection_zero_catastrophic",
        "seed_reliability_range_and_sd", "all_candidate_gains_nonnegative",
        "safety_vs_utr_and_original", "mechanism_activity_and_semantics", "integrity",
    )
    if all(criteria[key] for key in non_upper_required) and upper_tail_retention and upper_tail_assessable:
        decision = "D5_PILOT_GO_SIGNAL"
    elif all(criteria[key] for key in non_upper_required) and not upper_tail_assessable:
        decision = "D5_PILOT_INCONCLUSIVE_UPPER_TAIL"
    else:
        decision = "D5_PILOT_NO_GO"
    output = args.output_root / "diagnostics" / "stable_v2_d5_pilot_gate"
    if output.exists():
        raise FileExistsError(f"refusing aggregate overwrite/rerun: {output}")
    output.mkdir(parents=True, exist_ok=False)
    with (output / "seed_level_results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(seed_rows[0]))
        writer.writeheader(); writer.writerows(seed_rows)
    with (output / "safety_results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(safety_rows[0]))
        writer.writeheader(); writer.writerows(safety_rows)
    result = {
        "protocol": "DRTP-STABLE-V2-D5-PILOT-GATE-V1",
        "decision": decision,
        "criteria": criteria,
        "epsilon_J": epsilon,
        "downside_margin": margin,
        "endpoint_retention": endpoint_retention,
        "original_gain_dispersion": original_dispersion,
        "klb_gain_dispersion": candidate_dispersion,
        "upper_tail_reference_seeds": [row["seed"] for row in upper_tail_rows],
        "guard_telemetry": guard,
        "seed_results": seed_rows,
        "automatic_continuation_started": False,
        "mainline_a_modified": False,
    }
    with (output / "D5_PILOT_GATE_DECISION.json").open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2); handle.write("\n")
    table = "\n".join(
        f"| {row['seed']} | {row['G_original']:.3f} | {row['G_klb']:.3f} | {row['klb_minus_original']:.3f} | {row['original_catastrophic']} | {row['klb_catastrophic']} |"
        for row in seed_rows
    )
    report = f"""# DRTP-KLB D5 0.5M pilot gate

**Decision:** `{decision}`. No continuation or mainline-A change was started.

| Seed | G Original | G KLB | KLB-Original | Original catastrophic | KLB catastrophic |
|---:|---:|---:|---:|---|---|
{table}

## Frozen criteria

```json
{json.dumps(criteria, indent=2)}
```

Endpoint retention: `{json.dumps(endpoint_retention)}`.

Original dispersion: `{json.dumps(original_dispersion)}`. KLB dispersion: `{json.dumps(candidate_dispersion)}`.

KLB activity: `{json.dumps(guard)}`.

No seed replacement, target-KL change, checkpoint promotion, performance rerun, or automatic continuation was started.
"""
    with (output / "D5_PILOT_GATE_REPORT.md").open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(report)
    print(json.dumps({"decision": decision, "report": str(output / "D5_PILOT_GATE_REPORT.md")}, indent=2))


if __name__ == "__main__":
    main()
