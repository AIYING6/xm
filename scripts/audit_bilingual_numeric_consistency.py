from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / "results" / "bilingual_numeric_consistency_audit.csv"
OUT_MD = ROOT / "docs" / "bilingual_numeric_consistency_audit.md"


@dataclass(frozen=True)
class NumericSpec:
    claim_id: str
    source: str
    value: str
    english_file: str
    chinese_file: str
    note: str


EN_EXP = "paper_latex_en/sections/05_experiments.tex"
ZH_EXP = "paper_latex/sections/05_experiments.tex"
EN_APP = "paper_latex_en/sections/08_appendix_experiments.tex"
ZH_APP = "paper_latex/sections/08_appendix_experiments.tex"


def read_rows(rel: str) -> list[dict[str, str]]:
    with (ROOT / rel).open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def row_by(rows: list[dict[str, str]], **criteria: object) -> dict[str, str]:
    matches = []
    for row in rows:
        ok = True
        for key, value in criteria.items():
            if isinstance(value, float):
                ok = abs(float(row[key]) - value) < 1e-6
            else:
                ok = row[key] == str(value)
            if not ok:
                break
        if ok:
            matches.append(row)
    if len(matches) != 1:
        raise AssertionError(f"expected one row for {criteria}, got {len(matches)}")
    return matches[0]


def fmt(value: float) -> str:
    return f"{value:.3f}"


def specs_from_results() -> list[NumericSpec]:
    specs: list[NumericSpec] = []

    final_rows = read_rows("results/final_comm_300_summary.csv")
    for radius in [4.0, 6.0, 8.0, 10.0]:
        row = row_by(final_rows, method="EA-RG-MAPPO-S", radius=radius)
        for metric in ["success_mean", "collision_mean"]:
            specs.append(
                NumericSpec(
                    "C1",
                    "results/final_comm_300_summary.csv",
                    fmt(float(row[metric])),
                    EN_EXP,
                    ZH_EXP,
                    f"EA-RG-MAPPO-S radius {int(radius)} {metric}.",
                )
            )
    mappo_r4 = row_by(final_rows, method="MAPPO", radius=4.0)
    specs.append(NumericSpec("C1", "results/final_comm_300_summary.csv", fmt(float(mappo_r4["collision_mean"])), EN_EXP, ZH_EXP, "MAPPO radius 4 collision comparison."))

    paired_rows = read_rows("results/final_300_paired_statistics.csv")
    for baseline, radius, metric in [
        ("GAT-MAPPO", 4.0, "collision_reduction"),
        ("GAT-MAPPO", 8.0, "success_gain"),
        ("GAT-MAPPO", 8.0, "collision_reduction"),
    ]:
        row = row_by(paired_rows, baseline=baseline, radius=radius, metric=metric)
        specs.append(NumericSpec("C2", "results/final_300_paired_statistics.csv", fmt(float(row["ci95_low"])), EN_APP, ZH_APP, f"{baseline} radius {int(radius)} {metric} CI lower."))
        specs.append(NumericSpec("C2", "results/final_300_paired_statistics.csv", fmt(float(row["ci95_high"])), EN_APP, ZH_APP, f"{baseline} radius {int(radius)} {metric} CI upper."))

    dropout_rows = read_rows("results/comm_dropout_robustness_summary.csv")
    for radius in [4.0, 8.0]:
        for method in ["EA-RG-MAPPO-S", "MAPPO", "GAT-MAPPO"]:
            row = row_by(dropout_rows, method=method, radius=radius, comm_dropout_prob=0.5)
            specs.append(NumericSpec("C3", "results/comm_dropout_robustness_summary.csv", fmt(float(row["collision_mean"])), EN_APP, ZH_APP, f"{method} radius {int(radius)} dropout 0.50 collision."))

    aggregate_rows = read_rows("results/aggregate_robustness_summary.csv")
    for scope, method, metric in [
        ("final_cross_radius", "EA-RG-MAPPO-S", "mean_success"),
        ("final_cross_radius", "EA-RG-MAPPO-S", "mean_collision"),
        ("final_cross_radius", "EA-RG-MAPPO-S", "conservative_margin"),
        ("dropout_diagnostic", "EA-RG-MAPPO-S", "mean_success"),
        ("dropout_diagnostic", "EA-RG-MAPPO-S", "mean_collision"),
        ("dropout_diagnostic", "EA-RG-MAPPO-S", "conservative_margin"),
        ("dropout_diagnostic", "EA-RG-MAPPO-S", "worst_collision"),
        ("dropout_diagnostic", "MAPPO", "worst_collision"),
        ("dropout_diagnostic", "GAT-MAPPO", "worst_collision"),
    ]:
        row = row_by(aggregate_rows, scope=scope, method=method)
        specs.append(NumericSpec("C4", "results/aggregate_robustness_summary.csv", fmt(float(row[metric])), EN_APP, ZH_APP, f"{scope} {method} {metric}."))

    interp_rows = read_rows("results/radius_interpolation_summary.csv")
    for radius in [5.0, 7.0, 9.0]:
        for method in ["EA-RG-MAPPO-S", "MAPPO", "GAT-MAPPO"]:
            row = row_by(interp_rows, method=method, radius=radius)
            specs.append(NumericSpec("C5", "results/radius_interpolation_summary.csv", fmt(float(row["collision_mean"])), EN_APP, ZH_APP, f"{method} unseen radius {int(radius)} collision."))

    speed_rows = read_rows("results/speed_robustness_summary.csv")
    for radius in [4.0, 8.0]:
        for method in ["EA-RG-MAPPO-S", "MAPPO", "GAT-MAPPO"]:
            row = row_by(speed_rows, method=method, radius=radius, target_speed=0.9)
            specs.append(NumericSpec("C6", "results/speed_robustness_summary.csv", fmt(float(row["collision_mean"])), EN_APP, ZH_APP, f"{method} radius {int(radius)} target_speed 0.90 collision."))

    specs.append(NumericSpec("C9", "docs/english_experiments_draft.md", "0.587", EN_EXP, ZH_EXP, "Intent plain accuracy."))
    specs.append(NumericSpec("C9", "docs/english_experiments_draft.md", "0.200", EN_EXP, ZH_EXP, "Intent balanced accuracy."))
    return specs


