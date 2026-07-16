from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUTS = (
    ROOT / "results" / "intercept_3d_node_failure_curriculum_formal_node_failure_eval" / "episode_metrics.csv",
    ROOT / "results" / "intercept_3d_node_failure_curriculum_formal_selected_eval" / "episode_metrics.csv",
)
METRICS = ("success", "chain_closed", "tracking_rate", "comm_connectivity", "mean_message_age", "timeout", "steps")
BOOTSTRAP_METRICS = ("success", "timeout", "steps", "tracking_rate", "comm_connectivity")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize formal 3DOF topology-curriculum robustness evaluations as multi-relation minus single-graph deltas."
    )
    parser.add_argument("--inputs", nargs="+", type=Path, default=DEFAULT_INPUTS)
    parser.add_argument("--out-csv", type=Path, default=ROOT / "results" / "intercept_3d_topology_curriculum_formal_summary.csv")
    parser.add_argument("--summary-md", type=Path, default=ROOT / "docs" / "intercept_3d_topology_curriculum_formal_summary.md")
    parser.add_argument("--bootstrap-samples", type=int, default=10_000)
    parser.add_argument("--bootstrap-seed", type=int, default=20_260_716)
    return parser.parse_args()


def read_rows(paths: list[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(path)
        with path.open("r", encoding="utf-8", newline="") as f:
            rows.extend(csv.DictReader(f))
    return rows


def seed_metric_means(rows: list[dict[str, str]]) -> dict[tuple[str, str, int], dict[str, float]]:
    buckets: dict[tuple[str, str, int], dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        key = (row["scenario"], row["graph_encoder"], int(row["train_seed"]))
        for metric in METRICS:
            buckets[key][metric].append(float(row[metric]))
    return {key: {metric: float(np.mean(values)) for metric, values in metrics.items()} for key, metrics in buckets.items()}


def paired_episode_deltas(rows: list[dict[str, str]]) -> dict[str, dict[str, np.ndarray]]:
    buckets: dict[tuple[str, int, int], dict[str, dict[str, str]]] = defaultdict(dict)
    for row in rows:
        key = (row["scenario"], int(row["train_seed"]), int(row["episode"]))
        buckets[key][row["graph_encoder"]] = row

    deltas: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for (scenario, _seed, _episode), graphs in buckets.items():
        if "single" not in graphs or "multi_relation" not in graphs:
            continue
        single = graphs["single"]
        multi = graphs["multi_relation"]
        for metric in BOOTSTRAP_METRICS:
            deltas[scenario][metric].append(float(multi[metric]) - float(single[metric]))
    return {
        scenario: {metric: np.asarray(values, dtype=np.float64) for metric, values in metrics.items()}
        for scenario, metrics in deltas.items()
    }


def bootstrap_mean_ci(values: np.ndarray, rng: np.random.Generator, samples: int) -> tuple[float, float, float]:
    if values.size == 0:
        return float("nan"), float("nan"), float("nan")
    if samples <= 0:
        mean = float(np.mean(values))
        return mean, float("nan"), float("nan")
    indices = rng.integers(0, values.size, size=(samples, values.size))
    means = np.mean(values[indices], axis=1)
    return float(np.mean(values)), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def bootstrap_two_sided_p(values: np.ndarray, rng: np.random.Generator, samples: int) -> float:
    if values.size == 0 or samples <= 0:
        return float("nan")
    indices = rng.integers(0, values.size, size=(samples, values.size))
    means = np.mean(values[indices], axis=1)
    p_le = float(np.mean(means <= 0.0))
    p_ge = float(np.mean(means >= 0.0))
    return min(1.0, 2.0 * min(p_le, p_ge))


def summarize(rows: list[dict[str, str]], samples: int, bootstrap_seed: int) -> list[dict[str, str]]:
    seed_means = seed_metric_means(rows)
    episode_deltas = paired_episode_deltas(rows)
    rng = np.random.default_rng(bootstrap_seed)
    scenarios = sorted({key[0] for key in seed_means})
    out: list[dict[str, str]] = []
    for scenario in scenarios:
        single_keys = sorted(key for key in seed_means if key[0] == scenario and key[1] == "single")
        multi_keys = sorted(key for key in seed_means if key[0] == scenario and key[1] == "multi_relation")
        if len(single_keys) != len(multi_keys):
            raise ValueError(f"unmatched seed count for scenario {scenario}: single={len(single_keys)} multi={len(multi_keys)}")
        row: dict[str, str] = {"scenario": scenario, "n_seeds": str(len(single_keys))}
        pair_count = 0
        if scenario in episode_deltas and "success" in episode_deltas[scenario]:
            pair_count = int(episode_deltas[scenario]["success"].size)
        row["n_paired_episodes"] = str(pair_count)
        for metric in METRICS:
            single = np.asarray([seed_means[key][metric] for key in single_keys], dtype=np.float64)
            multi = np.asarray([seed_means[key][metric] for key in multi_keys], dtype=np.float64)
            delta = multi - single
            row[f"single_{metric}_mean"] = f"{float(np.mean(single)):.6g}"
            row[f"multi_{metric}_mean"] = f"{float(np.mean(multi)):.6g}"
            row[f"delta_{metric}_mean"] = f"{float(np.mean(delta)):.6g}"
            row[f"delta_{metric}_std"] = f"{float(np.std(delta, ddof=0)):.6g}"
            if metric in BOOTSTRAP_METRICS and scenario in episode_deltas:
                mean, lo, hi = bootstrap_mean_ci(episode_deltas[scenario][metric], rng, samples)
                p_value = bootstrap_two_sided_p(episode_deltas[scenario][metric], rng, samples)
                row[f"paired_delta_{metric}_mean"] = f"{mean:.6g}"
                row[f"paired_delta_{metric}_ci_low"] = f"{lo:.6g}"
                row[f"paired_delta_{metric}_ci_high"] = f"{hi:.6g}"
                row[f"paired_delta_{metric}_p_bootstrap"] = f"{p_value:.6g}"
        out.append(row)
    return out


def write_csv(rows: list[dict[str, str]], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys())
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_summary(rows: list[dict[str, str]], out_md: Path, args: argparse.Namespace) -> None:
    out_md.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 3DOF Topology Curriculum Formal Summary",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Inputs:",
        "",
        "```text",
        *[str(path) for path in args.inputs],
        "```",
        "",
        "## Multi-Relation Minus Single-Graph",
        "",
        "| Scenario | Seeds | Pairs | Success Delta | Success 95% CI | p_boot | Timeout Delta | Steps Delta | Tracking Delta |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['scenario']} | {row['n_seeds']} | {row['n_paired_episodes']} | "
            f"{float(row['delta_success_mean']):+.3f} | "
            f"[{float(row['paired_delta_success_ci_low']):+.3f}, {float(row['paired_delta_success_ci_high']):+.3f}] | "
            f"{float(row['paired_delta_success_p_bootstrap']):.3f} | "
            f"{float(row['delta_timeout_mean']):+.3f} | {float(row['delta_steps_mean']):+.1f} | "
            f"{float(row['delta_tracking_rate_mean']):+.3f} |"
        )
    lines.extend(
        [
            "",
            "## Step-Time Diagnostics",
            "",
            "| Scenario | Steps Delta | Steps 95% CI | Timeout Delta | Timeout 95% CI |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['scenario']} | {float(row['delta_steps_mean']):+.1f} | "
            f"[{float(row['paired_delta_steps_ci_low']):+.1f}, {float(row['paired_delta_steps_ci_high']):+.1f}] | "
            f"{float(row['delta_timeout_mean']):+.3f} | "
            f"[{float(row['paired_delta_timeout_ci_low']):+.3f}, {float(row['paired_delta_timeout_ci_high']):+.3f}] |"
        )
    lines.extend(
        [
            "",
            "## Use Boundary",
            "",
            "```text",
            "Positive success delta and negative timeout/steps delta favor the multi-relation graph.",
            "Bootstrap intervals resample paired evaluation episodes with replacement; they are useful diagnostics but do not replace a larger seed-level significance study.",
            "```",
            "",
        ]
    )
    out_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    rows = summarize(read_rows(args.inputs), args.bootstrap_samples, args.bootstrap_seed)
    write_csv(rows, args.out_csv)
    write_summary(rows, args.summary_md, args)
    print(args.out_csv)
    print(args.summary_md)
    print(f"scenarios: {len(rows)}")


if __name__ == "__main__":
    main()
