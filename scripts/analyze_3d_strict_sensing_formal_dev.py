from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_CSV = ROOT / "results" / "intercept_3d_strict_sensing_formal_dev_summary.csv"
DEFAULT_OUT_MD = ROOT / "docs" / "intercept_3d_strict_sensing_formal_dev_summary.md"


METRIC_KEYS = (
    "success_mean",
    "post_failure_chain_recovered_mean",
    "post_failure_chain_recovery_steps_mean",
    "tracking_during_failure_rate_mean",
    "connectivity_during_failure_mean",
    "chain_closed_during_failure_rate_mean",
    "steps_mean",
    "timeout_mean",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize the strict-sensing formal development run.")
    parser.add_argument("--seeds", nargs="+", type=int, default=(0, 1, 2))
    parser.add_argument(
        "--root-template",
        type=str,
        default="results/intercept_3d_strict_sensing_formal_seed{seed}_dev/checkpoint_sweep",
    )
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT_CSV)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def f(row: dict[str, str], key: str) -> float:
    return float(row[key])


def collect_rows(args: argparse.Namespace) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    test_rows: list[dict[str, str]] = []
    selected_rows: list[dict[str, str]] = []
    for seed in args.seeds:
        root = ROOT / args.root_template.format(seed=seed)
        test_rows.extend(read_csv(root / "test_checkpoint_summary.csv"))
        selected_rows.extend(read_csv(root / "validation_selected_checkpoints.csv"))
    return test_rows, selected_rows


def mean_std(values: list[float]) -> tuple[float, float]:
    arr = np.asarray(values, dtype=float)
    if len(arr) == 0:
        return float("nan"), float("nan")
    if len(arr) == 1:
        return float(arr[0]), 0.0
    return float(np.mean(arr)), float(np.std(arr, ddof=1))


