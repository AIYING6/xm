"""Seed-aware statistics for strict-sensing relay-failure experiments.

This analysis treats independent training seeds as the primary unit and uses a
hierarchical bootstrap:

1. resample training seeds with replacement;
2. within each sampled training seed, resample matched evaluation episodes;
3. compute method means and paired deltas.

The script is intentionally separate from the quick development summary because
episode-level bootstrap that ignores training seeds overstates confidence.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List

import numpy as np


DEFAULT_ROOTS = [
    Path("results/intercept_3d_strict_sensing_formal_seed0_dev/checkpoint_sweep/test_episode_metrics.csv"),
    Path("results/intercept_3d_strict_sensing_formal_seed1_dev/checkpoint_sweep/test_episode_metrics.csv"),
    Path("results/intercept_3d_strict_sensing_formal_seed2_dev/checkpoint_sweep/test_episode_metrics.csv"),
]


@dataclass(frozen=True)
class MetricSpec:
    name: str
    label: str
    unit: str
    higher_is_better: bool
    getter: Callable[[Dict[str, str]], float]


def _float(row: Dict[str, str], key: str, default: float = 0.0) -> float:
    value = row.get(key, "")
    if value == "" or value is None:
        return default
    return float(value)


def _bool_float(row: Dict[str, str], key: str) -> float:
    return 1.0 if _float(row, key) >= 0.5 else 0.0


def _capped_recovery_steps(row: Dict[str, str]) -> float:
    """Restricted mean time-to-recovery proxy.

    If an episode does not recover after relay failure, assign the remaining
    horizon after the failure starts. This keeps recovery probability and speed
    coupled without pretending unrecovered episodes have a finite observed
    recovery time.
    """

    if _bool_float(row, "post_failure_chain_recovered") > 0.5:
        return _float(row, "post_failure_chain_recovery_steps")
    max_steps = _float(row, "max_steps", default=_float(row, "steps", default=260.0))
    failure_start = _float(row, "node_failure_start_step", default=40.0)
    return max(0.0, max_steps - failure_start)


METRICS = [
    MetricSpec(
        name="success",
        label="Task success",
        unit="rate",
        higher_is_better=True,
        getter=lambda row: _bool_float(row, "success"),
    ),
    MetricSpec(
        name="post_failure_chain_recovered",
        label="Post-failure chain recovered",
        unit="rate",
        higher_is_better=True,
        getter=lambda row: _bool_float(row, "post_failure_chain_recovered"),
    ),
    MetricSpec(
        name="timeout",
        label="Timeout",
        unit="rate",
        higher_is_better=False,
        getter=lambda row: _bool_float(row, "timeout"),
    ),
    MetricSpec(
        name="capped_recovery_steps",
        label="Restricted mean recovery steps",
        unit="steps",
        higher_is_better=False,
        getter=_capped_recovery_steps,
    ),
    MetricSpec(
        name="tracking_during_failure_rate",
        label="Tracking during failure",
        unit="rate",
        higher_is_better=True,
        getter=lambda row: _float(row, "tracking_during_failure_rate"),
    ),
    MetricSpec(
        name="connectivity_during_failure",
        label="Connectivity during failure",
        unit="rate",
        higher_is_better=True,
        getter=lambda row: _float(row, "connectivity_during_failure"),
    ),
    MetricSpec(
        name="chain_closed_during_failure_rate",
        label="Chain closure during failure",
        unit="rate",
        higher_is_better=True,
        getter=lambda row: _float(row, "chain_closed_during_failure_rate"),
    ),
    MetricSpec(
        name="steps",
        label="Episode length",
        unit="steps",
        higher_is_better=False,
        getter=lambda row: _float(row, "steps"),
    ),
]


Pair = Dict[str, Dict[str, str]]
PairsBySeed = Dict[int, Dict[int, Pair]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--episode-csv",
        action="append",
        type=Path,
        default=None,
        help="Path to a test_episode_metrics.csv file. May be repeated.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results"),
        help="Directory for CSV outputs.",
    )
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=Path("docs"),
        help="Directory for Markdown report.",
    )
    parser.add_argument("--bootstrap-samples", type=int, default=5000)
    parser.add_argument("--bootstrap-seed", type=int, default=20260717)
    parser.add_argument(
        "--methods",
        nargs=2,
        default=["single", "multi_relation"],
        metavar=("BASELINE", "PROPOSED"),
        help="Method names to compare.",
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default=None,
        help="Optional scenario filter for combined episode CSVs.",
    )
    return parser.parse_args()


def load_pairs(paths: Iterable[Path], methods: tuple[str, str], scenario: str | None = None) -> PairsBySeed:
    pairs: PairsBySeed = {}
    allowed = set(methods)
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(path)
        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if scenario is not None and row.get("scenario", "") != scenario:
                    continue
                method = row.get("graph_encoder", row.get("method", ""))
                if method not in allowed:
                    continue
                train_seed = int(float(row["train_seed"]))
                episode_seed = int(float(row["seed"]))
                pairs.setdefault(train_seed, {}).setdefault(episode_seed, {})[method] = row

    complete: PairsBySeed = {}
    for train_seed, episodes in pairs.items():
        for episode_seed, pair in episodes.items():
            if all(method in pair for method in methods):
                complete.setdefault(train_seed, {})[episode_seed] = pair
    if not complete:
        raise ValueError("No matched method pairs found in episode CSVs.")
    return complete


def _mean(values: List[float]) -> float:
    return float(np.mean(values)) if values else float("nan")


def method_mean(pairs: List[Pair], method: str, metric: MetricSpec) -> float:
    return _mean([metric.getter(pair[method]) for pair in pairs])


def flatten_pairs(pairs_by_seed: PairsBySeed) -> List[Pair]:
    return [pair for episodes in pairs_by_seed.values() for pair in episodes.values()]


def seed_level_rows(
    pairs_by_seed: PairsBySeed, baseline: str, proposed: str
) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for train_seed in sorted(pairs_by_seed):
        pairs = list(pairs_by_seed[train_seed].values())
        for metric in METRICS:
            base = method_mean(pairs, baseline, metric)
            prop = method_mean(pairs, proposed, metric)
            rows.append(
                {
                    "train_seed": str(train_seed),
                    "metric": metric.name,
                    "label": metric.label,
                    "unit": metric.unit,
                    "n_matched_episodes": str(len(pairs)),
                    baseline: f"{base:.10g}",
                    proposed: f"{prop:.10g}",
                    "delta_proposed_minus_baseline": f"{(prop - base):.10g}",
                }
            )
    return rows


def observed_rows(
    pairs_by_seed: PairsBySeed, baseline: str, proposed: str
) -> List[Dict[str, object]]:
    pairs = flatten_pairs(pairs_by_seed)
    rows: List[Dict[str, object]] = []
    for metric in METRICS:
        base = method_mean(pairs, baseline, metric)
        prop = method_mean(pairs, proposed, metric)
        rows.append(
            {
                "metric": metric.name,
                "label": metric.label,
                "unit": metric.unit,
                "higher_is_better": str(metric.higher_is_better).lower(),
                baseline: base,
                proposed: prop,
                "delta_proposed_minus_baseline": prop - base,
            }
        )
    return rows


def hierarchical_bootstrap(
    pairs_by_seed: PairsBySeed,
    baseline: str,
    proposed: str,
    samples: int,
    seed: int,
) -> Dict[str, np.ndarray]:
    rng = np.random.default_rng(seed)
    train_seeds = np.array(sorted(pairs_by_seed), dtype=int)
    metric_values = {metric.name: np.zeros(samples, dtype=float) for metric in METRICS}

    for i in range(samples):
        sampled_train_seeds = rng.choice(train_seeds, size=len(train_seeds), replace=True)
        sampled_pairs: List[Pair] = []
        for train_seed in sampled_train_seeds:
            episode_ids = np.array(sorted(pairs_by_seed[int(train_seed)]), dtype=int)
            sampled_episode_ids = rng.choice(
                episode_ids, size=len(episode_ids), replace=True
            )
            sampled_pairs.extend(
                pairs_by_seed[int(train_seed)][int(episode_seed)]
                for episode_seed in sampled_episode_ids
            )
        for metric in METRICS:
            base = method_mean(sampled_pairs, baseline, metric)
            prop = method_mean(sampled_pairs, proposed, metric)
            metric_values[metric.name][i] = prop - base

    return metric_values


def bootstrap_rows(
    pairs_by_seed: PairsBySeed,
    baseline: str,
    proposed: str,
    samples: int,
    seed: int,
) -> List[Dict[str, str]]:
    observed = {row["metric"]: row for row in observed_rows(pairs_by_seed, baseline, proposed)}
    boot = hierarchical_bootstrap(pairs_by_seed, baseline, proposed, samples, seed)
    rows: List[Dict[str, str]] = []
    for metric in METRICS:
        values = boot[metric.name]
        low, high = np.percentile(values, [2.5, 97.5])
        obs = observed[metric.name]
        rows.append(
            {
                "metric": metric.name,
                "label": metric.label,
                "unit": metric.unit,
                "higher_is_better": str(metric.higher_is_better).lower(),
                "n_training_seeds": str(len(pairs_by_seed)),
                "n_matched_episodes_total": str(len(flatten_pairs(pairs_by_seed))),
                baseline: f"{float(obs[baseline]):.10g}",
                proposed: f"{float(obs[proposed]):.10g}",
                "delta_proposed_minus_baseline": f"{float(obs['delta_proposed_minus_baseline']):.10g}",
                "delta_ci_low": f"{float(low):.10g}",
                "delta_ci_high": f"{float(high):.10g}",
                "bootstrap_samples": str(samples),
                "bootstrap_seed": str(seed),
            }
        )
    return rows


def recovered_only_rows(
    pairs_by_seed: PairsBySeed, baseline: str, proposed: str
) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for method in [baseline, proposed]:
        values = [
            _float(pair[method], "post_failure_chain_recovery_steps")
            for pair in flatten_pairs(pairs_by_seed)
            if _bool_float(pair[method], "post_failure_chain_recovered") > 0.5
        ]
        rows.append(
            {
                "method": method,
                "metric": "recovered_only_recovery_steps",
                "unit": "steps",
                "n_recovered_episodes": str(len(values)),
                "mean": f"{_mean(values):.10g}",
                "note": "Conditional on episodes that recovered; use capped_recovery_steps for a comparable recovery-time proxy.",
            }
        )
    return rows


def write_csv(path: Path, rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"No rows to write for {path}")
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def format_metric_value(value: float, unit: str) -> str:
    if unit == "rate":
        return f"{100.0 * value:.1f}%"
    return f"{value:.2f}"


def write_markdown(
    path: Path,
    bootstrap: List[Dict[str, str]],
    seed_rows: List[Dict[str, str]],
    recovered_rows: List[Dict[str, str]],
    baseline: str,
    proposed: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    seed_count = bootstrap[0]["n_training_seeds"]
    episode_count = bootstrap[0]["n_matched_episodes_total"]

    lines: List[str] = [
        "# Strict-Sensing Seed-Aware Statistics",
        "",
        "This report uses matched strict-sensing evaluation episodes from the selected scenario.",
        "Uncertainty is estimated with a hierarchical bootstrap: training seeds are resampled first, then matched episodes are resampled within each selected training seed.",
        "",
        f"- Baseline: `{baseline}`",
        f"- Proposed: `{proposed}`",
        f"- Independent training seeds: {seed_count}",
        f"- Matched test episodes: {episode_count}",
        "",
        "## Bootstrap Summary",
        "",
        "| Metric | Baseline | Proposed | Delta | 95% CI for delta |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in bootstrap:
        unit = row["unit"]
        base = float(row[baseline])
        prop = float(row[proposed])
        delta = float(row["delta_proposed_minus_baseline"])
        low = float(row["delta_ci_low"])
        high = float(row["delta_ci_high"])
        if unit == "rate":
            delta_text = f"{100.0 * delta:+.1f} pp"
            ci_text = f"[{100.0 * low:+.1f}, {100.0 * high:+.1f}] pp"
        else:
            delta_text = f"{delta:+.2f}"
            ci_text = f"[{low:+.2f}, {high:+.2f}]"
        lines.append(
            "| "
            + " | ".join(
                [
                    row["label"],
                    format_metric_value(base, unit),
                    format_metric_value(prop, unit),
                    delta_text,
                    ci_text,
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Recovery-Time Handling",
            "",
            "Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.",
            "",
            "| Method | Recovered episodes | Recovered-only mean steps |",
            "|---|---:|---:|",
        ]
    )
    for row in recovered_rows:
        lines.append(
            f"| {row['method']} | {row['n_recovered_episodes']} | {float(row['mean']):.2f} |"
        )

    lines.extend(
        [
            "",
            "## Seed-Level Deltas",
            "",
            "| Seed | Metric | Baseline | Proposed | Delta |",
            "|---:|---|---:|---:|---:|",
        ]
    )
    for row in seed_rows:
        unit = row["unit"]
        base = float(row[baseline])
        prop = float(row[proposed])
        delta = float(row["delta_proposed_minus_baseline"])
        if unit == "rate":
            delta_text = f"{100.0 * delta:+.1f} pp"
        else:
            delta_text = f"{delta:+.2f}"
        lines.append(
            "| "
            + " | ".join(
                [
                    row["train_seed"],
                    row["label"],
                    format_metric_value(base, unit),
                    format_metric_value(prop, unit),
                    delta_text,
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    paths = args.episode_csv if args.episode_csv else DEFAULT_ROOTS
    baseline, proposed = tuple(args.methods)
    pairs_by_seed = load_pairs(paths, (baseline, proposed), scenario=args.scenario)

    seed_rows = seed_level_rows(pairs_by_seed, baseline, proposed)
    boot_rows = bootstrap_rows(
        pairs_by_seed,
        baseline,
        proposed,
        samples=args.bootstrap_samples,
        seed=args.bootstrap_seed,
    )
    recovered_rows = recovered_only_rows(pairs_by_seed, baseline, proposed)

    write_csv(
        args.output_dir / "intercept_3d_strict_sensing_seed_level_deltas.csv",
        seed_rows,
    )
    write_csv(
        args.output_dir / "intercept_3d_strict_sensing_seed_aware_bootstrap.csv",
        boot_rows,
    )
    write_csv(
        args.output_dir / "intercept_3d_strict_sensing_recovered_only_steps.csv",
        recovered_rows,
    )
    write_markdown(
        args.docs_dir / "intercept_3d_strict_sensing_seed_aware_bootstrap.md",
        boot_rows,
        seed_rows,
        recovered_rows,
        baseline,
        proposed,
    )


if __name__ == "__main__":
    main()
