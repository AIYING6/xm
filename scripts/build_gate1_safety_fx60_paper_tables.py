from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]

MAIN_SUMMARY = (
    ROOT
    / "results"
    / "intercept_3d_gate1_hardened_safety_5seed_formal_candidate"
    / "checkpoint_sweep_fixed_update60_test"
    / "merged"
    / "test_checkpoint_summary.csv"
)
MAIN_STATS = {
    "multi_relation_vs_single": ROOT
    / "results"
    / "intercept_3d_gate1_hardened_safety_5seed_formal_candidate"
    / "checkpoint_sweep_fixed_update60_test"
    / "merged_seed_aware_stats"
    / "multi_vs_single"
    / "intercept_3d_strict_sensing_seed_aware_bootstrap.csv",
    "multi_relation_vs_no_graph": ROOT
    / "results"
    / "intercept_3d_gate1_hardened_safety_5seed_formal_candidate"
    / "checkpoint_sweep_fixed_update60_test"
    / "merged_seed_aware_stats"
    / "multi_vs_no_graph"
    / "intercept_3d_strict_sensing_seed_aware_bootstrap.csv",
}
ABLATION_SUMMARIES = {
    "no_task_support": ROOT
    / "results"
    / "intercept_3d_gate1_hardened_safety_no_task_support_5seed_fixed_update60_candidate"
    / "checkpoint_sweep_fixed_update60_test_matched_full"
    / "test_checkpoint_summary.csv",
    "no_role_pair_gate": ROOT
    / "results"
    / "intercept_3d_gate1_hardened_safety_no_role_pair_gate_5seed_fixed_update60_candidate"
    / "checkpoint_sweep_fixed_update60_test_matched_full"
    / "test_checkpoint_summary.csv",
}
ABLATION_STATS = {
    "multi_relation_vs_no_task_support": ROOT
    / "results"
    / "intercept_3d_gate1_hardened_safety_no_task_support_5seed_fixed_update60_candidate"
    / "comparison_vs_full"
    / "seed_aware_stats_matched_full"
    / "intercept_3d_strict_sensing_seed_aware_bootstrap.csv",
    "multi_relation_vs_no_role_pair_gate": ROOT
    / "results"
    / "intercept_3d_gate1_hardened_safety_no_role_pair_gate_5seed_fixed_update60_candidate"
    / "comparison_vs_full"
    / "seed_aware_stats_matched_full"
    / "intercept_3d_strict_sensing_seed_aware_bootstrap.csv",
}

OUT_DIR = ROOT / "results" / "gate1_safety_fx60_paper_tables"
DOC_OUT = ROOT / "docs" / "gate1_safety_fx60_paper_tables.md"


METHOD_LABELS = {
    "no_graph": "MAPPO (no graph)",
    "single": "Single-graph MAPPO",
    "multi_relation": "Full multi-relation",
    "no_task_support": "w/o task-support relation",
    "no_role_pair_gate": "w/o role-pair gate",
}


@dataclass(frozen=True)
class Summary:
    method: str
    recovery_mean: float
    recovery_sd: float
    tracking_mean: float
    tracking_sd: float
    connectivity_mean: float
    connectivity_sd: float
    chain_mean: float
    chain_sd: float
    timeout_mean: float
    timeout_sd: float
    collision_mean: float
    collision_sd: float
    min_br_mean: float
    min_br_sd: float
    min_bb_mean: float
    min_bb_sd: float
    seed_recovery: list[float]


