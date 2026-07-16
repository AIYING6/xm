from __future__ import annotations

import csv
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
SOURCE = RESULTS / "comm_dropout_robustness_eval.csv"
OUT_CSV = RESULTS / "comm_dropout_paired_statistics.csv"
OUT_MD = RESULTS / "comm_dropout_paired_statistics.md"
OUT_TEX = RESULTS / "latex_comm_dropout_paired_ci_table.tex"

METHOD = "EA-RG-MAPPO-S"
BASELINES = ["MAPPO", "GAT-MAPPO"]
RADII = [4.0, 8.0]
DROPOUTS = [0.0, 0.25, 0.5]
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
    comm_dropout_prob: float
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
    by_key: dict[tuple[str, int, float, float], dict[str, str]] = {}
    for row in rows:
        by_key[
            (
                row["method"],
                int(row["seed"]),
                float(row["radius"]),
                float(row["comm_dropout_prob"]),
            )
        ] = row

    output: list[StatRow] = []
    for baseline in BASELINES:
        for radius in RADII:
            for dropout in DROPOUTS:
                seeds = sorted(
                    seed
                    for method, seed, r, p in by_key
                    if method == METHOD
                    and r == radius
                    and p == dropout
                    and (baseline, seed, radius, dropout) in by_key
                )
                if len(seeds) != 3:
                    raise RuntimeError(
                        f"expected 3 paired seeds for {baseline} radius={radius} dropout={dropout}, got {seeds}"
                    )
                for metric, (column, direction) in METRICS.items():
                    diffs = []
                    for seed in seeds:
                        proposed = float(by_key[(METHOD, seed, radius, dropout)][column])
                        base = float(by_key[(baseline, seed, radius, dropout)][column])
                        diffs.append((proposed - base) * direction)
                    mean, std, ci_low, ci_high, t_stat, cohen_dz = paired_statistics(diffs)
                    output.append(
                        StatRow(
                            baseline=baseline,
                            radius=radius,
                            comm_dropout_prob=dropout,
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
        "comm_dropout_prob",
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
                    "comm_dropout_prob": f"{row.comm_dropout_prob:.2f}",
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
    grouped: dict[tuple[str, float, float], dict[str, StatRow]] = defaultdict(dict)
    for row in rows:
        grouped[(row.baseline, row.radius, row.comm_dropout_prob)][row.metric] = row

    lines = [
        "# Communication-Dropout Paired Statistics",
        "",
        "Purpose:",
        "",
        "```text",
        "Provide seed-paired descriptive confidence intervals for the communication-dropout diagnostic.",
        "The sample size is three seeds, so these intervals support robustness discussion but should not be phrased as definitive significance tests.",
        "Positive success_gain means EA-RG-MAPPO-S has higher success than the baseline.",
        "Positive collision_reduction means EA-RG-MAPPO-S has lower collision than the baseline.",
        "```",
        "",
        "## Paired Differences",
        "",
        "| Baseline | Radius | Dropout | Success gain, mean [95% CI] | Collision reduction, mean [95% CI] |",
        "|---|---:|---:|---:|---:|",
    ]
    for baseline in BASELINES:
        for radius in RADII:
            for dropout in DROPOUTS:
                item = grouped[(baseline, radius, dropout)]
                lines.append(
                    f"| {baseline} | {radius:.0f} | {dropout:.2f} | "
                    f"{fmt_ci(item['success_gain'])} | {fmt_ci(item['collision_reduction'])} |"
                )
    lines.extend(
        [
            "",
            "## Use in Paper",
            "",
            "```text",
            "Use as appendix evidence that the proposed method keeps positive paired success gains and collision reductions under stochastic communication dropout.",
            "Do not use this table as the only support for the main claim; pair it with the 300-episode main evaluation and the raw dropout summary table.",
            "```",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def write_tex(rows: list[StatRow]) -> None:
    grouped: dict[tuple[str, float, float], dict[str, StatRow]] = defaultdict(dict)
    for row in rows:
        grouped[(row.baseline, row.radius, row.comm_dropout_prob)][row.metric] = row

    lines = [
        "\\begin{table*}[t]",
        "\\centering",
        "\\caption{Seed-paired descriptive confidence intervals for the communication-dropout diagnostic. Positive success gain means higher success than the baseline, and positive collision reduction means lower collision than the baseline.}",
        "\\label{tab:comm_dropout_paired_ci}",
        "\\begin{tabular}{lcccc}",
        "\\toprule",
        "Baseline & Radius & Dropout & Success gain $\\uparrow$ & Collision reduction $\\uparrow$ \\\\",
        "\\midrule",
    ]
    current = None
    for baseline in BASELINES:
        for radius in RADII:
            for dropout in DROPOUTS:
                if current is not None and baseline != current:
                    lines.append("\\midrule")
                current = baseline
                item = grouped[(baseline, radius, dropout)]
                lines.append(
                    f"{baseline} & {radius:.0f} & {dropout:.2f} & "
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
