from __future__ import annotations

import csv
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
SOURCE = RESULTS / "final_comm_300_eval.csv"
OUT_CSV = RESULTS / "final_300_paired_statistics.csv"
OUT_MD = RESULTS / "final_300_paired_statistics.md"
OUT_TEX = RESULTS / "latex_final_300_paired_ci_table.tex"

METHOD = "EA-RG-MAPPO-S"
BASELINES = ["MAPPO", "GAT-MAPPO"]
RADII = [4.0, 6.0, 8.0, 10.0]
METRICS = {
    "success_gain": ("success_rate", 1.0),
    "collision_reduction": ("collision_rate", -1.0),
}

# Two-sided 95% t critical value for n=3 paired samples, df=2.
T_CRIT_95_DF2 = 4.302652729911275


@dataclass(frozen=True)
class StatRow:
    baseline: str
    radius: float
    metric: str
    n: int
    mean_diff: float
    std_diff: float
    ci95_low: float
    ci95_high: float
    t_stat: float
    cohen_dz: float
    diffs: tuple[float, ...]


def load_rows() -> list[dict[str, str]]:
    with SOURCE.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def paired_statistics(diffs: list[float]) -> tuple[float, float, float, float, float, float]:
    n = len(diffs)
    mean = sum(diffs) / n
    if n <= 1:
        return mean, 0.0, mean, mean, 0.0, 0.0
    variance = sum((x - mean) ** 2 for x in diffs) / (n - 1)
    std = math.sqrt(variance)
    sem = std / math.sqrt(n)
    margin = T_CRIT_95_DF2 * sem
    t_stat = mean / sem if sem > 0 else math.inf
    cohen_dz = mean / std if std > 0 else math.inf
    return mean, std, mean - margin, mean + margin, t_stat, cohen_dz


def compute() -> list[StatRow]:
    rows = load_rows()
    by_key: dict[tuple[str, int, float], dict[str, str]] = {}
    for row in rows:
        by_key[(row["method"], int(row["seed"]), float(row["radius"]))] = row

    output: list[StatRow] = []
    for baseline in BASELINES:
        for radius in RADII:
            seeds = sorted(
                seed
                for method, seed, r in by_key
                if method == METHOD and r == radius and (baseline, seed, radius) in by_key
            )
            if len(seeds) != 3:
                raise RuntimeError(f"expected 3 paired seeds for {baseline} radius={radius}, got {seeds}")
            for metric, (column, direction) in METRICS.items():
                diffs = []
                for seed in seeds:
                    proposed = float(by_key[(METHOD, seed, radius)][column])
                    base = float(by_key[(baseline, seed, radius)][column])
                    diffs.append((proposed - base) * direction)
                mean, std, ci_low, ci_high, t_stat, cohen_dz = paired_statistics(diffs)
                output.append(
                    StatRow(
                        baseline=baseline,
                        radius=radius,
                        metric=metric,
                        n=len(diffs),
                        mean_diff=mean,
                        std_diff=std,
                        ci95_low=ci_low,
                        ci95_high=ci_high,
                        t_stat=t_stat,
                        cohen_dz=cohen_dz,
                        diffs=tuple(diffs),
                    )
                )
    return output


def write_csv(rows: list[StatRow]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "baseline",
        "radius",
        "metric",
        "n",
        "mean_diff",
        "std_diff",
        "ci95_low",
        "ci95_high",
        "t_stat",
        "cohen_dz",
        "seed_diffs",
    ]
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "baseline": row.baseline,
                    "radius": f"{row.radius:.0f}",
                    "metric": row.metric,
                    "n": row.n,
                    "mean_diff": f"{row.mean_diff:.10f}",
                    "std_diff": f"{row.std_diff:.10f}",
                    "ci95_low": f"{row.ci95_low:.10f}",
                    "ci95_high": f"{row.ci95_high:.10f}",
                    "t_stat": f"{row.t_stat:.10f}",
                    "cohen_dz": f"{row.cohen_dz:.10f}",
                    "seed_diffs": ";".join(f"{x:.10f}" for x in row.diffs),
                }
            )


def fmt_ci(row: StatRow) -> str:
    return f"{row.mean_diff:.3f} [{row.ci95_low:.3f}, {row.ci95_high:.3f}]"


def write_md(rows: list[StatRow]) -> None:
    grouped: dict[tuple[str, float], dict[str, StatRow]] = defaultdict(dict)
    for row in rows:
        grouped[(row.baseline, row.radius)][row.metric] = row

    lines = [
        "# Final 300-Episode Paired Statistics",
        "",
        "Purpose:",
        "",
        "```text",
        "Provide a seed-paired descriptive confidence-interval check for the final 300-episode main results.",
        "The sample size is three seeds, so these intervals are evidence-strength diagnostics rather than a stand-alone significance claim.",
        "Positive success_gain means EA-RG-MAPPO-S has higher success than the baseline.",
        "Positive collision_reduction means EA-RG-MAPPO-S has lower collision than the baseline.",
        "```",
        "",
        "## Paired Differences",
        "",
        "| Baseline | Radius | Success gain, mean [95% CI] | Collision reduction, mean [95% CI] |",
        "|---|---:|---:|---:|",
    ]
    for baseline in BASELINES:
        for radius in RADII:
            item = grouped[(baseline, radius)]
            lines.append(
                f"| {baseline} | {radius:.0f} | "
                f"{fmt_ci(item['success_gain'])} | {fmt_ci(item['collision_reduction'])} |"
            )
    lines.extend(
        [
            "",
            "## Use in Paper",
            "",
            "```text",
            "Use as supplementary support for robustness and collision-reduction claims.",
            "Do not phrase this as definitive statistical significance because n=3 makes the confidence intervals intentionally conservative.",
            "```",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def write_tex(rows: list[StatRow]) -> None:
    grouped: dict[tuple[str, float], dict[str, StatRow]] = defaultdict(dict)
    for row in rows:
        grouped[(row.baseline, row.radius)][row.metric] = row

    lines = [
        "\\begin{table*}[t]",
        "\\centering",
        "\\caption{Seed-paired descriptive confidence intervals for the final 300-episode evaluation. Positive success gain means higher success than the baseline, and positive collision reduction means lower collision than the baseline.}",
        "\\label{tab:final_300_paired_ci}",
        "\\begin{tabular}{lccc}",
        "\\toprule",
        "Baseline & Radius & Success gain $\\uparrow$ & Collision reduction $\\uparrow$ \\\\",
        "\\midrule",
    ]
    current = None
    for baseline in BASELINES:
        for radius in RADII:
            if current is not None and baseline != current:
                lines.append("\\midrule")
            current = baseline
            item = grouped[(baseline, radius)]
            lines.append(
                f"{baseline} & {radius:.0f} & "
                f"{fmt_ci(item['success_gain'])} & {fmt_ci(item['collision_reduction'])} \\\\"
            )
    lines.extend(["\\bottomrule", "\\end{tabular}", "\\end{table*}", ""])
    OUT_TEX.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = compute()
    write_csv(rows)
    write_md(rows)
    write_tex(rows)
    print(OUT_CSV)
    print(OUT_MD)
    print(OUT_TEX)


if __name__ == "__main__":
    main()
