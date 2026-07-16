from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "results" / "intercept_3d_node_failure_curriculum_formal_node_failure_eval" / "episode_metrics.csv"
METRICS = (
    "post_failure_chain_recovered",
    "post_failure_chain_recovery_steps",
    "chain_closed_during_failure_rate",
    "tracking_during_failure_rate",
    "connectivity_during_failure",
    "first_chain_close_step",
    "steps",
    "success",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze node-failure kill-chain recovery metrics for the 3DOF topology-curriculum experiment."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out-csv", type=Path, default=ROOT / "results" / "intercept_3d_node_failure_recovery_summary.csv")
    parser.add_argument("--summary-md", type=Path, default=ROOT / "docs" / "intercept_3d_node_failure_recovery_summary.md")
    parser.add_argument("--bootstrap-samples", type=int, default=10_000)
    parser.add_argument("--bootstrap-seed", type=int, default=20_260_716)
    return parser.parse_args()


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def paired_deltas(rows: list[dict[str, str]]) -> dict[str, dict[str, np.ndarray]]:
    pairs: dict[tuple[str, int, int], dict[str, dict[str, str]]] = defaultdict(dict)
    for row in rows:
        pairs[(row["scenario"], int(row["train_seed"]), int(row["episode"]))][row["graph_encoder"]] = row
    out: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for (scenario, _seed, _episode), graphs in pairs.items():
        if "single" not in graphs or "multi_relation" not in graphs:
            continue
        single, multi = graphs["single"], graphs["multi_relation"]
        for metric in METRICS:
            out[scenario][metric].append(float(multi[metric]) - float(single[metric]))
    return {scenario: {metric: np.asarray(values, dtype=np.float64) for metric, values in metrics.items()} for scenario, metrics in out.items()}


def graph_means(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, float]]:
    buckets: dict[tuple[str, str], dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        key = (row["scenario"], row["graph_encoder"])
        for metric in METRICS:
            buckets[key][metric].append(float(row[metric]))
    return {key: {metric: float(np.mean(values)) for metric, values in metrics.items()} for key, metrics in buckets.items()}


def bootstrap(values: np.ndarray, rng: np.random.Generator, samples: int) -> tuple[float, float, float, float]:
    if values.size == 0:
        return float("nan"), float("nan"), float("nan"), float("nan")
    indices = rng.integers(0, values.size, size=(samples, values.size))
    means = np.mean(values[indices], axis=1)
    mean = float(np.mean(values))
    lo = float(np.percentile(means, 2.5))
    hi = float(np.percentile(means, 97.5))
    p_value = min(1.0, 2.0 * min(float(np.mean(means <= 0.0)), float(np.mean(means >= 0.0))))
    return mean, lo, hi, p_value


def summarize(rows: list[dict[str, str]], samples: int, seed: int) -> list[dict[str, str]]:
    deltas = paired_deltas(rows)
    means = graph_means(rows)
    rng = np.random.default_rng(seed)
    output: list[dict[str, str]] = []
    for scenario in sorted(deltas):
        row = {"scenario": scenario, "n_paired_episodes": str(len(deltas[scenario]["success"]))}
        for metric in METRICS:
            single_mean = means[(scenario, "single")][metric]
            multi_mean = means[(scenario, "multi_relation")][metric]
            delta_mean, ci_low, ci_high, p_value = bootstrap(deltas[scenario][metric], rng, samples)
            row[f"single_{metric}_mean"] = f"{single_mean:.6g}"
            row[f"multi_{metric}_mean"] = f"{multi_mean:.6g}"
            row[f"delta_{metric}_mean"] = f"{delta_mean:.6g}"
            row[f"delta_{metric}_ci_low"] = f"{ci_low:.6g}"
            row[f"delta_{metric}_ci_high"] = f"{ci_high:.6g}"
            row[f"delta_{metric}_p_bootstrap"] = f"{p_value:.6g}"
        output.append(row)
    return output


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
        "# 3DOF Node-Failure Recovery Summary",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Input:",
        "",
        "```text",
        str(args.input),
        "```",
        "",
        "## Recovery Metrics",
        "",
        "| Scenario | Pairs | Recovered Delta | Recovery Steps Delta | Chain-During-Failure Delta | Connectivity-During-Failure Delta |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['scenario']} | {row['n_paired_episodes']} | "
            f"{float(row['delta_post_failure_chain_recovered_mean']):+.3f} "
            f"[{float(row['delta_post_failure_chain_recovered_ci_low']):+.3f}, {float(row['delta_post_failure_chain_recovered_ci_high']):+.3f}] | "
            f"{float(row['delta_post_failure_chain_recovery_steps_mean']):+.1f} "
            f"[{float(row['delta_post_failure_chain_recovery_steps_ci_low']):+.1f}, {float(row['delta_post_failure_chain_recovery_steps_ci_high']):+.1f}] | "
            f"{float(row['delta_chain_closed_during_failure_rate_mean']):+.3f} "
            f"[{float(row['delta_chain_closed_during_failure_rate_ci_low']):+.3f}, {float(row['delta_chain_closed_during_failure_rate_ci_high']):+.3f}] | "
            f"{float(row['delta_connectivity_during_failure_mean']):+.3f} "
            f"[{float(row['delta_connectivity_during_failure_ci_low']):+.3f}, {float(row['delta_connectivity_during_failure_ci_high']):+.3f}] |"
        )
    lines.extend(
        [
            "",
            "## Use Boundary",
            "",
            "```text",
            "Positive recovered/chain/connectivity deltas and negative recovery-step deltas favor the multi-relation graph.",
            "Recovery-step values are censored by episode termination when a post-failure chain closure is not observed.",
            "```",
            "",
        ]
    )
    out_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    rows = summarize(read_rows(args.input), args.bootstrap_samples, args.bootstrap_seed)
    write_csv(rows, args.out_csv)
    write_summary(rows, args.summary_md, args)
    print(args.out_csv)
    print(args.summary_md)
    print(f"scenarios: {len(rows)}")


if __name__ == "__main__":
    main()
