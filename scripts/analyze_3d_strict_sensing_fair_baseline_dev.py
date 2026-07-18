from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
METRICS = (
    "success_mean",
    "post_failure_chain_recovered_mean",
    "post_failure_chain_recovery_steps_mean",
    "tracking_during_failure_rate_mean",
    "connectivity_during_failure_mean",
    "steps_mean",
    "timeout_mean",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize the strict-sensing fair-baseline development protocol."
    )
    parser.add_argument(
        "--result-dir",
        type=Path,
        default=ROOT / "results" / "intercept_3d_strict_sensing_fair_baselines_dev2",
    )
    parser.add_argument(
        "--out-csv",
        type=Path,
        default=ROOT / "results" / "intercept_3d_strict_sensing_fair_baseline_dev_summary.csv",
    )
    parser.add_argument(
        "--summary-md",
        type=Path,
        default=ROOT / "docs" / "intercept_3d_strict_sensing_fair_baseline_dev_summary.md",
    )
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def to_float(value: str) -> float:
    if value == "inf":
        return float("inf")
    return float(value)


def mean_std(values: list[float]) -> tuple[float, float]:
    finite = [value for value in values if np.isfinite(value)]
    if not finite:
        return float("inf"), float("nan")
    return float(np.mean(finite)), float(np.std(finite, ddof=1)) if len(finite) > 1 else 0.0


def summarize_split(rows: list[dict[str, str]], split: str) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["scenario"], row["graph_encoder"])].append(row)

    summary: list[dict[str, str]] = []
    for (scenario, graph_encoder), part in sorted(grouped.items()):
        out = {
            "split": split,
            "scenario": scenario,
            "graph_encoder": graph_encoder,
            "n_training_seeds": str(len({row["train_seed"] for row in part})),
            "checkpoint_updates": ",".join(sorted({row["checkpoint_update"] for row in part}, key=int)),
        }
        for metric in METRICS:
            mean, std = mean_std([to_float(row[metric]) for row in part])
            out[f"{metric}_mean"] = "inf" if not np.isfinite(mean) else f"{mean:.6g}"
            out[f"{metric}_std"] = "nan" if np.isnan(std) else f"{std:.6g}"
        summary.append(out)
    return summary


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("No summary rows to write.")
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def fmt_rate(value: str) -> str:
    if value == "inf":
        return "inf"
    return f"{100.0 * float(value):.1f}%"


def fmt_num(value: str) -> str:
    if value in {"inf", "nan"}:
        return value
    return f"{float(value):.2f}"


def write_markdown(path: Path, rows: list[dict[str, str]], result_dir: Path) -> None:
    lines = [
        "# Strict-Sensing Fair Baseline Development Summary",
        "",
        f"Result directory: `{result_dir.as_posix()}`",
        "",
        "This is a development-budget diagnostic, not a paper result. Its purpose is to check whether `no_graph`, `single`, and `multi_relation` can be trained and evaluated under the same strict-sensing protocol before launching a five-seed formal run.",
        "",
        "| Split | Scenario | Method | Seeds | Success | Recovery | Recovery steps | Tracking | Connectivity | Timeout |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["split"],
                    row["scenario"],
                    row["graph_encoder"],
                    row["n_training_seeds"],
                    fmt_rate(row["success_mean_mean"]),
                    fmt_rate(row["post_failure_chain_recovered_mean_mean"]),
                    fmt_num(row["post_failure_chain_recovery_steps_mean_mean"]),
                    fmt_rate(row["tracking_during_failure_rate_mean_mean"]),
                    fmt_rate(row["connectivity_during_failure_mean_mean"]),
                    fmt_rate(row["timeout_mean_mean"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Decision Rule",
            "",
            "- If all methods have zero recovery, increase BC budget before increasing PPO updates.",
            "- If `no_graph` is clearly worse and `single`/`multi_relation` are stable, expand to a longer 300-update diagnostic.",
            "- If `single` catches `multi_relation`, keep the result and use it to tune scenario difficulty rather than forcing the claim.",
            "- Do not tune on the final test split.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    sweep_dir = args.result_dir / "checkpoint_sweep"
    rows = []
    for split in ("validation", "test"):
        rows.extend(summarize_split(read_csv(sweep_dir / f"{split}_checkpoint_summary.csv"), split))
    write_csv(args.out_csv, rows)
    write_markdown(args.summary_md, rows, args.result_dir)
    print(args.out_csv)
    print(args.summary_md)


if __name__ == "__main__":
    main()
