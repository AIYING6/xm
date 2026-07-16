from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


DEFAULT_LEARNED = ROOT / "results" / "intercept_3d_node_failure_curriculum_formal_node_failure_eval" / "episode_metrics.csv"
DEFAULT_GEOMETRIC = ROOT / "results" / "intercept_3d_geometric_node_failure_eval" / "episode_metrics.csv"
METHOD_ORDER = (
    "Oracle geometric pursuit",
    "Single-graph MAPPO",
    "EA-RG-MAPPO-S",
)
METRICS = (
    "success",
    "post_failure_chain_recovered",
    "post_failure_chain_recovery_steps",
    "tracking_during_failure_rate",
    "connectivity_during_failure",
    "steps",
    "timeout",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a compact node-failure baseline table from geometric, single-graph, and multi-relation results."
    )
    parser.add_argument("--learned-csv", type=Path, default=DEFAULT_LEARNED)
    parser.add_argument("--geometric-csv", type=Path, default=DEFAULT_GEOMETRIC)
    parser.add_argument(
        "--out-csv",
        type=Path,
        default=ROOT / "results" / "intercept_3d_compact_node_failure_baselines.csv",
    )
    parser.add_argument(
        "--summary-md",
        type=Path,
        default=ROOT / "docs" / "intercept_3d_compact_node_failure_baselines.md",
    )
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"missing input CSV: {path}")
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def method_label(row: dict[str, str]) -> str:
    graph = row.get("graph_encoder", "")
    if graph == "geometric":
        return "Oracle geometric pursuit"
    if graph == "single":
        return "Single-graph MAPPO"
    if graph == "multi_relation":
        return "EA-RG-MAPPO-S"
    return graph or row.get("method", "unknown")


def clean_rows(learned_rows: list[dict[str, str]], geometric_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in geometric_rows:
        copied = dict(row)
        copied["compact_method"] = method_label(copied)
        rows.append(copied)
    for row in learned_rows:
        if row.get("train_method", "bc_ppo") != "bc_ppo":
            continue
        if row.get("scenario") not in {"relay_failure", "scout_failure"}:
            continue
        copied = dict(row)
        copied["compact_method"] = method_label(copied)
        rows.append(copied)
    return rows


def mean_ci(values: list[float], rng: np.random.Generator, n_bootstrap: int = 5000) -> tuple[float, float, float]:
    arr = np.asarray(values, dtype=np.float64)
    if arr.size == 0:
        return float("nan"), float("nan"), float("nan")
    if arr.size == 1:
        value = float(arr[0])
        return value, value, value
    draws = rng.choice(arr, size=(n_bootstrap, arr.size), replace=True).mean(axis=1)
    return float(arr.mean()), float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))


def aggregate(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    seeds: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in rows:
        key = (row["scenario"], row["compact_method"])
        seeds[key].add(str(row.get("train_seed", row.get("seed", ""))))
        for metric in METRICS:
            grouped[key][metric].append(float(row[metric]))

    rng = np.random.default_rng(20260716)
    out: list[dict[str, object]] = []
    for scenario in ("relay_failure", "scout_failure"):
        for method in METHOD_ORDER:
            key = (scenario, method)
            if key not in grouped:
                continue
            row: dict[str, object] = {
                "scenario": scenario,
                "method": method,
                "n_episodes": len(grouped[key]["success"]),
                "n_replicates": len(seeds[key]),
            }
            for metric in METRICS:
                mean, low, high = mean_ci(grouped[key][metric], rng)
                row[f"{metric}_mean"] = mean
                row[f"{metric}_ci_low"] = low
                row[f"{metric}_ci_high"] = high
            out.append(row)
    return out


def write_csv(rows: list[dict[str, object]], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "scenario",
        "method",
        "n_episodes",
        "n_replicates",
        *[f"{metric}_{suffix}" for metric in METRICS for suffix in ("mean", "ci_low", "ci_high")],
    ]
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def fmt_ci(row: dict[str, object], metric: str, scale: float = 1.0, digits: int = 1) -> str:
    mean = float(row[f"{metric}_mean"]) * scale
    low = float(row[f"{metric}_ci_low"]) * scale
    high = float(row[f"{metric}_ci_high"]) * scale
    return f"{mean:.{digits}f} [{low:.{digits}f}, {high:.{digits}f}]"


def write_summary(rows: list[dict[str, object]], out_md: Path, args: argparse.Namespace) -> None:
    lines = [
        "# 3DOF Compact Node-Failure Baselines",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Inputs:",
        "",
        "```text",
        str(args.geometric_csv),
        str(args.learned_csv),
        "```",
        "",
        "Purpose:",
        "",
        "```text",
        "Put the oracle geometric pursuit diagnostic, single-graph MAPPO, and EA-RG-MAPPO-S under the same straight-target node-failure evaluation table.",
        "The geometric policy uses simulator target state and is therefore an oracle-style demonstrator/reference, not a fair decentralized learning baseline.",
        "Use this table to document task difficulty and baseline coverage; use the paired single-vs-multi and ablation tables for the method contribution.",
        "```",
        "",
        "## Compact Table",
        "",
        "| Scenario | Method | N | Success % [95% CI] | Recovery % [95% CI] | Recovery Steps [95% CI] | Tracking-Failure % [95% CI] | Connectivity-Failure % [95% CI] | Steps [95% CI] |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['scenario']} | {row['method']} | {row['n_episodes']} | "
            f"{fmt_ci(row, 'success', scale=100.0)} | "
            f"{fmt_ci(row, 'post_failure_chain_recovered', scale=100.0)} | "
            f"{fmt_ci(row, 'post_failure_chain_recovery_steps', digits=1)} | "
            f"{fmt_ci(row, 'tracking_during_failure_rate', scale=100.0)} | "
            f"{fmt_ci(row, 'connectivity_during_failure', scale=100.0)} | "
            f"{fmt_ci(row, 'steps', digits=1)} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "```text",
            "Straight-target node-failure episodes are now strong enough to show recovery timing differences, but they are not hard enough to separate an oracle geometric demonstrator from the learned policy.",
            "For a Q2-level manuscript, the next quality step is a stricter intermittent-sensing or maneuvering-target protocol where target truth is not always injected into every blue observation.",
            "```",
            "",
        ]
    )
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    rows = clean_rows(read_csv(args.learned_csv), read_csv(args.geometric_csv))
    summary_rows = aggregate(rows)
    if not summary_rows:
        raise RuntimeError("no compact baseline rows were produced")
    write_csv(summary_rows, args.out_csv)
    write_summary(summary_rows, args.summary_md, args)
    print(args.out_csv)
    print(args.summary_md)
    print(f"rows: {len(summary_rows)}")


if __name__ == "__main__":
    main()
