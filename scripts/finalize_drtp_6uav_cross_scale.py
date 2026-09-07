"""Read and finalize the frozen 6-UAV UTR-versus-DRTP endpoint artifacts.

This utility never trains, evaluates a checkpoint, reads an evaluation tape online,
or changes the completed 6-UAV experiment.  It only validates the expected files
and derives seed-level and cohort-level tables plus a publication figure.
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

import matplotlib as mpl
import matplotlib.pyplot as plt


ARMS = (
    "utr_scout_terminal_assigned_role_sg_mappo",
    "drtp_scout_terminal_assigned_role_sg_mappo",
)
METHOD_LABELS = {ARMS[0]: "UTR", ARMS[1]: "DRTP"}
SEEDS = (69011, 69012, 69013, 69014, 69015)
ALL_GROUPS = ("nominal", "R_upstream", "R_downstream", "C_relay_node", "C_balanced", "C_cross", "C_same_relay")
FAILURE_GROUPS = tuple(group for group in ALL_GROUPS if group != "nominal")
EPISODES_PER_GROUP = 100


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise RuntimeError(f"Refusing to write empty table: {path.name}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def mean(values: list[float]) -> float:
    return float(statistics.fmean(values))


def sample_sd(values: list[float]) -> float:
    return float(statistics.stdev(values)) if len(values) > 1 else 0.0


def load_seed_endpoint(output_root: Path, arm: str, seed: int) -> dict[str, Any]:
    run = output_root / "runs" / arm / f"seed{seed}"
    manifest_path = run / "run_manifest.json"
    evaluation_path = output_root / "evaluations" / arm / f"seed{seed}_final_10m.csv"
    if not manifest_path.is_file() or not evaluation_path.is_file():
        raise FileNotFoundError(f"Missing completed run or endpoint file for {arm}/seed{seed}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "completed" or manifest.get("updates") != 39063:
        raise RuntimeError(f"Run manifest is not a completed frozen 10M endpoint: {manifest_path}")
    rows = read_rows(evaluation_path)
    expected_rows = len(ALL_GROUPS) * EPISODES_PER_GROUP
    if len(rows) != expected_rows:
        raise RuntimeError(f"Expected {expected_rows} endpoint rows, found {len(rows)}: {evaluation_path}")
    by_group: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row.get("arm") != arm or int(row.get("seed", -1)) != seed or row.get("group") not in ALL_GROUPS:
            raise RuntimeError(f"Invalid endpoint row in {evaluation_path}")
        if row.get("checkpoint_sha256") != manifest.get("checkpoint_sha256"):
            raise RuntimeError(f"Checkpoint provenance mismatch in {evaluation_path}")
        by_group[row["group"]].append(row)
    if tuple(sorted(by_group)) != tuple(sorted(ALL_GROUPS)) or any(len(by_group[group]) != EPISODES_PER_GROUP for group in ALL_GROUPS):
        raise RuntimeError(f"Incomplete frozen group coverage in {evaluation_path}")
    group_means = {
        group: {
            metric: mean([float(row[metric]) for row in by_group[group]])
            for metric in ("score", "success", "timeout", "collision")
        }
        for group in ALL_GROUPS
    }
    failure = [group_means[group] for group in FAILURE_GROUPS]
    return {
        "method": METHOD_LABELS[arm],
        "arm": arm,
        "train_seed": seed,
        "checkpoint_sha256": manifest["checkpoint_sha256"],
        "J_nominal": group_means["nominal"]["score"],
        "J_perturbed": mean([item["score"] for item in failure]),
        "J_perturbed_worst_condition": min(item["score"] for item in failure),
        "success_perturbed": mean([item["success"] for item in failure]),
        "timeout_perturbed": mean([item["timeout"] for item in failure]),
        "collision_perturbed": mean([item["collision"] for item in failure]),
    }


def cohort_summary(seed_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for method in ("UTR", "DRTP"):
        rows = [row for row in seed_rows if row["method"] == method]
        result: dict[str, Any] = {"method": method, "n_training_seeds": len(rows)}
        for metric in ("J_perturbed", "J_perturbed_worst_condition", "success_perturbed", "timeout_perturbed", "collision_perturbed"):
            values = [float(row[metric]) for row in rows]
            result[f"mean_{metric}"] = mean(values)
            result[f"median_{metric}"] = float(statistics.median(values))
            result[f"worst_seed_{metric}"] = min(values) if metric not in {"timeout_perturbed", "collision_perturbed"} else max(values)
            result[f"sample_sd_{metric}"] = sample_sd(values)
        output.append(result)
    return output


def paired_deltas(seed_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lookup = {(row["method"], int(row["train_seed"])): row for row in seed_rows}
    rows = []
    for seed in SEEDS:
        utr, drtp = lookup[("UTR", seed)], lookup[("DRTP", seed)]
        rows.append({
            "train_seed": seed,
            "delta_J_nominal": float(drtp["J_nominal"]) - float(utr["J_nominal"]),
            "delta_J_perturbed": float(drtp["J_perturbed"]) - float(utr["J_perturbed"]),
            "delta_J_perturbed_worst_condition": float(drtp["J_perturbed_worst_condition"]) - float(utr["J_perturbed_worst_condition"]),
            "delta_success_perturbed": float(drtp["success_perturbed"]) - float(utr["success_perturbed"]),
            "delta_timeout_perturbed": float(drtp["timeout_perturbed"]) - float(utr["timeout_perturbed"]),
            "delta_collision_perturbed": float(drtp["collision_perturbed"]) - float(utr["collision_perturbed"]),
        })
    return rows


def plot_figure(seed_rows: list[dict[str, Any]], report_dir: Path) -> None:
    mpl.rcParams.update({
        "font.family": ["Arial", "DejaVu Sans", "sans-serif"],
        "font.size": 7,
        "axes.labelsize": 7,
        "axes.titlesize": 8,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "axes.spines.top": False,
        "axes.spines.right": False,
    })
    lookup = {(row["method"], int(row["train_seed"])): row for row in seed_rows}
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.55), sharex=True)
    panels = (
        ("J_perturbed", "Perturbed return", "higher is better"),
        ("timeout_perturbed", "Perturbed timeout rate", "lower is better"),
    )
    colors = {"UTR": "#737373", "DRTP": "#0072B2"}
    x = list(range(len(SEEDS)))
    for axis, (metric, ylabel, direction) in zip(axes, panels):
        utr_values = [float(lookup[("UTR", seed)][metric]) for seed in SEEDS]
        drtp_values = [float(lookup[("DRTP", seed)][metric]) for seed in SEEDS]
        for index, (utr, drtp) in enumerate(zip(utr_values, drtp_values)):
            axis.plot((index, index), (utr, drtp), color="#C7C7C7", lw=.8, zorder=1)
        axis.scatter(x, utr_values, s=30, color=colors["UTR"], label="UTR", zorder=3)
        axis.scatter(x, drtp_values, s=30, color=colors["DRTP"], label="DRTP", zorder=3)
        axis.set_xticks(x, [str(seed) for seed in SEEDS])
        axis.set_xlabel("Training seed")
        axis.set_ylabel(ylabel)
        axis.set_title(direction)
        axis.grid(axis="y", color="#D9D9D9", lw=.5)
    axes[0].legend(loc="best", frameon=False)
    fig.text(.5, -.03, "Fixed 10M endpoint; each paired line shares one frozen training seed. Results are reported at the training-seed level.", ha="center", va="top", fontsize=6.5, color="#404040")
    fig.subplots_adjust(left=.10, right=.99, top=.88, bottom=.25, wspace=.34)
    stem = report_dir / "Fig6_6UAV_cross_scale_paired_endpoint"
    fig.savefig(stem.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(stem.with_suffix(".tiff"), dpi=600, pil_kwargs={"compression": "tiff_lzw"}, bbox_inches="tight")
    fig.savefig(stem.with_suffix(".png"), dpi=300, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("explicit --execute is required")
    complete_path = args.output_root / "DRTP_6UAV_CROSS_SCALE_COMPLETE.json"
    if not complete_path.is_file():
        raise FileNotFoundError("6-UAV complete marker is absent; do not summarize an incomplete run")
    complete = json.loads(complete_path.read_text(encoding="utf-8"))
    if complete.get("status") != "DRTP_6UAV_CROSS_SCALE_COMPLETE" or not complete.get("endpoint_evaluation_completed"):
        raise RuntimeError("6-UAV run is not a completed fixed endpoint")
    if args.report_dir.exists():
        raise FileExistsError(f"refusing to overwrite report directory: {args.report_dir}")
    seed_rows = [load_seed_endpoint(args.output_root, arm, seed) for arm in ARMS for seed in SEEDS]
    summary_rows = cohort_summary(seed_rows)
    paired_rows = paired_deltas(seed_rows)
    args.report_dir.mkdir(parents=True)
    write_csv(args.report_dir / "DRTP_6UAV_PER_SEED_ENDPOINTS.csv", seed_rows)
    write_csv(args.report_dir / "DRTP_6UAV_COHORT_SUMMARY.csv", summary_rows)
    write_csv(args.report_dir / "DRTP_6UAV_PAIRED_DELTAS.csv", paired_rows)
    plot_figure(seed_rows, args.report_dir)
    report = {
        "protocol": "DRTP-6UAV-CROSS-SCALE-SUBMISSION-FINALIZER-V1",
        "verdict": "DRTP_6UAV_CROSS_SCALE_FINALIZED",
        "independent_unit": "training_seed",
        "training_seeds": list(SEEDS),
        "endpoint": "fixed_10m",
        "methods": ["UTR", "DRTP"],
        "source_complete_marker": str(complete_path),
        "training_started": False,
        "evaluation_started": False,
        "automatic_algorithm_revision": False,
    }
    (args.report_dir / "DRTP_6UAV_FINALIZATION.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (args.report_dir / "DRTP_6UAV_FINALIZATION.md").write_text(
        "# DRTP 6-UAV cross-scale finalization\n\n"
        "`DRTP_6UAV_CROSS_SCALE_FINALIZED`\n\n"
        "This post-processing step reads only completed fixed-endpoint artifacts. It reports mean, median, training-seed lower tail, success, timeout, collision, and paired UTR-versus-DRTP differences. It does not train, evaluate a checkpoint, alter an algorithm, or promote a run.\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
