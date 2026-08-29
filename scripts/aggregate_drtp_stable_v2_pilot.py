"""Apply the frozen high-return/downside/reliability Stable-v2 pilot gate."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import statistics


ROOT = Path(__file__).resolve().parents[1]
ARMS = ("utr_sg", "drtp_sg", "drtp_klr_sg")
SEEDS = (3101, 3102, 3103)
CONDITIONS = ("nominal", "F0_44_80", "T28_28_80", "D120_44_120", "C28_120")
FAILURES = CONDITIONS[1:]
ENDPOINTS = ("J_nominal", "J_F0", "J_pert_mean", "J_pert_worst")
EXPECTED_RAW = len(ARMS) * len(SEEDS) * len(CONDITIONS) * 100
TAPE = ROOT / "configs" / "drtp_stable_v2_pilot_tape.json"
FREEZE = ROOT / "configs" / "drtp_stable_v2_pilot_freeze.json"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def average(values) -> float:
    values = list(values)
    return sum(values) / len(values)


def dispersion(values: list[float]) -> dict[str, float]:
    median = statistics.median(values)
    return {
        "range": max(values) - min(values),
        "sample_sd": statistics.stdev(values),
        "mad": statistics.median(abs(value - median) for value in values),
    }


def metric_cell(summary: list[dict[str, str]], arm: str, seed: int) -> dict[str, float]:
    rows = {row["condition"]: row for row in summary if row["method"] == arm and int(row["train_seed"]) == seed}
    if set(rows) != set(CONDITIONS):
        raise RuntimeError(f"missing metric cell: {arm}/seed{seed}")
    value = lambda condition, key: float(rows[condition][key])
    return {
        "J_nominal": value("nominal", "J"),
        "J_F0": value("F0_44_80", "J"),
        "J_pert_mean": average(value(condition, "J") for condition in FAILURES),
        "J_pert_worst": min(value(condition, "J") for condition in FAILURES),
        "collision": average(value(condition, "collision") for condition in FAILURES),
        "timeout": average(value(condition, "timeout") for condition in FAILURES),
        "constraint_violation": max(value(condition, "constraint_violation") for condition in FAILURES),
    }


def ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0.0:
        raise RuntimeError("catastrophic gate requires positive UTR score endpoints")
    return numerator / denominator


def catastrophic(candidate: dict[str, float], utr: dict[str, float]) -> bool:
    f0_ratio = ratio(candidate["J_F0"], utr["J_F0"])
    worst_ratio = ratio(candidate["J_pert_worst"], utr["J_pert_worst"])
    reward_collapse = (
        (f0_ratio < 0.70 and worst_ratio < 0.85)
        or (worst_ratio < 0.70 and f0_ratio < 0.85)
    )
    safety_collapse = (
        candidate["timeout"] - utr["timeout"] > 0.20
        and (f0_ratio < 0.85 or worst_ratio < 0.85)
    )
    return reward_collapse or safety_collapse


def telemetry(output_root: Path) -> dict:
    per_seed, total_triggers, total_attempts = [], 0, 0
    for seed in SEEDS:
        path = output_root / "runs" / "drtp_klr_sg" / f"seed{seed}" / "train_log.csv"
        rows = read_csv(path)
        if len(rows) != 1953:
            raise RuntimeError(f"incomplete Stable-v2 telemetry: seed{seed} has {len(rows)} rows")
        required = {
            "policy_guard_triggered", "policy_steps_attempted", "policy_steps_accepted",
            "policy_kl_attempted_max", "policy_kl_threshold",
            "actor_optimizer_state_restored", "critic_step_retained_after_actor_rollback",
        }
        if not required.issubset(rows[0]):
            raise RuntimeError(f"missing Stable-v2 telemetry fields: seed{seed}")
        triggers = sum(int(float(row["policy_guard_triggered"])) for row in rows)
        attempts = sum(int(float(row["policy_steps_attempted"])) for row in rows)
        restored = sum(int(float(row["actor_optimizer_state_restored"])) for row in rows)
        critic_retained = sum(int(float(row["critic_step_retained_after_actor_rollback"])) for row in rows)
        if triggers != restored or triggers != critic_retained:
            raise RuntimeError(f"rollback telemetry inconsistency: seed{seed}")
        if any(float(row["policy_kl_threshold"]) != 0.02 for row in rows):
            raise RuntimeError(f"target KL drift: seed{seed}")
        total_triggers += triggers
        total_attempts += attempts
        per_seed.append({
            "seed": seed,
            "triggers": triggers,
            "attempts": attempts,
            "intervention_rate": triggers / attempts if attempts else 0.0,
            "max_attempted_kl": max(float(row["policy_kl_attempted_max"]) for row in rows),
        })
    return {
        "per_seed": per_seed,
        "total_triggers": total_triggers,
        "total_attempts": total_attempts,
        "pooled_intervention_rate": total_triggers / total_attempts if total_attempts else 0.0,
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
    if audit.get("status") != "D1_TECHNICAL_PASS":
        raise RuntimeError("TECHNICAL_INVALID: D1 audit is not PASS")
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
        raise RuntimeError("TECHNICAL_INVALID: incomplete or contract-violating Stable-v2 pilot")
    metrics = {arm: {seed: metric_cell(summary, arm, seed) for seed in SEEDS} for arm in ARMS}
    seed_rows = []
    for seed in SEEDS:
        utr, original, candidate = metrics["utr_sg"][seed], metrics["drtp_sg"][seed], metrics["drtp_klr_sg"][seed]
        row = {
            "seed": seed,
            "G_original": original["J_pert_mean"] - utr["J_pert_mean"],
            "G_klr": candidate["J_pert_mean"] - utr["J_pert_mean"],
            "klr_minus_original": candidate["J_pert_mean"] - original["J_pert_mean"],
            "original_catastrophic": catastrophic(original, utr),
            "klr_catastrophic": catastrophic(candidate, utr),
        }
        for endpoint in ENDPOINTS:
            row[f"original_{endpoint}"] = original[endpoint]
            row[f"klr_{endpoint}"] = candidate[endpoint]
            row[f"klr_minus_original_{endpoint}"] = candidate[endpoint] - original[endpoint]
        seed_rows.append(row)
    epsilon = float(freeze["epsilon_J"])
    margin = float(freeze["practical_downside_improvement_margin"])
    original_gains = [row["G_original"] for row in seed_rows]
    candidate_gains = [row["G_klr"] for row in seed_rows]
    original_dispersion, candidate_dispersion = dispersion(original_gains), dispersion(candidate_gains)
    endpoint_retention = {
        endpoint: average(metrics["drtp_klr_sg"][seed][endpoint] for seed in SEEDS)
        >= average(metrics["drtp_sg"][seed][endpoint] for seed in SEEDS) - epsilon
        for endpoint in ENDPOINTS
    }
    advantage_retention = all(endpoint_retention.values())
    downside_protection = (
        min(candidate_gains) - min(original_gains) > margin
        and sum(row["klr_catastrophic"] for row in seed_rows)
        <= sum(row["original_catastrophic"] for row in seed_rows)
    )
    seed_reliability = (
        candidate_dispersion["range"] < original_dispersion["range"]
        and candidate_dispersion["sample_sd"] < original_dispersion["sample_sd"]
    )
    direction_consistency = sum(row["klr_minus_original"] >= -epsilon for row in seed_rows) >= 2
    upper_tail_rows = [row for row in seed_rows if row["G_original"] > epsilon]
    upper_tail_retention = bool(upper_tail_rows) and all(
        row["klr_minus_original"] >= -epsilon for row in upper_tail_rows
    )
    safety_rows = []
    for seed in SEEDS:
        for condition in CONDITIONS:
            by_arm = {
                arm: next(
                    row for row in summary
                    if row["method"] == arm
                    and int(row["train_seed"]) == seed
                    and row["condition"] == condition
                )
                for arm in ARMS
            }
            candidate = by_arm["drtp_klr_sg"]
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
        all(average(row[key] for row in failure_safety if row["reference"] == reference) <= float(freeze["pooled_safety_margin"])
            for reference in ("utr_sg", "drtp_sg") for key in ("collision_difference", "timeout_difference"))
        and all(
            row["collision_difference"] <= float(freeze["seed_condition_safety_margin"])
            and row["timeout_difference"] <= float(freeze["seed_condition_safety_margin"])
            and row["constraint_difference"] <= 0.0
            for row in safety_rows
        )
    )
    guard = telemetry(args.output_root)
    mechanism_activity = (
        guard["total_triggers"] >= int(freeze["minimum_intervention_count"])
        and guard["pooled_intervention_rate"] <= float(freeze["maximum_intervention_rate"])
    )
    criteria = {
        "advantage_retention_all_four_endpoints": advantage_retention,
        "downside_protection": downside_protection,
        "seed_reliability_range_and_sd": seed_reliability,
        "direction_consistency": direction_consistency,
        "upper_tail_retention": upper_tail_retention,
        "upper_tail_assessable": bool(upper_tail_rows),
        "safety_vs_utr_and_original": safety,
        "mechanism_activity": mechanism_activity,
        "integrity": integrity,
    }
    required = (
        "advantage_retention_all_four_endpoints", "downside_protection",
        "seed_reliability_range_and_sd", "direction_consistency", "upper_tail_retention",
        "upper_tail_assessable", "safety_vs_utr_and_original", "mechanism_activity", "integrity",
    )
    decision = "PILOT_GO_SIGNAL" if all(criteria[key] for key in required) else "PILOT_NO_GO"
    reasons = [key for key in required if not criteria[key]]
    output = args.output_root / "diagnostics" / "stable_v2_pilot_gate"
    if output.exists():
        raise FileExistsError(f"refusing aggregate overwrite/rerun: {output}")
    output.mkdir(parents=True, exist_ok=False)
    with (output / "seed_level_results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(seed_rows[0]))
        writer.writeheader()
        writer.writerows(seed_rows)
    with (output / "safety_results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(safety_rows[0]))
        writer.writeheader()
        writer.writerows(safety_rows)
    result = {
        "protocol": "DRTP-STABLE-V2-PILOT-GATE-V1",
        "decision": decision,
        "criteria": criteria,
        "no_go_reasons": reasons,
        "endpoint_retention": endpoint_retention,
        "epsilon_J": epsilon,
        "downside_margin": margin,
        "original_gain_dispersion": original_dispersion,
        "klr_gain_dispersion": candidate_dispersion,
        "upper_tail_reference_seeds": [row["seed"] for row in upper_tail_rows],
        "guard_telemetry": guard,
        "seed_results": seed_rows,
        "automatic_continuation_started": False,
        "mainline_a_modified": False,
    }
    (output / "PILOT_GATE_DECISION.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    table = "\n".join(
        f"| {row['seed']} | {row['G_original']:.3f} | {row['G_klr']:.3f} | {row['klr_minus_original']:.3f} | {row['original_catastrophic']} | {row['klr_catastrophic']} |"
        for row in seed_rows
    )
    report = f"""# Stable-v2 0.5M pilot gate

**Decision:** `{decision}`. This development result does not modify mainline A and starts no continuation.

| Seed | G Original | G KLR | KLR−Original | Original catastrophic | KLR catastrophic |
|---:|---:|---:|---:|---|---|
{table}

## Frozen criteria

```json
{json.dumps(criteria, indent=2)}
```

Endpoint retention: `{json.dumps(endpoint_retention)}`.

Original gain dispersion: `{json.dumps(original_dispersion)}`. KLR gain dispersion: `{json.dumps(candidate_dispersion)}`.

Guard activity: `{json.dumps(guard)}`.

NO-GO reasons: `{reasons if reasons else 'none'}`. No seed replacement, threshold tuning, checkpoint promotion, or automatic continuation was started.
"""
    (output / "PILOT_GATE_REPORT.md").write_text(report, encoding="utf-8")
    print(json.dumps({"decision": decision, "report": str(output / "PILOT_GATE_REPORT.md")}, indent=2))


if __name__ == "__main__":
    main()
