from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / "results" / "bilingual_manuscript_completeness_audit.csv"
OUT_MD = ROOT / "docs" / "bilingual_manuscript_completeness_audit.md"


SECTION_FILES = [
    "sections/01_introduction.tex",
    "sections/02_related_work.tex",
    "sections/03_problem.tex",
    "sections/04_method.tex",
    "sections/05_experiments.tex",
    "sections/06_discussion.tex",
    "sections/07_conclusion.tex",
    "sections/08_appendix_experiments.tex",
]


@dataclass(frozen=True)
class ProjectSpec:
    name: str
    path: Path
    author_placeholder: str
    keyword_marker: str
    min_main_words: int
    required_markers: tuple[str, ...]


PROJECTS = [
    ProjectSpec(
        name="english",
        path=ROOT / "paper_latex_en",
        author_placeholder="To be completed",
        keyword_marker="Keywords:",
        min_main_words=2500,
        required_markers=(
            "EA-RG-MAPPO-S",
            "300 evaluation episodes per seed",
            "not used as a main contribution",
            "not be treated as a full air-combat system",
        ),
    ),
    ProjectSpec(
        name="chinese",
        path=ROOT / "paper_latex",
        author_placeholder="待补充",
        keyword_marker="关键词：",
        min_main_words=1800,
        required_markers=(
            "EA-RG-MAPPO-S",
            "每种子 300 回合",
            "不作为本文主贡献",
            "不能被写成完整 6DOF 空战验证",
        ),
    ),
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def strip_latex(text: str) -> str:
    text = re.sub(r"%.*", " ", text)
    text = re.sub(r"\\(?:cite|ref|eqref|label|input|includegraphics)(?:\[[^\]]*\])?\{[^}]*\}", " ", text)
    text = re.sub(r"\\[a-zA-Z]+?\*?(?:\[[^\]]*\])?(?:\{([^{}]*)\})?", r" \1 ", text)
    text = re.sub(r"[{}_$^&~]", " ", text)
    return text


def lexical_count(text: str, language: str) -> int:
    stripped = strip_latex(text)
    english_words = re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)?", stripped)
    if language == "english":
        return len(english_words)
    chinese_chars = re.findall(r"[\u4e00-\u9fff]", stripped)
    return len(chinese_chars) + len(english_words)


def extract_command(text: str, command: str) -> str:
    match = re.search(rf"\\{command}\{{(.+?)\}}", text, flags=re.DOTALL)
    return match.group(1).strip() if match else ""


def extract_environment(text: str, env: str) -> str:
    match = re.search(rf"\\begin\{{{env}\}}(.+?)\\end\{{{env}\}}", text, flags=re.DOTALL)
    return match.group(1).strip() if match else ""


def row(project: str, check: str, value: str, status: str, notes: str) -> dict[str, str]:
    return {
        "project": project,
        "check": check,
        "value": value,
        "status": status,
        "notes": notes,
    }


