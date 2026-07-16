from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / "results" / "latex_reference_integrity_audit.csv"
OUT_MD = ROOT / "docs" / "latex_reference_integrity_audit.md"


@dataclass(frozen=True)
class ProjectSpec:
    name: str
    path: Path
    required_labels: tuple[str, ...]
    required_refs: tuple[str, ...]


BASE_TABLE_LABELS = (
    "tab:training_settings",
    "tab:final_comm_300_results",
    "tab:ablation_results",
    "tab:final_300_paired_ci",
    "tab:comm_dropout_robustness",
    "tab:comm_dropout_paired_ci",
    "tab:aggregate_robustness",
    "tab:radius_interpolation",
    "tab:speed_robustness",
    "tab:edge_feature_masking",
)

EN_FIG_LABELS = (
    "fig:method_overview_en",
    "fig:final_success_en",
    "fig:final_collision_en",
    "fig:comm_dropout_success_en",
    "fig:comm_dropout_collision_en",
    "fig:radius_interp_success_en",
    "fig:radius_interp_collision_en",
    "fig:speed_success_r4_en",
    "fig:speed_collision_r4_en",
    "fig:speed_success_r8_en",
    "fig:speed_collision_r8_en",
    "fig:edge_feature_delta_en",
)

ZH_FIG_LABELS = (
    "fig:method_overview",
    "fig:final_success",
    "fig:final_collision",
    "fig:comm_dropout_success",
    "fig:comm_dropout_collision",
    "fig:radius_interp_success",
    "fig:radius_interp_collision",
    "fig:speed_success_r4",
    "fig:speed_collision_r4",
    "fig:speed_success_r8",
    "fig:speed_collision_r8",
    "fig:edge_feature_delta",
)

