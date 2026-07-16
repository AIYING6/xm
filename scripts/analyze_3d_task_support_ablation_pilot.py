from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FULL = ROOT / "results" / "intercept_3d_task_support_full_seed0_matched_eval" / "episode_metrics.csv"
DEFAULT_ABLATED = (
    ROOT / "results" / "intercept_3d_no_task_support_topology_seed0_pilot" / "robustness_eval" / "episode_metrics.csv"
)
DEFAULT_OUT_CSV = ROOT / "results" / "intercept_3d_task_support_ablation_seed0_pilot_summary.csv"
DEFAULT_OUT_MD = ROOT / "docs" / "intercept_3d_task_support_ablation_seed0_pilot_summary.md"

METRICS = (
    "success",
    "chain_closed",
    "tracking_rate",
    "comm_connectivity",
    "mean_message_age",
    "timeout",
    "steps",
    "post_failure_chain_recovered",
    "post_failure_chain_recovery_steps",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare full and no-task-support 3DOF pilot evaluations.")
    parser.add_argument("--full-csv", type=Path, default=DEFAULT_FULL)
    parser.add_argument("--ablated-csv", type=Path, default=DEFAULT_ABLATED)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT_CSV)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    return parser.parse_args()


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def means(rows: list[dict[str, str]]) -> dict[str, dict[str, float]]:
    buckets: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        for metric in METRICS:
            buckets[row["scenario"]][metric].append(float(row[metric]))
    return {scenario: {metric: float(np.mean(values)) for metric, values in metrics.items()} for scenario, metrics in buckets.items()}


def paired_deltas(full_rows: list[dict[str, str]], ablated_rows: list[dict[str, str]]) -> dict[str, dict[str, float]]:
    full_by_key = {(row["scenario"], row["seed"], row["episode"]): row for row in full_rows}
    ablated_by_key = {(row["scenario"], row["seed"], row["episode"]): row for row in ablated_rows}
    buckets: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for key, full in full_by_key.items():
        ablated = ablated_by_key.get(key)
        if ablated is None:
            continue
        scenario = key[0]
        for metric in METRICS:
            buckets[scenario][metric].append(float(full[metric]) - float(ablated[metric]))
    return {scenario: {metric: float(np.mean(values)) for metric, values in metrics.items()} for scenario, metrics in buckets.items()}


def build_rows(full_rows: list[dict[str, str]], ablated_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    full_means = means(full_rows)
    ablated_means = means(ablated_rows)
    deltas = paired_deltas(full_rows, ablated_rows)
    rows: list[dict[str, str]] = []
    for scenario in sorted(set(full_means) & set(ablated_means)):
        row = {
            "scenario": scenario,
            "episodes": str(sum(1 for item in full_rows if item["scenario"] == scenario)),
        }
        for metric in METRICS:
            row[f"full_{metric}"] = f"{full_means[scenario][metric]:.6g}"
            row[f"no_task_support_{metric}"] = f"{ablated_means[scenario][metric]:.6g}"
            row[f"full_minus_no_task_support_{metric}"] = f"{deltas[scenario][metric]:.6g}"
        rows.append(row)
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise RuntimeError("No paired ablation rows were generated")
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_md(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 3DOF Task-Support Ablation Pilot",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "This is a one-seed diagnostic comparison. It is useful for deciding whether the task-support relation deserves formal ablation budget, but it is not a paper-level statistical result.",
        "",
        "| Scenario | Episodes | Success full/no-task | Success delta | Recovery full/no-task | Recovery delta | Steps full/no-task | Steps delta |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['scenario']} | {row['episodes']} | "
            f"{float(row['full_success']):.3f} / {float(row['no_task_support_success']):.3f} | "
            f"{float(row['full_minus_no_task_support_success']):+.3f} | "
            f"{float(row['full_post_failure_chain_recovered']):.3f} / {float(row['no_task_support_post_failure_chain_recovered']):.3f} | "
            f"{float(row['full_minus_no_task_support_post_failure_chain_recovered']):+.3f} | "
            f"{float(row['full_steps']):.1f} / {float(row['no_task_support_steps']):.1f} | "
            f"{float(row['full_minus_no_task_support_steps']):+.1f} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The pilot supports keeping `no_task_support` as the first formal ablation.",
            "- The current seed0 gap is large enough to justify spending formal budget, but it must be repeated with matched seeds and at least 30 evaluation episodes per scenario before being used as a manuscript claim.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    rows = build_rows(read_rows(args.full_csv), read_rows(args.ablated_csv))
    write_csv(args.out_csv, rows)
    write_md(args.out_md, rows)
    print(args.out_csv)
    print(args.out_md)


if __name__ == "__main__":
    main()