def audit_project(spec: ProjectSpec) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    main_path = spec.path / "main.tex"
    if not main_path.exists():
        return [row(spec.name, "main_file", "missing", "failed", "main.tex is missing")]

    main_text = read(main_path)
    section_texts: list[str] = []
    missing_sections = []
    for rel in SECTION_FILES:
        path = spec.path / rel
        if path.exists() and path.stat().st_size > 0:
            section_texts.append(read(path))
        else:
            missing_sections.append(rel)

    full_text = "\n".join([main_text, *section_texts])
    main_body_text = "\n".join(section_texts[:-1])
    title = extract_command(main_text, "title")
    author = extract_command(main_text, "author")
    abstract = extract_environment(main_text, "abstract")
    main_count = lexical_count(main_body_text, spec.name)
    total_count = lexical_count(full_text, spec.name)
    table_inputs = len(re.findall(r"\\input\{../results/latex_", full_text))
    figures = len(re.findall(r"\\begin\{figure", full_text))
    citations = len(re.findall(r"\\cite\{", full_text))

    rows.append(row(spec.name, "main_file", "present", "ok", "main.tex exists and is nonempty"))
    rows.append(
        row(
            spec.name,
            "section_files",
            f"{len(SECTION_FILES) - len(missing_sections)}/{len(SECTION_FILES)}",
            "ok" if not missing_sections else "failed",
            "all expected section files present" if not missing_sections else "missing: " + ",".join(missing_sections),
        )
    )
    rows.append(row(spec.name, "title", str(lexical_count(title, spec.name)), "ok" if title else "failed", "title present" if title else "title missing"))
    rows.append(
        row(
            spec.name,
            "author",
            author or "missing",
            "action_item" if spec.author_placeholder in author else ("ok" if author else "failed"),
            "replace author placeholder before submission" if spec.author_placeholder in author else ("author present" if author else "author missing"),
        )
    )
    abstract_count = lexical_count(abstract, spec.name)
    rows.append(
        row(
            spec.name,
            "abstract",
            str(abstract_count),
            "ok" if abstract_count >= (150 if spec.name == "english" else 250) else "failed",
            "abstract present with reasonable length",
        )
    )
    rows.append(
        row(
            spec.name,
            "keywords",
            "present" if spec.keyword_marker in main_text else "missing",
            "ok" if spec.keyword_marker in main_text else "failed",
            "keyword line present" if spec.keyword_marker in main_text else "keyword line missing",
        )
    )
    rows.append(
        row(
            spec.name,
            "main_body_size",
            str(main_count),
            "ok" if main_count >= spec.min_main_words else "action_item",
            f"main text lexical count target >= {spec.min_main_words}",
        )
    )
    rows.append(row(spec.name, "total_size", str(total_count), "ok", "total lexical count including appendix"))
    rows.append(row(spec.name, "result_table_inputs", str(table_inputs), "ok" if table_inputs >= 9 else "failed", "result table inputs present"))
    rows.append(row(spec.name, "figures", str(figures), "ok" if figures >= 10 else "failed", "figure environments present"))
    rows.append(row(spec.name, "citations", str(citations), "ok" if citations >= 8 else "action_item", "citation commands present"))
    rows.append(
        row(
            spec.name,
            "bibliography_style",
            "plain" if "\\bibliographystyle{plain}" in main_text else "custom",
            "action_item" if "\\bibliographystyle{plain}" in main_text else "ok",
            "replace generic bibliography style after target journal is selected" if "\\bibliographystyle{plain}" in main_text else "journal-specific bibliography style present",
        )
    )
    rows.append(
        row(
            spec.name,
            "data_availability",
            "present" if "Data Availability" in full_text or "数据可用" in full_text else "missing",
            "action_item",
            "add data/code availability statement after journal target is selected",
        )
    )
    rows.append(
        row(
            spec.name,
            "funding_conflict_statement",
            "present" if "Funding" in full_text or "基金" in full_text else "missing",
            "action_item",
            "add funding/conflict/author contribution declarations if required",
        )
    )

    for marker in spec.required_markers:
        rows.append(
            row(
                spec.name,
                "required_marker",
                marker,
                "ok" if marker in full_text else "failed",
                "required manuscript marker present" if marker in full_text else "required manuscript marker missing",
            )
        )
    return rows


def write_csv(rows: list[dict[str, str]]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fields = ["project", "check", "value", "status", "notes"]
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_report(rows: list[dict[str, str]]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    failures = [r for r in rows if r["status"] == "failed"]
    action_items = [r for r in rows if r["status"] == "action_item"]
    lines = [
        "# Bilingual Manuscript Completeness Audit",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Purpose:",
        "",
        "```text",
        "Check Chinese and English LaTeX manuscript completeness before journal-template migration.",
        "Action items are submission tasks that should be resolved after author and target-journal details are known.",
        "```",
        "",
        "## Summary",
        "",
        "```text",
        f"checks = {len(rows)}",
        f"failures = {len(failures)}",
        f"action_items = {len(action_items)}",
        "```",
        "",
        "## Rows",
        "",
        "| Project | Check | Value | Status | Notes |",
        "|---|---|---:|---|---|",
    ]
    for item in rows:
        lines.append(f"| {item['project']} | {item['check']} | {item['value']} | {item['status']} | {item['notes']} |")
    if failures:
        lines.extend(["", "## Failures", ""])
        for item in failures:
            lines.append(f"- {item['project']} {item['check']}: {item['notes']}")
    if action_items:
        lines.extend(["", "## Action Items", ""])
        for item in action_items:
            lines.append(f"- {item['project']} {item['check']}: {item['notes']}")
    lines.extend(
        [
            "",
            "## Use Boundary",
            "",
            "```text",
            "Passing this audit means the manuscript source is structurally complete enough for continued drafting.",
            "It does not replace PDF rendering, adviser review, or target-journal template migration.",
            "```",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows: list[dict[str, str]] = []
    for spec in PROJECTS:
        rows.extend(audit_project(spec))
    write_csv(rows)
    write_report(rows)
    failures = [r for r in rows if r["status"] == "failed"]
    action_items = [r for r in rows if r["status"] == "action_item"]
    print(OUT_CSV)
    print(OUT_MD)
    print(f"checks: {len(rows)}")
    print(f"failures: {len(failures)}")
    print(f"action items: {len(action_items)}")
    if failures:
        for item in failures:
            print(f"failed: {item['project']} {item['check']} {item['notes']}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