def read_rows(path: Path) -> list[dict[str, str]]:
    with open_path(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open_path(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def native_path(path: Path) -> str:
    resolved = path.resolve()
    text = str(resolved)
    if os.name == "nt" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def open_path(path: Path, mode: str, **kwargs):
    return open(native_path(path), mode, **kwargs)


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def sd(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = mean(values)
    return (sum((v - m) ** 2 for v in values) / (len(values) - 1)) ** 0.5


def values(rows: list[dict[str, str]], key: str) -> list[float]:
    return [float(row[key]) for row in rows if row.get(key, "") not in {"", "inf", "nan"}]


def summarize_method(method: str, rows: list[dict[str, str]]) -> Summary:
    return Summary(
        method=method,
        recovery_mean=mean(values(rows, "post_failure_chain_recovered_mean")),
        recovery_sd=sd(values(rows, "post_failure_chain_recovered_mean")),
        tracking_mean=mean(values(rows, "tracking_during_failure_rate_mean")),
        tracking_sd=sd(values(rows, "tracking_during_failure_rate_mean")),
        connectivity_mean=mean(values(rows, "connectivity_during_failure_mean")),
        connectivity_sd=sd(values(rows, "connectivity_during_failure_mean")),
        chain_mean=mean(values(rows, "chain_closed_during_failure_rate_mean")),
        chain_sd=sd(values(rows, "chain_closed_during_failure_rate_mean")),
        timeout_mean=mean(values(rows, "timeout_mean")),
        timeout_sd=sd(values(rows, "timeout_mean")),
        collision_mean=mean(values(rows, "collision_mean")),
        collision_sd=sd(values(rows, "collision_mean")),
        min_br_mean=mean(values(rows, "episode_min_blue_red_distance_mean")),
        min_br_sd=sd(values(rows, "episode_min_blue_red_distance_mean")),
        min_bb_mean=mean(values(rows, "episode_min_blue_blue_distance_mean")),
        min_bb_sd=sd(values(rows, "episode_min_blue_blue_distance_mean")),
        seed_recovery=values(rows, "post_failure_chain_recovered_mean"),
    )


def collect_main_summaries() -> list[Summary]:
    rows = read_rows(MAIN_SUMMARY)
    out: list[Summary] = []
    for method in ("no_graph", "single", "multi_relation"):
        method_rows = [row for row in rows if row["graph_encoder"] == method]
        out.append(summarize_method(method, method_rows))
    return out


def collect_ablation_summaries(main: Summary) -> list[Summary]:
    out = [main]
    for name, path in ABLATION_SUMMARIES.items():
        rows = read_rows(path)
        out.append(summarize_method(name, rows))
    return out


def fmt_pm(mean_value: float, sd_value: float, scale: float = 100.0, suffix: str = "") -> str:
    return f"{mean_value * scale:.1f} +/- {sd_value * scale:.1f}{suffix}"


def fmt_ci(row: dict[str, str], scale: float = 100.0, suffix: str = " pp") -> str:
    delta = float(row["delta_proposed_minus_baseline"]) * scale
    lo = float(row["delta_ci_low"]) * scale
    hi = float(row["delta_ci_high"]) * scale
    return f"{delta:+.1f} [{lo:+.1f}, {hi:+.1f}]{suffix}"


def summary_to_row(summary: Summary) -> dict[str, object]:
    return {
        "method": summary.method,
        "label": METHOD_LABELS.get(summary.method, summary.method),
        "recovery_mean": f"{summary.recovery_mean:.6g}",
        "recovery_sd": f"{summary.recovery_sd:.6g}",
        "tracking_mean": f"{summary.tracking_mean:.6g}",
        "tracking_sd": f"{summary.tracking_sd:.6g}",
        "connectivity_mean": f"{summary.connectivity_mean:.6g}",
        "connectivity_sd": f"{summary.connectivity_sd:.6g}",
        "chain_mean": f"{summary.chain_mean:.6g}",
        "chain_sd": f"{summary.chain_sd:.6g}",
        "timeout_mean": f"{summary.timeout_mean:.6g}",
        "timeout_sd": f"{summary.timeout_sd:.6g}",
        "collision_mean": f"{summary.collision_mean:.6g}",
        "collision_sd": f"{summary.collision_sd:.6g}",
        "min_blue_red_m": f"{summary.min_br_mean:.2f}",
        "min_blue_blue_m": f"{summary.min_bb_mean:.2f}",
        "seed_recovery": "[" + ", ".join(f"{v:.2f}" for v in summary.seed_recovery) + "]",
    }


def collect_stat_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for comparison, path in {**MAIN_STATS, **ABLATION_STATS}.items():
        for row in read_rows(path):
            if row["metric"] in {
                "post_failure_chain_recovered",
                "timeout",
                "capped_recovery_steps",
                "tracking_during_failure_rate",
                "connectivity_during_failure",
                "chain_closed_during_failure_rate",
            }:
                out = dict(row)
                out["comparison"] = comparison
                rows.append(out)
    return rows


def markdown_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    return [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *["| " + " | ".join(row) + " |" for row in rows],
    ]


def latex_table(path: Path, caption: str, label: str, headers: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    align = "l" + "c" * (len(headers) - 1)
    lines = [
        "\\begin{table}[t]",
        "\\centering",
        f"\\caption{{{caption}}}",
        f"\\label{{{label}}}",
        "\\small",
        "\\resizebox{\\textwidth}{!}{%",
        f"\\begin{{tabular}}{{{align}}}",
        "\\toprule",
        " & ".join(headers) + " \\\\",
        "\\midrule",
    ]
    lines.extend(" & ".join(row) + " \\\\" for row in rows)
    lines.extend(["\\bottomrule", "\\end{tabular}%", "}", "\\end{table}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    main_summaries = collect_main_summaries()
    full = next(summary for summary in main_summaries if summary.method == "multi_relation")
    ablation_summaries = collect_ablation_summaries(full)
    stat_rows = collect_stat_rows()

    summary_columns = [
        "method",
        "label",
        "recovery_mean",
        "recovery_sd",
        "tracking_mean",
        "tracking_sd",
        "connectivity_mean",
        "connectivity_sd",
        "chain_mean",
        "chain_sd",
        "timeout_mean",
        "timeout_sd",
        "collision_mean",
        "collision_sd",
        "min_blue_red_m",
        "min_blue_blue_m",
        "seed_recovery",
    ]
    write_csv(OUT_DIR / "main_results.csv", [summary_to_row(s) for s in main_summaries], summary_columns)
    write_csv(OUT_DIR / "ablation_results.csv", [summary_to_row(s) for s in ablation_summaries], summary_columns)

    stat_columns = [
        "comparison",
        "metric",
        "label",
        "unit",
        "n_training_seeds",
        "n_matched_episodes_total",
        "delta_proposed_minus_baseline",
        "delta_ci_low",
        "delta_ci_high",
        "bootstrap_samples",
        "bootstrap_seed",
    ]
    write_csv(OUT_DIR / "seed_aware_deltas.csv", stat_rows, stat_columns)

    main_md_rows = [
        [
            METHOD_LABELS[s.method],
            fmt_pm(s.recovery_mean, s.recovery_sd),
            fmt_pm(s.tracking_mean, s.tracking_sd),
            fmt_pm(s.connectivity_mean, s.connectivity_sd),
            fmt_pm(s.chain_mean, s.chain_sd),
            fmt_pm(s.timeout_mean, s.timeout_sd),
            fmt_pm(s.collision_mean, s.collision_sd),
        ]
        for s in main_summaries
    ]
    ablation_md_rows = [
        [
            METHOD_LABELS[s.method],
            fmt_pm(s.recovery_mean, s.recovery_sd),
            fmt_pm(s.tracking_mean, s.tracking_sd),
            fmt_pm(s.chain_mean, s.chain_sd),
            fmt_pm(s.timeout_mean, s.timeout_sd),
            fmt_pm(s.collision_mean, s.collision_sd),
            "[" + ", ".join(f"{v:.2f}" for v in s.seed_recovery) + "]",
        ]
        for s in ablation_summaries
    ]

    def stat_metric(comparison: str, metric: str) -> dict[str, str]:
        for row in stat_rows:
            if row["comparison"] == comparison and row["metric"] == metric:
                return row
        raise KeyError((comparison, metric))

    ci_rows = [
        [
            "Full vs Single graph",
            fmt_ci(stat_metric("multi_relation_vs_single", "post_failure_chain_recovered")),
            fmt_ci(stat_metric("multi_relation_vs_single", "tracking_during_failure_rate")),
            fmt_ci(stat_metric("multi_relation_vs_single", "chain_closed_during_failure_rate")),
            fmt_ci(stat_metric("multi_relation_vs_single", "timeout")),
        ],
        [
            "Full vs No graph",
            fmt_ci(stat_metric("multi_relation_vs_no_graph", "post_failure_chain_recovered")),
            fmt_ci(stat_metric("multi_relation_vs_no_graph", "tracking_during_failure_rate")),
            fmt_ci(stat_metric("multi_relation_vs_no_graph", "chain_closed_during_failure_rate")),
            fmt_ci(stat_metric("multi_relation_vs_no_graph", "timeout")),
        ],
        [
            "Full vs w/o task-support",
            fmt_ci(stat_metric("multi_relation_vs_no_task_support", "post_failure_chain_recovered")),
            fmt_ci(stat_metric("multi_relation_vs_no_task_support", "tracking_during_failure_rate")),
            fmt_ci(stat_metric("multi_relation_vs_no_task_support", "chain_closed_during_failure_rate")),
            fmt_ci(stat_metric("multi_relation_vs_no_task_support", "timeout")),
        ],
        [
            "Full vs w/o role-pair gate",
            fmt_ci(stat_metric("multi_relation_vs_no_role_pair_gate", "post_failure_chain_recovered")),
            fmt_ci(stat_metric("multi_relation_vs_no_role_pair_gate", "tracking_during_failure_rate")),
            fmt_ci(stat_metric("multi_relation_vs_no_role_pair_gate", "chain_closed_during_failure_rate")),
            fmt_ci(stat_metric("multi_relation_vs_no_role_pair_gate", "timeout")),
        ],
    ]

    main_headers = ["Method", "Recovery", "Tracking", "Connectivity", "Chain", "Timeout", "Collision"]
    ablation_headers = ["Variant", "Recovery", "Tracking", "Chain", "Timeout", "Collision", "Seed recovery"]
    ci_headers = ["Comparison", "Recovery delta", "Tracking delta", "Chain delta", "Timeout delta"]

    latex_table(
        OUT_DIR / "main_results_latex.tex",
        "Fixed-update-60 hardened safety main comparison under strict intermittent sensing.",
        "tab:gate1-safety-fx60-main",
        main_headers,
        main_md_rows,
    )
    latex_table(
        OUT_DIR / "ablation_results_latex.tex",
        "Fixed-update-60 hardened safety mechanism ablations.",
        "tab:gate1-safety-fx60-ablation",
        ablation_headers,
        ablation_md_rows,
    )
    latex_table(
        OUT_DIR / "seed_aware_deltas_latex.tex",
        "Seed-aware hierarchical bootstrap deltas for fixed-update-60 hardened safety results.",
        "tab:gate1-safety-fx60-bootstrap",
        ci_headers,
        ci_rows,
    )

    md_lines = [
        "# Gate 1 Safety Fixed-Update-60 Paper Tables",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Status",
        "",
        "These tables package the fixed-budget hardened safety evidence for paper drafting. They do not introduce new training or new checkpoint selection.",
        "",
        "## Main Comparison",
        "",
        *markdown_table(main_headers, main_md_rows),
        "",
        "## Mechanism Ablations",
        "",
        *markdown_table(ablation_headers, ablation_md_rows),
        "",
        "## Seed-Aware Deltas",
        "",
        *markdown_table(ci_headers, ci_rows),
        "",
        "## Recommended Paper Claim",
        "",
        "- The full multi-relation method strongly improves post-failure recovery over no-graph and single-graph baselines.",
        "- Role-pair-conditioned message gating is the cleanest current mechanism ablation; its seed-aware recovery interval separates in favor of the full method.",
        "- Task-support relation removal lowers mean recovery but the seed-aware interval crosses zero, so use it as supportive rather than decisive evidence.",
        "",
        "## Caution",
        "",
        "- This package uses the frozen fixed `update_0060` rule. Do not mix these tables with validation-selected results without stating the checkpoint-selection protocol.",
        "- `no_curriculum` is not included. If omitted from the paper, state that the current evidence targets graph/message mechanisms, not isolated curriculum causality.",
        "",
        "## Artifacts",
        "",
        f"- Main CSV: `{(OUT_DIR / 'main_results.csv').relative_to(ROOT).as_posix()}`",
        f"- Ablation CSV: `{(OUT_DIR / 'ablation_results.csv').relative_to(ROOT).as_posix()}`",
        f"- Bootstrap CSV: `{(OUT_DIR / 'seed_aware_deltas.csv').relative_to(ROOT).as_posix()}`",
        f"- Main LaTeX: `{(OUT_DIR / 'main_results_latex.tex').relative_to(ROOT).as_posix()}`",
        f"- Ablation LaTeX: `{(OUT_DIR / 'ablation_results_latex.tex').relative_to(ROOT).as_posix()}`",
        f"- Bootstrap LaTeX: `{(OUT_DIR / 'seed_aware_deltas_latex.tex').relative_to(ROOT).as_posix()}`",
        "",
    ]
    DOC_OUT.write_text("\n".join(md_lines), encoding="utf-8")
    print(DOC_OUT)
    print(OUT_DIR)


if __name__ == "__main__":
    main()
