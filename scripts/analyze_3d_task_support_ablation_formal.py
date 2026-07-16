from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FULL = ROOT / "results" / "intercept_3d_node_failure_curriculum_formal_node_failure_eval" / "episode_metrics.csv"
DEFAULT_ABLATED = ROOT / "results" / "intercept_3d_no_task_support_topology_formal" / "robustness_eval" / "episode_metrics.csv"
DEFAULT_OUT_CSV = ROOT / "results" / "intercept_3d_task_support_ablation_formal_summary.csv"
DEFAULT_OUT_MD = ROOT / "docs" / "intercept_3d_task_support_ablation_formal_summary.md"

METRICS = (
    "success",
    "post_failure_chain_recovered",
    "post_failure_chain_recovery_steps",
    "chain_closed_during_failure_rate",
    "tracking_during_failure_rate",
    "connectivity_during_failure",
    "steps",
    "timeout",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze formal full-vs-no-task-support 3DOF task-support ablation.")
    parser.add_argument("--full-csv", type=Path, default=DEFAULT_FULL)
    parser.add_argument("--ablated-csv", type=Path, default=DEFAULT_ABLATED)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT_CSV)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--bootstrap-samples", type=int, default=10_000)
    parser.add_argument("--bootstrap-seed", type=int, default=20_260_716)
    return parser.parse_args()


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def select_full(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if row.get("graph_encoder") == "multi_relation" and row.get("train_method") == "bc_ppo"]


def select_ablated(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if row.get("graph_encoder") == "multi_relation"
        and row.get("train_method") == "bc_ppo"
        and row.get("graph_relation_ablation", "no_task_support") == "no_task_support"
    ]


def means(rows: list[dict[str, str]]) -> dict[str, dict[str, float]]:
    buckets: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        for metric in METRICS:
            buckets[row["scenario"]][metric].append(float(row[metric]))
    return {scenario: {metric: float(np.mean(values)) for metric, values in metrics.items()} for scenario, metrics in buckets.items()}


def paired_values(full_rows: list[dict[str, str]], ablated_rows: list[dict[str, str]]) -> dict[str, dict[str, np.ndarray]]:
    full_by_key = {(row["scenario"], row["train_seed"], row["episode"]): row for row in full_rows}
    ablated_by_key = {(row["scenario"], row["train_seed"], row["episode"]): row for row in ablated_rows}
    buckets: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for key, full in full_by_key.items():
        ablated = ablated_by_key.get(key)
        if ablated is None:
            continue
        scenario = key[0]
        for metric in METRICS:
            buckets[scenario][metric].append(float(full[metric]) - float(ablated[metric]))
    return {scenario: {metric: np.asarray(values, dtype=np.float64) for metric, values in metrics.items()} for scenario, metrics in buckets.items()}


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


def build_summary(full_rows: list[dict[str, str]], ablated_rows: list[dict[str, str]], samples: int, seed: int) -> list[dict[str, str]]:
    full_means = means(full_rows)
    ablated_means = means(ablated_rows)
    deltas = paired_values(full_rows, ablated_rows)
    rng = np.random.default_rng(seed)
    rows: list[dict[str, str]] = []
    for scenario in sorted(set(full_means) & set(ablated_means)):
        row: dict[str, str] = {"scenario": scenario, "n_paired_episodes": str(len(next(iter(deltas[scenario].values()))))}
        for metric in METRICS:
            mean, lo, hi, p = bootstrap(deltas[scenario][metric], rng, samples)
            row[f"full_{metric}_mean"] = f"{full_means[scenario][metric]:.6g}"
            row[f"no_task_support_{metric}_mean"] = f"{ablated_means[scenario][metric]:.6g}"
            row[f"delta_{metric}_mean"] = f"{mean:.6g}"
            row[f"delta_{metric}_ci_low"] = f"{lo:.6g}"
            row[f"delta_{metric}_ci_high"] = f"{hi:.6g}"
            row[f"delta_{metric}_p_bootstrap"] = f"{p:.6g}"
        rows.append(row)
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise RuntimeError("No paired formal task-support ablation rows were generated")
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def fmt_ci(row: dict[str, str], metric: str, scale: float = 1.0) -> str:
    return (
        f"{scale * float(row[f'delta_{metric}_mean']):+.3f} "
        f"[{scale * float(row[f'delta_{metric}_ci_low']):+.3f}, {scale * float(row[f'delta_{metric}_ci_high']):+.3f}]"
    )


def write_md(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 3DOF Formal Task-Support Ablation",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "This table compares the full multi-relation role graph against the `no_task_support` ablation on matched node-failure evaluation seeds. Positive deltas favor the full model, except for steps and recovery steps where negative deltas favor the full model.",
        "",
        "| Scenario | N | Success full/no-task | Success delta [95% CI] | Recovery full/no-task | Recovery delta [95% CI] | Recovery steps full/no-task | Recovery-step delta [95% CI] | Steps delta [95% CI] |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['scenario']} | {row['n_paired_episodes']} | "
            f"{float(row['full_success_mean']):.3f} / {float(row['no_task_support_success_mean']):.3f} | "
            f"{fmt_ci(row, 'success')} | "
            f"{float(row['full_post_failure_chain_recovered_mean']):.3f} / {float(row['no_task_support_post_failure_chain_recovered_mean']):.3f} | "
            f"{fmt_ci(row, 'post_failure_chain_recovered')} | "
            f"{float(row['full_post_failure_chain_recovery_steps_mean']):.1f} / {float(row['no_task_support_post_failure_chain_recovery_steps_mean']):.1f} | "
            f"{fmt_ci(row, 'post_failure_chain_recovery_steps')} | "
            f"{fmt_ci(row, 'steps')} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "Use this as a manuscript-level ablation only when the ablated CSV was produced by the formal protocol with matched seeds and 30 evaluation episodes per scenario.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    rows = build_summary(select_full(read_rows(args.full_csv)), select_ablated(read_rows(args.ablated_csv)), args.bootstrap_samples, args.bootstrap_seed)
    write_csv(args.out_csv, rows)
    write_md(args.out_md, rows)
    print(args.out_csv)
    print(args.out_md)


if __name__ == "__main__":
    main()