def check_spec(spec: NumericSpec) -> dict[str, str]:
    en_text = (ROOT / spec.english_file).read_text(encoding="utf-8")
    zh_text = (ROOT / spec.chinese_file).read_text(encoding="utf-8")
    en_ok = spec.value in en_text
    zh_ok = spec.value in zh_text
    status = "ok" if en_ok and zh_ok else "failed"
    missing = []
    if not en_ok:
        missing.append("english")
    if not zh_ok:
        missing.append("chinese")
    return {
        "claim_id": spec.claim_id,
        "source": spec.source,
        "value": spec.value,
        "english_file": spec.english_file,
        "chinese_file": spec.chinese_file,
        "status": status,
        "notes": spec.note if status == "ok" else f"{spec.note} Missing in: {','.join(missing)}",
    }


def write_csv(rows: list[dict[str, str]]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fields = ["claim_id", "source", "value", "english_file", "chinese_file", "status", "notes"]
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_report(rows: list[dict[str, str]]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    failures = [row for row in rows if row["status"] != "ok"]
    by_claim: dict[str, int] = {}
    for row in rows:
        by_claim[row["claim_id"]] = by_claim.get(row["claim_id"], 0) + 1
    lines = [
        "# Bilingual Numeric Consistency Audit",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Purpose:",
        "",
        "```text",
        "Check that key numeric values derived from result CSVs appear in both Chinese and English LaTeX manuscript sources.",
        "This audit catches manual manuscript edits that desynchronize reported numbers from result files.",
        "```",
        "",
        "## Summary",
        "",
        "```text",
        f"numeric_markers_checked = {len(rows)}",
        f"failures = {len(failures)}",
        *[f"{claim_id} = {count}" for claim_id, count in sorted(by_claim.items())],
        "```",
        "",
        "## Rows",
        "",
        "| Claim | Source | Value | Status | Notes |",
        "|---|---|---:|---|---|",
    ]
    for row in rows:
        lines.append(f"| {row['claim_id']} | `{row['source']}` | {row['value']} | {row['status']} | {row['notes']} |")
    if failures:
        lines.extend(["", "## Failures", ""])
        for row in failures:
            lines.append(f"- {row['claim_id']} value `{row['value']}`: {row['notes']}")
    lines.extend(
        [
            "",
            "## Use Boundary",
            "",
            "```text",
            "Passing this audit means the selected key numbers are present in both manuscript languages.",
            "It does not replace full proofreading, PDF layout inspection, or journal-specific formatting checks.",
            "```",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = [check_spec(spec) for spec in specs_from_results()]
    write_csv(rows)
    write_report(rows)
    failures = [row for row in rows if row["status"] != "ok"]
    print(OUT_CSV)
    print(OUT_MD)
    print(f"numeric markers checked: {len(rows)}")
    print(f"failures: {len(failures)}")
    if failures:
        for row in failures:
            print(f"failed: {row['claim_id']} value={row['value']} {row['notes']}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
