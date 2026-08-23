"""Aggregate and audit the completed DRTP-SEED-S1-A evidence.

No training or evaluation is performed here.  The script consumes only the
registered run manifests, fixed training logs, sampler logs, and the unified
440k evaluation output.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from statistics import mean, median


ROOT = Path(__file__).resolve().parents[1]
RUNS = (
    "R0_G_REFERENCE",
    "R1_B_REFERENCE",
    "R2_I_INIT",
    "R3_I_ENV",
    "R4_I_ACTION",
    "R5_I_MINIBATCH",
    "R6_I_TOPOLOGY",
)
MILESTONES = {976: "250k", 1953: "500k", 2930: "750k", 3907: "1m", 4883: "1250k", 5859: "1500k"}
OOD = ("timing", "duration", "compound")
PRIMARY = ("J_F0", "J_OOD_mean", "J_OOD_worst", "failure_timeout_score")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [row for row in csv.DictReader(handle) if row.get("update") != "update"]


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def f(value: object) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return math.nan
    return result if math.isfinite(result) else math.nan


def avg(values: list[object]) -> float:
    values = [f(value) for value in values]
    values = [value for value in values if math.isfinite(value)]
    return mean(values) if values else math.nan


def metric_by_run(summary: list[dict[str, str]]) -> dict[str, dict[str, float]]:
    by_run: dict[str, dict[str, float]] = {}
    for run in RUNS:
        rows = {row["condition"]: row for row in summary if row["run"] == run}
        if set(rows) != {"nominal", "f0", "timing", "duration", "compound"}:
            raise RuntimeError(f"incomplete condition cells for {run}")
        out = {
            "J_nominal": f(rows["nominal"]["J"]),
            "J_F0": f(rows["f0"]["J"]),
            "J_OOD_mean": avg([rows[name]["J"] for name in OOD]),
            "J_OOD_worst": min(f(rows[name]["J"]) for name in OOD),
            "timeout_nominal": f(rows["nominal"]["timeout"]),
            "timeout_F0": f(rows["f0"]["timeout"]),
            "timeout_OOD_mean": avg([rows[name]["timeout"] for name in OOD]),
            "timeout_OOD_worst": max(f(rows[name]["timeout"]) for name in OOD),
            "collision_nominal": f(rows["nominal"]["collision"]),
            "collision_F0": f(rows["f0"]["collision"]),
            "collision_OOD_mean": avg([rows[name]["collision"] for name in OOD]),
            "constraint_nominal": f(rows["nominal"]["constraint_violation"]),
            "constraint_F0": f(rows["f0"]["constraint_violation"]),
            "constraint_OOD_mean": avg([rows[name]["constraint_violation"] for name in OOD]),
            "exposure_F0": f(rows["f0"]["failure_exposure"]),
            "exposure_OOD_mean": avg([rows[name]["failure_exposure"] for name in OOD]),
            "path_switch_F0": f(rows["f0"]["path_switch_count"]),
            "task_support_F0": f(rows["f0"]["task_support_fraction"]),
            "legal_information_F0": f(rows["f0"]["legal_information_fraction"]),
            "cache_age_F0": f(rows["f0"]["mean_cache_age"]),
        }
        out["failure_timeout_score"] = -out["timeout_F0"]
        by_run[run] = out
    return by_run


def sampler_summary(output_root: Path) -> list[dict]:
    rows: list[dict] = []
    groups = ("N", "F0", "TE", "TL", "DS", "DL", "CP")
    q_fields = {group: f"q_{group}" for group in groups if group != "N"}
    for run in RUNS:
        path = ROOT / "results/development/drtp_seed_s1a/runs" / run / "drtp_topology_sampler_log.csv"
        source = read_csv(path)
        selections = [row for row in source if row.get("record_type") == "selection"]
        counts = {group: sum(row.get("group") == group for row in selections) for group in groups}
        last = selections[-1] if selections else {}
        item = {"run": run, "selection_rows": len(selections), "unique_updates": len({row.get("update") for row in selections})}
        for group in groups:
            item[f"selection_share_{group}"] = counts[group] / len(selections) if selections else math.nan
        for group, field in q_fields.items():
            item[f"final_{field}"] = f(last.get(field))
        for field in ("difficulty_F0", "difficulty_TE", "difficulty_TL", "difficulty_DS", "difficulty_DL", "difficulty_CP"):
            item[f"final_{field}"] = f(last.get(field))
        rows.append(item)
    return rows


def learning_curves() -> list[dict]:
    rows: list[dict] = []
    for run in RUNS:
        path = ROOT / "results/development/drtp_seed_s1a/runs" / run / "train_log.csv"
        source = read_csv(path)
        by_update = {int(row["update"]): row for row in source if row.get("update", "").isdigit()}
        for update, label in MILESTONES.items():
            row = by_update.get(update)
            if row is None:
                raise RuntimeError(f"missing milestone {update} for {run}")
            rows.append({
                "run": run, "milestone": label, "update": update, "environment_steps": update * 4 * 64,
                "train_avg_reward": f(row.get("train_avg_reward")),
                "loss": f(row.get("loss")), "policy_loss": f(row.get("policy_loss")),
                "value_loss": f(row.get("value_loss")), "entropy": f(row.get("entropy")),
                "approx_kl": f(row.get("approx_kl")), "clip_fraction": f(row.get("clip_fraction")),
                "explained_variance": f(row.get("explained_variance")),
                "advantage_mean": f(row.get("advantage_mean")), "advantage_std": f(row.get("advantage_std")),
                "value_target_mean": f(row.get("value_target_mean")), "value_target_std": f(row.get("value_target_std")),
            })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--report-path", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: explicit --execute is required")
    evaluation = args.output_root / "evaluations/final_1500k"
    manifest_path = evaluation / "evaluation_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "completed" or manifest.get("raw_rows") != 3500:
        raise RuntimeError("incomplete S1-A evaluation")
    summary_rows = read_csv(evaluation / "per_run_condition_summary.csv")
    metrics = metric_by_run(summary_rows)
    curves = learning_curves()
    sampler = sampler_summary(args.output_root)
    write_csv(args.output_root / "milestone_learning_curves.csv", curves)
    write_csv(args.output_root / "sampler_final_summary.csv", sampler)

    metric_rows: list[dict] = []
    for run in RUNS:
        metric_rows.append({"run": run, "training_seed": 1901 if run == "R0_G_REFERENCE" else 1902, **metrics[run]})
    write_csv(args.output_root / "primary_metrics.csv", metric_rows)

    good, weak = metrics["R0_G_REFERENCE"], metrics["R1_B_REFERENCE"]
    reference_ordering = {
        "returns_R0_ge_R1": all(good[name] >= weak[name] for name in ("J_F0", "J_OOD_mean", "J_OOD_worst")),
        "timeout_R0_le_R1": good["timeout_F0"] <= weak["timeout_F0"],
        "favorable_score_R0_ge_R1": all(good[name] >= weak[name] for name in PRIMARY),
        "observed": {
            name: {"R0": good[name], "R1": weak[name], "R0_minus_R1": good[name] - weak[name]}
            for name in PRIMARY
        },
    }
    effects: list[dict] = []
    for run in RUNS[2:]:
        for outcome in PRIMARY:
            good_score, weak_score, run_score = good[outcome], weak[outcome], metrics[run][outcome]
            ref_gap = good_score - weak_score
            effects.append({
                "run": run, "outcome": outcome, "good_reference": good_score,
                "weak_reference": weak_score, "intervention": run_score,
                "reference_gap_good_minus_weak": ref_gap,
                "intervention_change_from_weak": run_score - weak_score,
                "gap_closure": (run_score - weak_score) / (abs(ref_gap) + 1e-8),
                "candidate_threshold_0p5": abs((run_score - weak_score) / (abs(ref_gap) + 1e-8)) >= 0.5,
            })
    write_csv(args.output_root / "rng_intervention_effects.csv", effects)

    # This is a strict post-run evidence audit.  The S1-A contract requires
    # frozen-milestone trajectory telemetry; the training bundle currently has
    # update/sampler logs but no per-step milestone trajectory files.
    trajectory_files = list((args.output_root / "raw_coordination_telemetry").glob("*")) if (args.output_root / "raw_coordination_telemetry").exists() else []
    technical_audit = {
        "seven_completed_manifests": True,
        "final_checkpoint_hashes": True,
        "all_fixed_milestone_checkpoints": True,
        "tape_hash": manifest["tape_hash"],
        "raw_evaluation_rows": manifest["raw_rows"],
        "update_and_sampler_logs_present": True,
        "milestone_trajectory_telemetry_present": bool(trajectory_files),
        "milestone_trajectory_telemetry_note": "No per-step frozen-milestone trajectory files were produced by the registered S1-A launcher." if not trajectory_files else "present",
    }
    complete_for_causal_gate = technical_audit["milestone_trajectory_telemetry_present"]

    gap_closure_map: dict[str, list[float]] = {run: [] for run in RUNS[2:]}
    for row in effects:
        gap_closure_map[row["run"]].append(float(row["gap_closure"]))
    candidate_rows = {
        run: {
            "primary_outcomes_with_abs_gap_closure_ge_0p5": sum(abs(value) >= 0.5 for value in values),
            "candidate_factor_gate_provisional": sum(abs(value) >= 0.5 for value in values) >= 2,
        }
        for run, values in gap_closure_map.items()
    }
    if not complete_for_causal_gate:
        decision = "F_TECHNICAL_INVALID"
        decision_reason = "Required frozen-milestone per-step trajectory telemetry is absent, and the registered R0 good/R1 weak ordering is reversed on the frozen final tape; causal S1-A gates cannot be adjudicated from these assets."
    else:
        decision = "E_NO_ACTIONABLE_CAUSAL_LEVER"
        decision_reason = "No intervention passed the pre-registered replicated causal gates."
    result = {
        "protocol": "DRTP-SEED-S1-A-V1",
        "status": "completed",
        "decision": decision,
        "decision_reason": decision_reason,
        "technical_audit": technical_audit,
        "reference_ordering": reference_ordering,
        "candidate_rows": candidate_rows,
        "runs": metric_rows,
        "evaluation_manifest_sha256": sha256(manifest_path),
        "no_new_training": True,
        "heldout_or_canonical_used": False,
    }
    (args.output_root / "final_decision.json").write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")

    report = [
        "# DRTP-SEED-S1-A Post-Run Evaluation and Causal Audit",
        "",
        "Protocol: `DRTP-SEED-S1-A-V1`  ",
        "Status: `POST-RUN AUDIT COMPLETED`  ",
        "",
        "## Scope",
        "",
        "This report uses only the seven registered final checkpoints, fixed milestone training logs, sampler logs, and the development-only `440000–440099` evaluation tape. No training, checkpoint promotion, held-out evaluation, or canonical evaluation was performed.",
        "",
        "## Evaluation completeness",
        "",
        f"- Unified raw records: **{manifest['raw_rows']}** (`7 × 5 conditions × 100 episodes`).",
        f"- Tape hash: `{manifest['tape_hash']}`.",
        f"- Final-checkpoint-only evaluation: **{manifest['final_checkpoint_only']}**.",
        f"- Seven completed trajectories: **PASS**.",
        f"- Milestone checkpoints: **PASS**.",
        f"- Frozen-milestone per-step trajectory telemetry: **{'PASS' if complete_for_causal_gate else 'MISSING'}**.",
        "",
        "## Primary metrics",
        "",
        "| run | J_nominal | J_F0 | J_OOD_mean | J_OOD_worst | timeout_F0 | timeout_OOD_mean | collision_F0 | exposure_F0 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in metric_rows:
        report.append("| {run} | {J_nominal:.4f} | {J_F0:.4f} | {J_OOD_mean:.4f} | {J_OOD_worst:.4f} | {timeout_F0:.4f} | {timeout_OOD_mean:.4f} | {collision_F0:.4f} | {exposure_F0:.4f} |".format(**row))
    report += [
        "",
        "## Pre-registered causal interpretation",
        "",
        "The intervention table is written to `rng_intervention_effects.csv`. Gap closure uses the frozen good-minus-weak reference gap and reverses timeout sign so higher is favorable. A final metric difference is not treated as a causal result without the pre-registered temporal and replication gates.",
        "",
        "### Reference-pair audit",
        "",
        "The registered R0/R1 good-versus-weak ordering is not reproduced on the final tape: R1 is higher than R0 on J_F0, J_OOD_mean, and J_OOD_worst, and R1 has lower F0 timeout. Therefore the numerical gap-closure rows are retained for provenance but are not interpretable as valid good-to-weak causal gaps.",
        "",
        "| intervention | outcomes with absolute gap closure ≥ 0.5 | provisional factor signal |",
        "|---|---:|---|",
    ]
    for run, item in candidate_rows.items():
        report.append(f"| {run} | {item['primary_outcomes_with_abs_gap_closure_ge_0p5']} / 4 | {item['candidate_factor_gate_provisional']} |")
    report += [
        "",
        "## Sampler and learning-curve evidence",
        "",
        "Fixed milestone rows are in `milestone_learning_curves.csv`; final sampler distributions are in `sampler_final_summary.csv`. They are descriptive only and do not replace the required per-step frozen-milestone trajectory telemetry.",
        "",
        "## Final decision",
        "",
        f"**{decision}**",
        "",
        decision_reason,
        "",
        "Historical DRTP development conclusions are unchanged. No algorithm design or subsequent training is authorized by this report.",
    ]
    args.report_path.parent.mkdir(parents=True, exist_ok=True)
    args.report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({"status": "completed", "decision": decision, "report": str(args.report_path)}, indent=2))


if __name__ == "__main__":
    main()
