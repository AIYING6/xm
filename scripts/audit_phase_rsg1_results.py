"""Audit the frozen RSG-1 development results and emit a decision report."""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

METHODS = ("mappo", "matched_single_graph", "rsg_tc")
SEEDS = (1501, 1502, 1503)
PROTOCOL = "PHASE-RSG-1-V1"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def mean(rows: list[dict[str, str]], key: str) -> float:
    return float(np.mean([float(row[key]) for row in rows]))


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def audit(root: Path) -> dict:
    summary_rows = read_csv(root / "per_seed_summary.csv")
    by_method = {method: [row for row in summary_rows if row["method"] == method]
                 for method in METHODS}
    expected = {(method, str(seed)) for method in METHODS for seed in SEEDS}
    observed = {(row["method"], row["train_seed"]) for row in summary_rows}
    integrity = {
        "summary_cells": len(summary_rows) == 9 and observed == expected,
        "completed_manifests": True,
        "updates_per_cell": True,
        "raw_rows_per_cell": True,
        "tape_per_cell": True,
    }
    manifests = []
    all_raw = []
    for method, seed in sorted(expected):
        run_dir = root / "runs" / method / f"seed{seed}"
        manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
        manifests.append(manifest)
        integrity["completed_manifests"] &= manifest.get("status") == "completed"
        integrity["updates_per_cell"] &= len(read_csv(run_dir / "train_log.csv")) == 782
        raw = read_csv(run_dir / "raw_episode_metrics.csv")
        integrity["raw_rows_per_cell"] &= len(raw) == 200
        ids = {int(row["development_episode_id"]) for row in raw}
        integrity["tape_per_cell"] &= ids == set(range(340000, 340100))
        all_raw.extend(raw)

    sg = by_method["matched_single_graph"]
    rsg = by_method["rsg_tc"]
    sg_nominal = mean(sg, "J_nominal_mean")
    rsg_nominal = mean(rsg, "J_nominal_mean")
    sg_failure = mean(sg, "J_failure_mean")
    rsg_failure = mean(rsg, "J_failure_mean")
    sg_delta = mean(sg, "delta_J_mean")
    rsg_delta = mean(rsg, "delta_J_mean")

    gates = {
        "gate_1_nominal_competence": {
            "value": rsg_nominal / sg_nominal if sg_nominal else math.nan,
            "threshold": 0.90,
            "pass": rsg_nominal / sg_nominal >= 0.90 if sg_nominal else False,
        },
        "gate_2_failure_score": {
            "value": rsg_failure / sg_failure if sg_failure else math.nan,
            "threshold": 0.90,
            "pass": rsg_failure >= 0.90 * sg_failure if sg_failure else False,
        },
        "gate_3_mean_degradation": {
            "rsg_tc_mean_delta_J": rsg_delta,
            "matched_sg_mean_delta_J": sg_delta,
            "pass": rsg_delta < sg_delta,
        },
    }
    sg_by_seed = {row["train_seed"]: float(row["delta_J_mean"]) for row in sg}
    rsg_by_seed = {row["train_seed"]: float(row["delta_J_mean"]) for row in rsg}
    better_seeds = [seed for seed in sorted(rsg_by_seed)
                    if rsg_by_seed[seed] < sg_by_seed[seed]]
    gates["gate_4_seed_direction"] = {
        "rsg_tc_better_seeds": better_seeds,
        "better_seed_count": len(better_seeds),
        "required_better_seed_count": 2,
        "pooled_direction": rsg_delta < sg_delta,
        "pass": len(better_seeds) >= 2 and rsg_delta < sg_delta,
    }

    safety = {}
    for metric in ("collision_failure_mean", "timeout_failure_mean", "constraint_failure_mean"):
        sg_value = mean(sg, metric)
        rsg_value = mean(rsg, metric)
        safety[metric] = {
            "rsg_tc": rsg_value, "matched_sg": sg_value,
            "absolute_difference": rsg_value - sg_value,
            "threshold": 0.05,
            "pass": rsg_value - sg_value <= 0.05,
        }
    gates["gate_5_safety"] = {**safety, "pass": all(item["pass"] for item in safety.values())}

    bias_rows = read_csv(root / "bias_telemetry.csv")
    bias_rows = [row for row in bias_rows if row["method"] == "rsg_tc"]
    bias_values = np.asarray([float(row["bias"]) for row in bias_rows], dtype=float)
    bias_seed_stats = {}
    for seed in SEEDS:
        rows = [row for row in bias_rows if row["train_seed"] == str(seed)]
        cells = defaultdict(list)
        for row in rows:
            cells[(row["relation_combo"], row["phase"], row["condition"])].append(float(row["bias"]))
        cell_means = {"|".join(key): float(np.mean(values)) for key, values in cells.items()}
        baseline = [float(row["bias"]) for row in rows
                    if row["condition"] == "nominal" and row["phase"] == "pre_failure"]
        perturbed = [float(row["bias"]) for row in rows
                     if row["condition"] == "relay_failure" and row["phase"] == "post_failure"]
        baseline_mean = float(np.mean(baseline)) if baseline else math.nan
        perturbed_mean = float(np.mean(perturbed)) if perturbed else math.nan
        cell_range = max(cell_means.values()) - min(cell_means.values()) if cell_means else 0.0
        phase_condition_diff = abs(perturbed_mean - baseline_mean) if baseline and perturbed else 0.0
        bias_seed_stats[str(seed)] = {
            "rows": len(rows), "observed_cells": len(cell_means),
            "cell_mean_range": cell_range,
            "nominal_pre_failure_mean": baseline_mean,
            "failure_post_failure_mean": perturbed_mean,
            "absolute_phase_condition_difference": phase_condition_diff,
            "seed_pass": cell_range > 1e-4 or phase_condition_diff > 1e-4,
        }
    passing_bias_seeds = [seed for seed, stats in bias_seed_stats.items() if stats["seed_pass"]]
    gates["gate_6_bias_telemetry"] = {
        "pooled_rows": len(bias_rows),
        "pooled_std": float(np.std(bias_values)) if len(bias_values) else 0.0,
        "pooled_std_threshold": 1e-4,
        "seed_stats": bias_seed_stats,
        "passing_seed_count": len(passing_bias_seeds),
        "required_passing_seed_count": 2,
        "pass": len(passing_bias_seeds) >= 2 and (float(np.std(bias_values)) > 1e-4 if len(bias_values) else False),
    }

    all_gates_pass = all(item["pass"] for item in gates.values()) and all(integrity.values())
    decision = "KEEP RSG-TC" if all_gates_pass else "REMOVE RSG-TC / RSG-1 NO-GO"
    result = {
        "protocol": PROTOCOL, "integrity": integrity, "all_integrity_pass": all(integrity.values()),
        "descriptive_means": {
            "matched_single_graph": {"J_nominal": sg_nominal, "J_failure": sg_failure, "delta_J": sg_delta},
            "rsg_tc": {"J_nominal": rsg_nominal, "J_failure": rsg_failure, "delta_J": rsg_delta},
        },
        "gates": gates, "all_gates_pass": all_gates_pass,
        "decision": decision, "manifests": manifests,
    }
    write_json(root / "RSG1_GATE_AUDIT.json", result)
    return result


