from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FINAL_SOURCE = RESULTS / "final_comm_300_summary.csv"
DROPOUT_SOURCE = RESULTS / "comm_dropout_robustness_summary.csv"
OUT_CSV = RESULTS / "aggregate_robustness_summary.csv"
OUT_MD = RESULTS / "aggregate_robustness_summary.md"
OUT_TEX = RESULTS / "latex_aggregate_robustness_table.tex"

METHODS = ["MAPPO", "GAT-MAPPO", "EA-RG-MAPPO-S"]
SCOPES = {
    "final_cross_radius": {
        "source": FINAL_SOURCE,
        "description": "300-episode final evaluation across communication radii 4, 6, 8, and 10",
    },
    "dropout_diagnostic": {
        "source": DROPOUT_SOURCE,
        "description": "50-episode communication-dropout diagnostic across radii 4 and 8 and dropout probabilities 0, 0.25, and 0.5",
    },
}


@dataclass(frozen=True)
class AggregateRow:
    scope: str
    method: str
    n_conditions: int
    mean_success: float
    worst_success: float
    success_range: float
    mean_collision: float
    worst_collision: float
    collision_range: float
    mean_margin: float
    conservative_margin: float


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def aggregate(scope: str, rows: list[dict[str, str]]) -> list[AggregateRow]:
    output: list[AggregateRow] = []
    for method in METHODS:
        method_rows = [row for row in rows if row["method"] == method]
        if not method_rows:
            raise RuntimeError(f"missing rows for method={method} scope={scope}")
        success = [float(row["success_mean"]) for row in method_rows]
        collision = [float(row["collision_mean"]) for row in method_rows]
        output.append(
            AggregateRow(
                scope=scope,
                method=method,
                n_conditions=len(method_rows),
                mean_success=mean(success),
                worst_success=min(success),
                success_range=max(success) - min(success),
                mean_collision=mean(collision),
                worst_collision=max(collision),
                collision_range=max(collision) - min(collision),
                mean_margin=mean(success) - mean(collision),
                conservative_margin=min(success) - max(collision),
            )
        )
    return output


def compute() -> list[AggregateRow]:
    rows: list[AggregateRow] = []
    for scope, cfg in SCOPES.items():
        rows.extend(aggregate(scope, load_csv(cfg["source"])))
    return rows


def write_csv(rows: list[AggregateRow]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "scope",
        "method",
        "n_conditions",
        "mean_success",
        "worst_success",
        "success_range",
        "mean_collision",
        "worst_collision",
        "collision_range",
        "mean_margin",
        "conservative_margin",
    ]
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "scope": row.scope,
                    "method": row.method,
                    "n_conditions": row.n_conditions,
                    "mean_success": f"{row.mean_success:.10f}",
                    "worst_success": f"{row.worst_success:.10f}",
                    "success_range": f"{row.success_range:.10f}",
                    "mean_collision": f"{row.mean_collision:.10f}",
                    "worst_collision": f"{row.worst_collision:.10f}",
                    "collision_range": f"{row.collision_range:.10f}",
                    "mean_margin": f"{row.mean_margin:.10f}",
                    "conservative_margin": f"{row.conservative_margin:.10f}",
                }
            )


def fmt(value: float) -> str:
    return f"{value:.3f}"


def scope_title(scope: str) -> str:
    return {
        "final_cross_radius": "Final cross-radius",
        "dropout_diagnostic": "Dropout diagnostic",
    }[scope]


def write_md(rows: list[AggregateRow]) -> None:
    lines = [
        "# Aggregate Robustness Summary",
        "",
        "Purpose:",
        "",
        "```text",
        "Summarize robustness across evaluation conditions without introducing a new training run.",
        "Mean margin is mean_success - mean_collision.",
        "Conservative margin is worst_success - worst_collision, where worst_success is the minimum success across conditions and worst_collision is the maximum collision across conditions.",
        "These are descriptive diagnostics for paper organization, not a new optimization objective.",
        "```",
        "",
        "## Scope Definitions",
        "",
        "| Scope | Definition |",
        "|---|---|",
    ]
    for scope, cfg in SCOPES.items():
        lines.append(f"| `{scope}` | {cfg['description']} |")

    lines.extend(
        [
            "",
            "## Aggregate Metrics",
            "",
            "| Scope | Method | Conditions | Mean success | Worst success | Success range | Mean collision | Worst collision | Collision range | Mean margin | Conservative margin |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in rows:
        lines.append(
            f"| {scope_title(row.scope)} | {row.method} | {row.n_conditions} | "
            f"{fmt(row.mean_success)} | {fmt(row.worst_success)} | {fmt(row.success_range)} | "
            f"{fmt(row.mean_collision)} | {fmt(row.worst_collision)} | {fmt(row.collision_range)} | "
            f"{fmt(row.mean_margin)} | {fmt(row.conservative_margin)} |"
        )

    proposed = [row for row in rows if row.method == "EA-RG-MAPPO-S"]
    lines.extend(["", "## Reading Notes", "", "```text"])
    for row in proposed:
        lines.append(
            f"{scope_title(row.scope)}: EA-RG-MAPPO-S mean_margin={row.mean_margin:.3f}, "
            f"conservative_margin={row.conservative_margin:.3f}, "
            f"worst_collision={row.worst_collision:.3f}."
        )
    lines.extend(
        [
            "Use these values as compact descriptive evidence for finite-communication robustness.",
            "Do not replace the main per-radius tables with this aggregate summary.",
            "```",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def write_tex(rows: list[AggregateRow]) -> None:
    lines = [
        "\\begin{table*}[t]",
        "\\centering",
        "\\caption{Aggregate robustness diagnostics across communication conditions. Mean margin is mean success minus mean collision. Conservative margin is worst success minus worst collision across the evaluated conditions.}",
        "\\label{tab:aggregate_robustness}",
        "\\begin{tabular}{llrrrrr}",
        "\\toprule",
        "Scope & Method & Mean Succ. $\\uparrow$ & Worst Succ. $\\uparrow$ & Mean Coll. $\\downarrow$ & Worst Coll. $\\downarrow$ & Cons. margin $\\uparrow$ \\\\",
        "\\midrule",
    ]
    current_scope = None
    for row in rows:
        if current_scope is not None and row.scope != current_scope:
            lines.append("\\midrule")
        current_scope = row.scope
        lines.append(
            f"{scope_title(row.scope)} & {row.method} & "
            f"{fmt(row.mean_success)} & {fmt(row.worst_success)} & "
            f"{fmt(row.mean_collision)} & {fmt(row.worst_collision)} & "
            f"{fmt(row.conservative_margin)} \\\\"
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
