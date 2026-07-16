from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / "results" / "method_naming_audit.csv"
OUT_REPORT = ROOT / "docs" / "method_naming_audit.md"


PUBLISHABLE_FILES = [
    "paper_latex/main.tex",
    "paper_latex/sections/01_introduction.tex",
    "paper_latex/sections/02_related_work.tex",
    "paper_latex/sections/03_problem.tex",
    "paper_latex/sections/04_method.tex",
    "paper_latex/sections/05_experiments.tex",
    "paper_latex/sections/06_discussion.tex",
    "paper_latex/sections/07_conclusion.tex",
    "paper_latex/sections/08_appendix_experiments.tex",
    "paper_latex_en/main.tex",
    "paper_latex_en/sections/01_introduction.tex",
    "paper_latex_en/sections/02_related_work.tex",
    "paper_latex_en/sections/03_problem.tex",
    "paper_latex_en/sections/04_method.tex",
    "paper_latex_en/sections/05_experiments.tex",
    "paper_latex_en/sections/06_discussion.tex",
    "paper_latex_en/sections/07_conclusion.tex",
    "paper_latex_en/sections/08_appendix_experiments.tex",
    "docs/paper_manuscript_zh_v1.md",
    "docs/english_abstract_and_contributions.md",
    "docs/english_introduction_draft.md",
    "docs/english_related_work_draft.md",
    "docs/english_problem_method_draft.md",
    "docs/english_experiments_draft.md",
    "docs/english_discussion_conclusion_draft.md",
    "docs/english_manuscript_draft.md",
]

MAPPING_FILES = [
    "docs/reproducibility_manifest.md",
    "docs/checkpoint_inventory.md",
    "docs/submission_readiness_checklist.md",
]

FINAL_NAME = "EA-RG-MAPPO-S"
REQUIRED_METHOD_MARKERS = [
    "EA-RG-MAPPO-S",
    "GAT-MAPPO",
    "MAPPO",
]
OLD_METHOD_MARKERS = [
    "RI-GMAPPO",
    "RI edge",
    "RI no-edge",
]
REQUIRED_MAPPING_MARKERS = [
    "EA-RG-MAPPO-S",
    "ri_gmappo_edge_stage2_rand_seed0_20",
    "ri_gmappo_edge_stage2_rand_seed1_20",
    "ri_gmappo_edge_stage2_rand_seed2_20",
]


@dataclass(frozen=True)
class NamingAuditRow:
    file: str
    final_name_count: int
    old_name_count: int
    required_marker_missing: str
    status: str
    notes: str


def read_text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="ignore")


def count_any(text: str, markers: list[str]) -> int:
    return sum(text.count(marker) for marker in markers)


def audit_publishable_file(rel: str) -> NamingAuditRow:
    text = read_text(rel)
    old_count = count_any(text, OLD_METHOD_MARKERS)
    notes = []
    if old_count:
        notes.append("old_method_markers_present")
    return NamingAuditRow(
        file=rel,
        final_name_count=text.count(FINAL_NAME),
        old_name_count=old_count,
        required_marker_missing="",
        status="ok" if old_count == 0 else "failed",
        notes="; ".join(notes) if notes else "publishable naming ok",
    )


def audit_publishable_bundle() -> NamingAuditRow:
    text = "\n".join(read_text(rel) for rel in PUBLISHABLE_FILES)
    missing = [marker for marker in REQUIRED_METHOD_MARKERS if marker not in text]
    old_count = count_any(text, OLD_METHOD_MARKERS)
    return NamingAuditRow(
        file="publishable_bundle",
        final_name_count=text.count(FINAL_NAME),
        old_name_count=old_count,
        required_marker_missing=";".join(missing) if missing else "",
        status="ok" if not missing and old_count == 0 else "failed",
        notes="required method names present across publishable bundle" if not missing else "missing bundle markers",
    )


def audit_mapping_files() -> NamingAuditRow:
    text = "\n".join(read_text(rel) for rel in MAPPING_FILES)
    missing = [marker for marker in REQUIRED_MAPPING_MARKERS if marker not in text]
    return NamingAuditRow(
        file="mapping_docs",
        final_name_count=text.count(FINAL_NAME),
        old_name_count=count_any(text, OLD_METHOD_MARKERS),
        required_marker_missing=";".join(missing) if missing else "",
        status="ok" if not missing else "failed",
        notes="code-directory mapping present" if not missing else "missing mapping markers",
    )


def compute_rows() -> list[NamingAuditRow]:
    return [audit_publishable_file(rel) for rel in PUBLISHABLE_FILES] + [
        audit_publishable_bundle(),
        audit_mapping_files(),
    ]


def write_csv(rows: list[NamingAuditRow]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "file",
        "final_name_count",
        "old_name_count",
        "required_marker_missing",
        "status",
        "notes",
    ]
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "file": row.file,
                    "final_name_count": row.final_name_count,
                    "old_name_count": row.old_name_count,
                    "required_marker_missing": row.required_marker_missing,
                    "status": row.status,
                    "notes": row.notes,
                }
            )


def write_report(rows: list[NamingAuditRow]) -> None:
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    failures = [row for row in rows if row.status != "ok"]
    publishable = [row for row in rows if row.file != "mapping_docs"]
    lines = [
        "# Method Naming Consistency Audit",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Purpose:",
        "",
        "```text",
        "Ensure publishable manuscripts consistently use EA-RG-MAPPO-S as the final method name.",
        "Historical RI-GMAPPO names are allowed in workflow logs and code paths, but not in publishable drafts.",
        "The reproducibility mapping must still record the code directory names for traceability.",
        "```",
        "",
        "## Summary",
        "",
        "| Item | Value |",
        "|---|---:|",
        f"| Publishable files checked | {len(publishable)} |",
        f"| Mapping checks | 1 |",
        f"| Failures | {len(failures)} |",
        "",
        "## Rows",
        "",
        "| File | Final name count | Old marker count | Status | Notes |",
        "|---|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row.file}` | {row.final_name_count} | {row.old_name_count} | {row.status} | {row.notes} |"
        )
    lines.extend(
        [
            "",
            "## Naming Rule",
            "",
            "```text",
            "Paper method name: EA-RG-MAPPO-S.",
            "Allowed code/result directory stem: ri_gmappo_edge_stage2_rand_seed*_20.",
            "Old route names such as RI-GMAPPO or RI edge may remain only in internal history logs.",
            "```",
            "",
        ]
    )
    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = compute_rows()
    write_csv(rows)
    write_report(rows)
    failures = [row for row in rows if row.status != "ok"]
    print(OUT_CSV)
    print(OUT_REPORT)
    print(f"naming rows checked: {len(rows)}")
    print(f"failures: {len(failures)}")
    if failures:
        for row in failures:
            print(f"failed: {row.file} {row.notes}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