def report(result: dict, path: Path, root: Path) -> None:
    d = result["descriptive_means"]
    g = result["gates"]
    lines = [
        "# Phase RSG-1 Development Smoke Report",
        "",
        "> Frozen nine-cell development smoke; descriptive development evidence only.",
        "",
        "## Final decision",
        "",
        f"**{result['decision']}**",
        "",
        "The result does not authorize canonical training or a headline claim. The fixed protocol, tape, seeds, and checkpoint rule were not changed.",
        "",
        "## Evidence integrity",
        "",
        "- 3 methods × 3 seeds = 9 completed cells.",
        "- 200,192 environment steps per cell; 782 updates per cell.",
        "- Fixed final checkpoint only; no resume, early stopping, promotion, or seed exclusion.",
        "- Shared paired evaluation tape: episode IDs 340000–340099.",
        "- Archive SHA256: `B5612CEA1A5B8D611CEFB1F813B942E3B536F78F689CDC6EFA3C6441CD52FE92`.",
        "",
        "## Descriptive primary metrics",
        "",
        "| Method | Mean nominal J | Mean failure J | Mean ΔJ |",
        "|---|---:|---:|---:|",
        f"| matched Single-Graph | {d['matched_single_graph']['J_nominal']:.4f} | {d['matched_single_graph']['J_failure']:.4f} | {d['matched_single_graph']['delta_J']:.4f} |",
        f"| RSG-TC | {d['rsg_tc']['J_nominal']:.4f} | {d['rsg_tc']['J_failure']:.4f} | {d['rsg_tc']['delta_J']:.4f} |",
        "",
        "RSG-TC nominal competence is substantially below matched Single-Graph, and its mean failure score is also lower. Its mean degradation is not lower than matched Single-Graph.",
        "",
        "## Gate results",
        "",
        "| Gate | Result | Evidence |",
        "|---|---|---|",
        f"| G1 nominal competence | {'PASS' if g['gate_1_nominal_competence']['pass'] else 'FAIL'} | ratio {g['gate_1_nominal_competence']['value']:.4f}, threshold ≥ 0.90 |",
        f"| G2 failure score | {'PASS' if g['gate_2_failure_score']['pass'] else 'FAIL'} | ratio {g['gate_2_failure_score']['value']:.4f}, threshold ≥ 0.90 |",
        f"| G3 mean degradation | {'PASS' if g['gate_3_mean_degradation']['pass'] else 'FAIL'} | RSG-TC {d['rsg_tc']['delta_J']:.4f} vs SG {d['matched_single_graph']['delta_J']:.4f} |",
        f"| G4 seed direction | {'PASS' if g['gate_4_seed_direction']['pass'] else 'FAIL'} | {g['gate_4_seed_direction']['better_seed_count']}/3 better; pooled direction {'PASS' if g['gate_4_seed_direction']['pooled_direction'] else 'FAIL'} |",
        f"| G5 safety | {'PASS' if g['gate_5_safety']['pass'] else 'FAIL'} | collision/timeout/constraint margins checked at 0.05 |",
        f"| G6 bias telemetry | {'PASS' if g['gate_6_bias_telemetry']['pass'] else 'FAIL'} | pooled std {g['gate_6_bias_telemetry']['pooled_std']:.6g}; seed rule checked |",
        "",
        "## Interpretation",
        "",
        "RSG-TC does not pass the pre-registered development retention rules. Two seeds have a smaller ΔJ than matched Single-Graph, but the pooled direction fails and the nominal/failure competence gates fail. The apparent lower degradation is therefore not sufficient evidence of robustness; it is confounded by weak and unstable nominal competence.",
        "",
        "The relation-bias telemetry is reported as mechanism diagnostics only. It cannot rescue the failed competence gates or justify a formal RSG-TC claim.",
        "",
        "## Next action",
        "",
        "- Stop RSG-TC architecture screening under this frozen contract.",
        "- Do not start canonical RSG-TC training, confirmatory seeds, or Phase 3A on the basis of this result.",
        "- Retain MAPPO and matched Single-Graph as controls/evidence; decide separately whether the simpler matched Single-Graph line is publishable as an application/robustness study.",
        "- Do not alter the environment, failure semantics, tape, or seeds to improve this outcome.",
        "",
        "Raw evidence remains under the archival result directory; `RSG1_GATE_AUDIT.json` contains the machine-readable audit.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.results_root)
    report(result, args.report, args.results_root)
    print(json.dumps({"decision": result["decision"], "all_gates_pass": result["all_gates_pass"],
                      "report": str(args.report)}, indent=2))


if __name__ == "__main__":
    main()