def summarize_by_graph(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for graph in ("single", "multi_relation"):
        part = [row for row in rows if row["graph_encoder"] == graph]
        if not part:
            continue
        summary = {
            "row_type": "graph_summary",
            "graph_encoder": graph,
            "train_seed": "all",
            "selected_update": "",
            "selected_checkpoint": "",
            "n_seeds": str(len(part)),
        }
        for key in METRIC_KEYS:
            mean, std = mean_std([f(row, key) for row in part])
            summary[f"{key}_mean"] = f"{mean:.6g}"
            summary[f"{key}_std"] = f"{std:.6g}"
        out.append(summary)
    return out


def seed_rows(test_rows: list[dict[str, str]], selected_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    selected_by_key = {
        (row["graph_encoder"], row["train_seed"]): row
        for row in selected_rows
    }
    out: list[dict[str, str]] = []
    for row in sorted(test_rows, key=lambda r: (int(r["train_seed"]), r["graph_encoder"])):
        selected = selected_by_key[(row["graph_encoder"], row["train_seed"])]
        out_row = {
            "row_type": "seed_result",
            "graph_encoder": row["graph_encoder"],
            "train_seed": row["train_seed"],
            "selected_update": selected["selected_checkpoint_update"],
            "selected_checkpoint": selected["selected_checkpoint"],
            "n_seeds": "1",
        }
        for key in METRIC_KEYS:
            out_row[f"{key}_mean"] = row[key]
            out_row[f"{key}_std"] = "0"
        out.append(out_row)
    return out


def paired_delta_rows(test_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    by_seed: dict[str, dict[str, dict[str, str]]] = {}
    for row in test_rows:
        by_seed.setdefault(row["train_seed"], {})[row["graph_encoder"]] = row
    out: list[dict[str, str]] = []
    delta_by_metric: dict[str, list[float]] = {key: [] for key in METRIC_KEYS}
    for seed, parts in sorted(by_seed.items(), key=lambda item: int(item[0])):
        if "single" not in parts or "multi_relation" not in parts:
            continue
        row = {
            "row_type": "paired_seed_delta_multi_minus_single",
            "graph_encoder": "multi_minus_single",
            "train_seed": seed,
            "selected_update": "",
            "selected_checkpoint": "",
            "n_seeds": "1",
        }
        for key in METRIC_KEYS:
            delta = f(parts["multi_relation"], key) - f(parts["single"], key)
            delta_by_metric[key].append(delta)
            row[f"{key}_mean"] = f"{delta:.6g}"
            row[f"{key}_std"] = "0"
        out.append(row)
    summary = {
        "row_type": "paired_delta_summary_multi_minus_single",
        "graph_encoder": "multi_minus_single",
        "train_seed": "all",
        "selected_update": "",
        "selected_checkpoint": "",
        "n_seeds": str(len(out)),
    }
    for key, values in delta_by_metric.items():
        mean, std = mean_std(values)
        summary[f"{key}_mean"] = f"{mean:.6g}"
        summary[f"{key}_std"] = f"{std:.6g}"
    out.append(summary)
    return out


def all_columns(rows: list[dict[str, str]]) -> list[str]:
    columns = ["row_type", "graph_encoder", "train_seed", "selected_update", "selected_checkpoint", "n_seeds"]
    for key in METRIC_KEYS:
        columns.extend([f"{key}_mean", f"{key}_std"])
    return columns


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = all_columns(rows)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def pct(value: str) -> str:
    return f"{100.0 * float(value):.1f}"


def write_md(path: Path, rows: list[dict[str, str]], seeds: list[int], out_csv: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    summaries = {row["graph_encoder"]: row for row in rows if row["row_type"] == "graph_summary"}
    delta_summary = next(row for row in rows if row["row_type"] == "paired_delta_summary_multi_minus_single")
    seed_results = [row for row in rows if row["row_type"] == "seed_result"]
    seed_deltas = [row for row in rows if row["row_type"] == "paired_seed_delta_multi_minus_single"]
    lines = [
        "# Strict-Sensing Formal Development Summary",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "This is a three-seed development result for the formal strict-sensing relay-failure protocol. It uses validation-selected checkpoints and disjoint test episodes. It is stronger than the earlier 10-update pilot, but it is still a development result until the final seed budget and baseline set are frozen.",
        "",
        "## Protocol",
        "",
        "```text",
        f"seeds = {seeds}",
        "scenario = relay_failure",
        "strict_target_sensing = True",
        "validation episodes per seed/checkpoint = 50",
        "test episodes per selected seed/checkpoint = 100",
        "checkpoint snapshots = every 10 updates up to 120",
        "checkpoint selection = validation recovery/success/recovery-step score",
        "```",
        "",
        "## Test Summary",
        "",
        "| Graph | Seeds | Recovery % mean/std | Success % mean/std | Recovery steps mean/std | Timeout % mean/std |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for graph in ("single", "multi_relation"):
        row = summaries[graph]
        lines.append(
            f"| `{graph}` | {row['n_seeds']} | "
            f"{pct(row['post_failure_chain_recovered_mean_mean'])} / {pct(row['post_failure_chain_recovered_mean_std'])} | "
            f"{pct(row['success_mean_mean'])} / {pct(row['success_mean_std'])} | "
            f"{float(row['post_failure_chain_recovery_steps_mean_mean']):.2f} / {float(row['post_failure_chain_recovery_steps_mean_std']):.2f} | "
            f"{pct(row['timeout_mean_mean'])} / {pct(row['timeout_mean_std'])} |"
        )
    lines.extend(
        [
            "",
            "## Paired Delta",
            "",
            "Positive recovery/success deltas favor the multi-relation model. Negative step/timeout deltas favor the multi-relation model.",
            "",
            "| Metric | Mean delta | Std over seeds |",
            "| --- | ---: | ---: |",
            f"| Recovery probability | {100.0 * float(delta_summary['post_failure_chain_recovered_mean_mean']):+.1f} pp | {100.0 * float(delta_summary['post_failure_chain_recovered_mean_std']):.1f} pp |",
            f"| Success probability | {100.0 * float(delta_summary['success_mean_mean']):+.1f} pp | {100.0 * float(delta_summary['success_mean_std']):.1f} pp |",
            f"| Recovery steps | {float(delta_summary['post_failure_chain_recovery_steps_mean_mean']):+.2f} | {float(delta_summary['post_failure_chain_recovery_steps_mean_std']):.2f} |",
            f"| Timeout probability | {100.0 * float(delta_summary['timeout_mean_mean']):+.1f} pp | {100.0 * float(delta_summary['timeout_mean_std']):.1f} pp |",
            "",
            "## Selected Checkpoints and Seed-Level Test Results",
            "",
            "| Seed | Graph | Update | Recovery % | Success % | Recovery steps | Timeout % |",
            "| ---: | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in seed_results:
        lines.append(
            f"| {row['train_seed']} | `{row['graph_encoder']}` | {row['selected_update']} | "
            f"{pct(row['post_failure_chain_recovered_mean_mean'])} | "
            f"{pct(row['success_mean_mean'])} | "
            f"{float(row['post_failure_chain_recovery_steps_mean_mean']):.2f} | "
            f"{pct(row['timeout_mean_mean'])} |"
        )
    lines.extend(
        [
            "",
            "## Seed-Level Paired Deltas",
            "",
            "| Seed | Recovery delta pp | Success delta pp | Recovery-step delta | Timeout delta pp |",
            "| ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in seed_deltas:
        lines.append(
            f"| {row['train_seed']} | "
            f"{100.0 * float(row['post_failure_chain_recovered_mean_mean']):+.1f} | "
            f"{100.0 * float(row['success_mean_mean']):+.1f} | "
            f"{float(row['post_failure_chain_recovery_steps_mean_mean']):+.2f} | "
            f"{100.0 * float(row['timeout_mean_mean']):+.1f} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- This development run supports continuing the strict-sensing relay-failure line.",
            "- The validation-selected multi-relation checkpoints are consistently strong across seeds.",
            "- The single-graph baseline can also solve some seeds after validation selection, so the final paper still needs five seeds, fair MAPPO/GAT baselines, and seed-aware statistics before making a final Q2-level claim.",
            "",
            "## Files",
            "",
            f"- `{out_csv.relative_to(ROOT).as_posix()}`",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    test_rows, selected_rows = collect_rows(args)
    rows = [
        *seed_rows(test_rows, selected_rows),
        *summarize_by_graph(test_rows),
        *paired_delta_rows(test_rows),
    ]
    write_csv(args.out_csv, rows)
    write_md(args.out_md, rows, list(args.seeds), args.out_csv)
    print(args.out_csv)
    print(args.out_md)


if __name__ == "__main__":
    main()