PROJECTS = [
    ProjectSpec(
        name="english",
        path=ROOT / "paper_latex_en",
        required_labels=(*BASE_TABLE_LABELS, *EN_FIG_LABELS),
        required_refs=(
            "tab:training_settings",
            "tab:final_comm_300_results",
            "tab:ablation_results",
            "tab:final_300_paired_ci",
            "tab:comm_dropout_robustness",
            "tab:comm_dropout_paired_ci",
            "tab:aggregate_robustness",
            "tab:radius_interpolation",
            "tab:speed_robustness",
            "tab:edge_feature_masking",
            "fig:method_overview_en",
            "fig:final_success_en",
            "fig:final_collision_en",
            "fig:comm_dropout_success_en",
            "fig:comm_dropout_collision_en",
            "fig:radius_interp_success_en",
            "fig:radius_interp_collision_en",
            "fig:speed_success_r4_en",
            "fig:speed_collision_r8_en",
            "fig:edge_feature_delta_en",
        ),
    ),
    ProjectSpec(
        name="chinese",
        path=ROOT / "paper_latex",
        required_labels=(*BASE_TABLE_LABELS, *ZH_FIG_LABELS),
        required_refs=(
            "tab:final_comm_300_results",
            "tab:final_300_paired_ci",
            "tab:comm_dropout_robustness",
            "tab:comm_dropout_paired_ci",
            "tab:aggregate_robustness",
            "tab:radius_interpolation",
            "tab:speed_robustness",
            "tab:edge_feature_masking",
            "fig:method_overview",
            "fig:final_success",
            "fig:final_collision",
            "fig:comm_dropout_success",
            "fig:comm_dropout_collision",
            "fig:radius_interp_success",
            "fig:radius_interp_collision",
            "fig:speed_success_r4",
            "fig:speed_collision_r8",
            "fig:edge_feature_delta",
        ),
    ),
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def resolve_input(project: Path, base_path: Path, ref: str) -> Path | None:
    raw = Path(ref)
    candidates = [
        (base_path.parent / raw).with_suffix(".tex"),
        (project / raw).with_suffix(".tex"),
        (ROOT / raw).with_suffix(".tex"),
    ]
    if base_path == project / "main.tex":
        candidates.insert(0, (project / f"{ref}.tex"))
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return None


def collect_tex_files(project: Path) -> list[Path]:
    initial = [project / "main.tex", *sorted((project / "sections").glob("*.tex"))]
    seen = {path.resolve() for path in initial}
    queue = [path.resolve() for path in initial]
    while queue:
        path = queue.pop(0)
        for ref in re.findall(r"\\input\{([^}]+)\}", read(path)):
            candidate = resolve_input(project, path, ref)
            if candidate is not None and candidate not in seen:
                seen.add(candidate)
                queue.append(candidate)
    return sorted(seen)


def scan_project(spec: ProjectSpec) -> tuple[list[dict[str, str]], int, int]:
    files = collect_tex_files(spec.path)
    texts = [(path, read(path)) for path in files]
    labels: list[str] = []
    refs: list[str] = []
    for _, text in texts:
        labels.extend(re.findall(r"\\label\{([^}]+)\}", text))
        refs.extend(re.findall(r"\\(?:ref|eqref)\{([^}]+)\}", text))

    label_set = set(labels)
    ref_set = set(refs)
    rows: list[dict[str, str]] = []

    dupes = sorted({label for label in labels if labels.count(label) > 1})
    rows.append(
        {
            "project": spec.name,
            "check_type": "duplicate_labels",
            "item": "all_labels",
            "status": "ok" if not dupes else "failed",
            "notes": "no duplicate labels" if not dupes else ",".join(dupes),
        }
    )
    missing_ref_targets = sorted(ref_set - label_set)
    rows.append(
        {
            "project": spec.name,
            "check_type": "missing_ref_targets",
            "item": "all_refs",
            "status": "ok" if not missing_ref_targets else "failed",
            "notes": "all refs resolve to labels" if not missing_ref_targets else ",".join(missing_ref_targets),
        }
    )

    for label in spec.required_labels:
        rows.append(
            {
                "project": spec.name,
                "check_type": "required_label",
                "item": label,
                "status": "ok" if label in label_set else "failed",
                "notes": "label present" if label in label_set else "label missing",
            }
        )
    for ref in spec.required_refs:
        rows.append(
            {
                "project": spec.name,
                "check_type": "required_ref",
                "item": ref,
                "status": "ok" if ref in ref_set else "failed",
                "notes": "reference present" if ref in ref_set else "reference missing",
            }
        )
    return rows, len(files), len(label_set)


def write_csv(rows: list[dict[str, str]]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fields = ["project", "check_type", "item", "status", "notes"]
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_report(rows: list[dict[str, str]], project_counts: dict[str, tuple[int, int]]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    failures = [row for row in rows if row["status"] != "ok"]
    lines = [
        "# LaTeX Reference Integrity Audit",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Purpose:",
        "",
        "```text",
        "Check that Chinese and English LaTeX projects keep required table/figure labels and manuscript references intact.",
        "This audit complements the broader LaTeX static check by recording publishable evidence labels as an explicit artifact.",
        "```",
        "",
        "## Summary",
        "",
        "```text",
        f"reference_checks = {len(rows)}",
        f"failures = {len(failures)}",
    ]
    for project, (tex_count, label_count) in sorted(project_counts.items()):
        lines.append(f"{project}_tex_files = {tex_count}")
        lines.append(f"{project}_labels = {label_count}")
    lines.extend(
        [
            "```",
            "",
            "## Rows",
            "",
            "| Project | Type | Item | Status | Notes |",
            "|---|---|---|---|---|",
        ]
    )
    for row in rows:
        lines.append(f"| {row['project']} | {row['check_type']} | `{row['item']}` | {row['status']} | {row['notes']} |")
    if failures:
        lines.extend(["", "## Failures", ""])
        for row in failures:
            lines.append(f"- {row['project']} {row['check_type']} `{row['item']}`: {row['notes']}")
    lines.extend(
        [
            "",
            "## Use Boundary",
            "",
            "```text",
            "Passing this audit means key evidence table/figure labels and references exist in source LaTeX.",
            "It does not replace PDF compilation and visual layout inspection.",
            "```",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows: list[dict[str, str]] = []
    project_counts: dict[str, tuple[int, int]] = {}
    for spec in PROJECTS:
        project_rows, tex_count, label_count = scan_project(spec)
        rows.extend(project_rows)
        project_counts[spec.name] = (tex_count, label_count)
    write_csv(rows)
    write_report(rows, project_counts)
    failures = [row for row in rows if row["status"] != "ok"]
    print(OUT_CSV)
    print(OUT_MD)
    print(f"reference checks: {len(rows)}")
    print(f"failures: {len(failures)}")
    if failures:
        for row in failures:
            print(f"failed: {row['project']} {row['check_type']} {row['item']} {row['notes']}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
