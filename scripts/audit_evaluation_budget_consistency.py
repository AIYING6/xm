from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / "results" / "evaluation_budget_audit.csv"
OUT_REPORT = ROOT / "docs" / "evaluation_budget_audit.md"


@dataclass(frozen=True)
class BudgetSpec:
    name: str
    csv_path: str
    expected_rows: int
    expected_episodes: int | None
    latex_path: str | None
    latex_marker: str | None
    note: str


SPECS = [
    BudgetSpec(
        name="final_main",
        csv_path="results/final_comm_300_summary.csv",
        expected_rows=12,
        expected_episodes=300,
        latex_path="results/latex_final_comm_300_table.tex",
        latex_marker="Final 300-episode evaluation",
        note="Main evaluation table.",
    ),
    BudgetSpec(
        name="ablation",
        csv_path="results/paper_comm_results.csv",
        expected_rows=20,
        expected_episodes=None,
        latex_path="results/latex_ablation_comm_table.tex",
        latex_marker="Ablation study",
        note="100-episode-per-seed module ablation; source CSV is legacy formatted without an episodes column.",
    ),
    BudgetSpec(
        name="speed_robustness",
        csv_path="results/speed_robustness_summary.csv",
        expected_rows=18,
        expected_episodes=100,
        latex_path="results/latex_speed_robustness_table.tex",
        latex_marker="100 episodes per seed",
        note="Appendix target-speed robustness diagnostic.",
    ),
    BudgetSpec(
        name="comm_dropout",
        csv_path="results/comm_dropout_robustness_summary.csv",
        expected_rows=18,
        expected_episodes=50,
        latex_path="results/latex_comm_dropout_robustness_table.tex",
        latex_marker="50 episodes per seed",
        note="Appendix communication-dropout diagnostic.",
    ),
    BudgetSpec(
        name="radius_interpolation",
        csv_path="results/radius_interpolation_summary.csv",
        expected_rows=9,
        expected_episodes=50,
        latex_path="results/latex_radius_interpolation_table.tex",
        latex_marker="50 episodes per seed",
        note="Appendix unseen-radius interpolation diagnostic.",
    ),
    BudgetSpec(
        name="edge_feature_masking",
        csv_path="results/edge_feature_ablation_summary.csv",
        expected_rows=14,
        expected_episodes=30,
        latex_path="results/latex_edge_feature_ablation_table.tex",
        latex_marker="30 episodes per seed",
        note="Appendix evaluation-time edge-feature masking diagnostic.",
    ),
]


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def audit_spec(spec: BudgetSpec) -> dict[str, str]:
    csv_path = ROOT / spec.csv_path
    rows = read_rows(csv_path)
    status = "ok"
    notes = []
    if len(rows) != spec.expected_rows:
        status = "failed"
        notes.append(f"row_count expected={spec.expected_rows} actual={len(rows)}")

    actual_episodes = "n/a"
    if spec.expected_episodes is not None:
        if "episodes" not in rows[0]:
            status = "failed"
            notes.append("missing episodes column")
        else:
            episodes = sorted({int(float(row["episodes"])) for row in rows})
            actual_episodes = ",".join(str(value) for value in episodes)
            if episodes != [spec.expected_episodes]:
                status = "failed"
                notes.append(f"episodes expected={spec.expected_episodes} actual={episodes}")

    if spec.latex_path is not None and spec.latex_marker is not None:
        latex_text = (ROOT / spec.latex_path).read_text(encoding="utf-8")
        if spec.latex_marker not in latex_text:
            status = "failed"
            notes.append(f"latex marker missing: {spec.latex_marker}")

    return {
        "name": spec.name,
        "csv_path": spec.csv_path,
        "expected_rows": str(spec.expected_rows),
        "actual_rows": str(len(rows)),
        "expected_episodes": str(spec.expected_episodes) if spec.expected_episodes is not None else "n/a",
        "actual_episodes": actual_episodes,
        "latex_path": spec.latex_path or "",
        "latex_marker": spec.latex_marker or "",
        "status": status,
        "notes": "; ".join(notes) if notes else spec.note,
    }


def write_csv(rows: list[dict[str, str]]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "name",
        "csv_path",
        "expected_rows",
        "actual_rows",
        "expected_episodes",
        "actual_episodes",
        "latex_path",
        "latex_marker",
        "status",
        "notes",
    ]
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_report(rows: list[dict[str, str]]) -> None:
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    failures = [row for row in rows if row["status"] != "ok"]
    lines = [
        "# Evaluation Budget Consistency Audit",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Purpose:",
        "",
        "```text",
        "Check that main, appendix, and diagnostic tables keep their intended evaluation budgets.",
        "This audit prevents 300-episode main results, 100-episode appendix results, and smaller diagnostics from being mixed without labels.",
        "```",
        "",
        "## Summary",
        "",
        "| Item | Value |",
        "|---|---:|",
        f"| Budget groups checked | {len(rows)} |",
        f"| Failures | {len(failures)} |",
        "",
        "## Rows",
        "",
        "| Name | Rows | Episodes | LaTeX marker | Status | Notes |",
        "|---|---:|---:|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['name']}` | {row['actual_rows']} / {row['expected_rows']} | "
            f"{row['actual_episodes']} / {row['expected_episodes']} | "
            f"`{row['latex_marker']}` | {row['status']} | {row['notes']} |"
        )
    lines.extend(
        [
            "",
            "## Use Boundary",
            "",
            "```text",
            "Use this audit to keep evaluation-budget wording synchronized.",
            "Do not treat a smaller appendix diagnostic as equivalent to the final 300-episode main table.",
            "```",
            "",
        ]
    )
    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = [audit_spec(spec) for spec in SPECS]
    write_csv(rows)
    write_report(rows)
    print(OUT_CSV)
    print(OUT_REPORT)
    failures = [row for row in rows if row["status"] != "ok"]
    print(f"budget groups checked: {len(rows)}")
    print(f"failures: {len(failures)}")
    if failures:
        for row in failures:
            print(f"failed: {row['name']} {row['notes']}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
