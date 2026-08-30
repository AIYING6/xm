"""Create the frozen B5 1M mechanism-review data products without overclaiming."""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
import json
import math
from pathlib import Path


ARMS = ("utr_sg", "drtp_sg")
SEEDS = (3601, 3602, 3603, 3604, 3605)
LABELS = ("250k", "500k", "750k", "1m")
PERT = ("F0_44_80", "T28_28_80", "D120_44_120", "C28_120")
MILESTONE_END = {"250k": 976, "500k": 1953, "750k": 2930, "1m": 3907}


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f"cannot write empty data product: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def finite(values) -> list[float]:
    result = []
    for value in values:
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(number):
            result.append(number)
    return result


def average(values) -> float | None:
    values = finite(values)
    return sum(values) / len(values) if values else None


def window_label(update: int) -> str:
    for label in LABELS:
        if update <= MILESTONE_END[label]:
            return label
    raise ValueError(f"update outside frozen 1M ceiling: {update}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("--execute required")
    report = args.output_root / "diagnostics" / "b5_1m_mechanism_gate"
    if report.exists():
        raise FileExistsError(f"refusing aggregate rerun: {report}")
    report.mkdir(parents=True, exist_ok=False)
    eval_root = args.output_root / "evaluations" / "milestones_025m_to_1m"
    eval_manifest = json.loads((eval_root / "evaluation_manifest.json").read_text(encoding="utf-8"))
    if eval_manifest.get("raw_rows") != 20000 or eval_manifest.get("checkpoint_promotion") is not False:
        raise RuntimeError("invalid B5 evaluation integrity")
    conditions = read_csv(eval_root / "per_seed_condition_summary.csv")
    by_condition = {
        (row["arm"], int(row["seed"]), row["checkpoint_label"], row["condition"]): row
        for row in conditions
    }
    endpoints = []
    for arm in ARMS:
        for seed in SEEDS:
            for label in LABELS:
                nominal = float(by_condition[(arm, seed, label, "nominal")]["J"])
                perturbations = [float(by_condition[(arm, seed, label, condition)]["J"]) for condition in PERT]
                endpoints.append({
                    "arm": arm,
                    "seed": seed,
                    "checkpoint_label": label,
                    "J_nominal": nominal,
                    "J_F0": float(by_condition[(arm, seed, label, "F0_44_80")]["J"]),
                    "J_pert_mean": sum(perturbations) / len(perturbations),
                    "J_pert_worst": min(perturbations),
                    "collision_pert_mean": average(by_condition[(arm, seed, label, condition)]["collision"] for condition in PERT),
                    "timeout_pert_mean": average(by_condition[(arm, seed, label, condition)]["timeout"] for condition in PERT),
                    "independent_unit": "training_seed",
                })
    write_csv(report / "seed_level_milestone_endpoints.csv", endpoints)
    endpoint_index = {(row["arm"], row["seed"], row["checkpoint_label"]): row for row in endpoints}
    paired = []
    for seed in SEEDS:
        for label in LABELS:
            utr = endpoint_index[("utr_sg", seed, label)]
            drtp = endpoint_index[("drtp_sg", seed, label)]
            paired.append({
                "seed": seed,
                "checkpoint_label": label,
                "drtp_minus_utr_J_nominal": drtp["J_nominal"] - utr["J_nominal"],
                "drtp_minus_utr_J_F0": drtp["J_F0"] - utr["J_F0"],
                "drtp_minus_utr_J_pert_mean": drtp["J_pert_mean"] - utr["J_pert_mean"],
                "drtp_minus_utr_J_pert_worst": drtp["J_pert_worst"] - utr["J_pert_worst"],
                "inference_unit": "training_seed",
            })
    write_csv(report / "paired_endpoint_timeline.csv", paired)

    credit_summary, conflict_summary, inventory = [], [], []
    for arm in ARMS:
        for seed in SEEDS:
            run = args.output_root / "runs" / arm / f"seed{seed}"
            manifest = json.loads((run / "run_manifest.json").read_text(encoding="utf-8"))
            if manifest.get("status") != "completed" or manifest.get("environment_steps") != 1000192:
                raise RuntimeError(f"invalid B5 run: {run}")
            credit = read_csv(run / "group_credit_telemetry.csv")
            conflicts = read_csv(run / "group_credit_gradient_conflicts.csv")
            inventory.append({
                "arm": arm, "seed": seed, "credit_rows": len(credit), "conflict_rows": len(conflicts),
                "episode_summary_present": (run / "failure_telemetry" / "episode_summary.jsonl").is_file(),
                "event_window_present": (run / "failure_telemetry" / "failure_event_window.jsonl").is_file(),
            })
            grouped_credit: dict[tuple, list[dict]] = defaultdict(list)
            for row in credit:
                grouped_credit[(window_label(int(row["update"])), row["group"])].append(row)
            for (label, group), rows in grouped_credit.items():
                observed = [row for row in rows if row["status"] == "OK"]
                credit_summary.append({
                    "arm": arm, "seed": seed, "window_end": label, "group": group,
                    "observed_updates": len(observed),
                    "mean_value_residual_rmse": average(row["value_residual_rmse"] for row in observed),
                    "mean_td_residual_abs_q90": average(row["td_residual_abs_q90"] for row in observed),
                    "mean_normalized_advantage": average(row["normalized_advantage_mean"] for row in observed),
                    "mean_actor_gradient_norm": average(row["actor_gradient_norm"] for row in observed),
                    "mean_critic_gradient_norm": average(row["critic_gradient_norm"] for row in observed),
                    "repetition_unit": "update_x_group",
                    "independent_unit": "training_seed",
                })
            grouped_conflict: dict[tuple, list[dict]] = defaultdict(list)
            for row in conflicts:
                grouped_conflict[(window_label(int(row["update"])), row["group_a"], row["group_b"])].append(row)
            for (label, group_a, group_b), rows in grouped_conflict.items():
                conflict_summary.append({
                    "arm": arm, "seed": seed, "window_end": label,
                    "group_a": group_a, "group_b": group_b, "observed_updates": len(rows),
                    "mean_actor_cosine": average(row["actor_gradient_cosine"] for row in rows),
                    "actor_conflict_fraction": average(1.0 if row["actor_gradient_conflict"] == "True" else 0.0 for row in rows),
                    "mean_critic_cosine": average(row["critic_gradient_cosine"] for row in rows),
                    "critic_conflict_fraction": average(1.0 if row["critic_gradient_conflict"] == "True" else 0.0 for row in rows),
                    "repetition_unit": "update_x_group_pair",
                    "independent_unit": "training_seed",
                })
    write_csv(report / "group_credit_timeline_summary.csv", credit_summary)
    write_csv(report / "gradient_conflict_timeline_summary.csv", conflict_summary)
    write_csv(report / "telemetry_integrity_inventory.csv", inventory)
    integrity = all(
        row["credit_rows"] > 0 and row["conflict_rows"] > 0 and
        row["episode_summary_present"] and row["event_window_present"]
        for row in inventory
    )
    status = "B5_1M_MECHANISM_GATE_READY_FOR_REVIEW" if integrity else "B5_TECHNICAL_INVALID"
    decision = {
        "status": status,
        "integrity": integrity,
        "mechanism_declared": False,
        "algorithm_modification_authorized": False,
        "automatic_continuation_authorized": False,
        "independent_unit": "training_seed",
        "note": "Update/group rows and evaluation episodes are technical repetitions, not independent n."
    }
    (report / "B5_1M_GATE_DECISION.json").write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    (report / "B5_1M_GATE_REPORT.md").write_text(
        f"# DRTP B5 1M mechanism gate\n\n**Status:** `{status}`.\n\n"
        "This automatic stage verifies provenance and constructs the frozen time-aligned evidence products. "
        "It does not infer a mechanism from final-score correlation and does not authorize a new algorithm. "
        "A human review must apply every frozen temporal-precedence, 2/5 replication, paired-UTR specificity, "
        "middle-layer and neighboring-threshold requirement.\n",
        encoding="utf-8",
    )
    print(json.dumps(decision, indent=2))


if __name__ == "__main__":
    main()
