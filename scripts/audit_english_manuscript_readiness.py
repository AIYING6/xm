from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper_latex_3d_en"
OUT = ROOT / "docs" / "english_manuscript_readiness_audit.md"


SECTION_FILES = [
    "main.tex",
    "sections/01_introduction.tex",
    "sections/02_related_work.tex",
    "sections/03_problem.tex",
    "sections/04_method.tex",
    "sections/05_experiments.tex",
    "sections/06_discussion.tex",
    "sections/07_conclusion.tex",
]


PUBLISHABLE_SECTION_FILES = [
    "sections/01_introduction.tex",
    "sections/02_related_work.tex",
    "sections/03_problem.tex",
    "sections/04_method.tex",
    "sections/05_experiments.tex",
    "sections/06_discussion.tex",
    "sections/07_conclusion.tex",
]


REQUIRED_BOUNDARY_MARKERS = [
    "training protocol in this paper, not as a primary contribution",
    "nor does it claim full-system 4v2 red-blue air-combat validity",
    "Instead of directly training all baselines in a full 6DOF JSBSim environment",
    "future scenario-depth work",
]


REQUIRED_EVIDENCE_MARKERS = [
    "fixed-budget checkpoint rule",
    "five training seeds",
    "100 matched test episodes per seed",
    "hierarchical bootstrap",
    "88.6\\%",
    "role-pair-conditioned message gating",
    "100 matched test episodes per seed",
]


@dataclass(frozen=True)
class FileStats:
    rel: str
    lines: int
    words: int
    tables: int
    figures: int
    citations: int


def read(rel: str) -> str:
    return (PAPER / rel).read_text(encoding="utf-8")


def strip_latex(text: str) -> str:
    text = re.sub(r"%.*", " ", text)
    text = re.sub(r"\\(?:cite|ref|eqref|label|input|includegraphics)(?:\[[^\]]*\])?\{[^}]*\}", " ", text)
    text = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{([^{}]*)\})?", r" \1 ", text)
    text = re.sub(r"[{}_$^&~]", " ", text)
    return text


def word_count(text: str) -> int:
    stripped = strip_latex(text)
    return len(re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)?", stripped))


def extract_command(text: str, name: str) -> str:
    match = re.search(rf"\\{name}\{{(.+?)\}}", text, flags=re.DOTALL)
    return match.group(1).strip() if match else ""


def extract_environment(text: str, env: str) -> str:
    match = re.search(rf"\\begin\{{{env}\}}(.+?)\\end\{{{env}\}}", text, flags=re.DOTALL)
    return match.group(1).strip() if match else ""


def collect_stats() -> list[FileStats]:
    stats = []
    for rel in SECTION_FILES:
        text = read(rel)
        stats.append(
            FileStats(
                rel=rel,
                lines=len(text.splitlines()),
                words=word_count(text),
                tables=len(re.findall(r"\\begin\{table", text)) + len(re.findall(r"\\input\{../results/", text)),
                figures=len(re.findall(r"\\begin\{figure", text)),
                citations=len(re.findall(r"\\cite\{", text)),
            )
        )
    return stats


def make_report() -> tuple[str, list[str]]:
    main = read("main.tex")
    full_text = "\n".join(read(rel) for rel in SECTION_FILES)
    publishable_text = "\n".join(read(rel) for rel in PUBLISHABLE_SECTION_FILES)

    title = extract_command(main, "title")
    author = extract_command(main, "author")
    abstract = extract_environment(main, "abstract")
    keywords = re.search(r"\\textbf\{Keywords:\}(.+)", main)
    keyword_text = keywords.group(1).strip() if keywords else ""
    stats = collect_stats()

    hard_errors: list[str] = []
    action_items: list[str] = []
    notes: list[str] = []

    missing_files = [rel for rel in SECTION_FILES if not (PAPER / rel).exists()]
    if missing_files:
        hard_errors.extend(f"missing file: {rel}" for rel in missing_files)
    if not title:
        hard_errors.append("missing title")
    if not abstract:
        hard_errors.append("missing abstract")
    if not keyword_text:
        hard_errors.append("missing keywords")

    title_words = word_count(title)
    abstract_words = word_count(abstract)
    publishable_words = word_count(publishable_text)
    total_words = word_count(full_text)

    if "To be completed" in author:
        action_items.append("Replace the author placeholder in paper_latex_3d_en/main.tex.")
    if abstract_words > 300:
        action_items.append(f"Shorten the abstract from {abstract_words} words to about 180-250 words.")
    elif abstract_words < 150:
        action_items.append(f"Expand the abstract from {abstract_words} words to about 180-250 words.")
    if title_words > 18:
        action_items.append(f"Shorten the title from {title_words} words if the selected journal prefers concise titles.")
    if publishable_words < 2500:
        action_items.append(f"The main text is only {publishable_words} words; expand related work or discussion before submission.")
    if publishable_words > 7000:
        action_items.append(f"The main text is {publishable_words} words; compress before journal template migration.")
    if "\\section*{Data Availability}" not in full_text and "Data Availability" not in full_text:
        action_items.append("Add a Data/Code Availability statement after the target journal is selected.")
    if "\\section*{Funding}" not in full_text and "Funding" not in full_text:
        action_items.append("Add funding, conflict-of-interest, and author-contribution statements if required by the journal.")
    if "\\bibliographystyle{plain}" in main:
        action_items.append("Replace the generic plain bibliography style with the selected journal template style.")

    for marker in REQUIRED_BOUNDARY_MARKERS:
        if marker not in full_text:
            hard_errors.append(f"missing evidence-boundary marker: {marker}")
    for marker in REQUIRED_EVIDENCE_MARKERS:
        if marker not in full_text:
            hard_errors.append(f"missing evidence marker: {marker}")

    combat_terms = len(re.findall(r"\bair-combat\b|\bmissile\b|\bradar\b|\bhuman-UAV\b", full_text, flags=re.IGNORECASE))
    if combat_terms:
        notes.append(
            f"Air-combat/radar/missile/human-UAV terms occur {combat_terms} times; keep them in limitations/future-work context."
        )
    notes.append("PDF rendering is not verified in the current runtime because xelatex/latexmk/bibtex are unavailable.")

    lines = [
        "# English Manuscript Readiness Audit",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Purpose:",
        "",
        "```text",
        "Audit the English LaTeX manuscript for submission-facing structure, evidence boundaries, and low-cost action items.",
        "This report does not replace journal-template compilation or adviser review.",
        "```",
        "",
        "## Summary",
        "",
        "| Item | Value |",
        "|---|---:|",
        f"| Title words | {title_words} |",
        f"| Abstract words | {abstract_words} |",
        f"| Main-text words, excluding appendix | {publishable_words} |",
        f"| Total words, including appendix | {total_words} |",
        f"| LaTeX files checked | {len(stats)} |",
        f"| Hard errors | {len(hard_errors)} |",
        f"| Action items | {len(action_items)} |",
        "",
        "## File Statistics",
        "",
        "| File | Lines | Words | Tables/inputs | Figures | Cite commands |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for item in stats:
        lines.append(
            f"| `{item.rel}` | {item.lines} | {item.words} | "
            f"{item.tables} | {item.figures} | {item.citations} |"
        )

    lines.extend(["", "## Hard Errors", ""])
    if hard_errors:
        lines.extend(f"- {err}" for err in hard_errors)
    else:
        lines.append("None.")

    lines.extend(["", "## Submission Action Items", ""])
    if action_items:
        lines.extend(f"- {item}" for item in action_items)
    else:
        lines.append("None.")

    lines.extend(["", "## Notes", ""])
    lines.extend(f"- {note}" for note in notes)

    lines.extend(
        [
            "",
            "## Recommended Next Edit",
            "",
            "```text",
            "For Drones/Aerospace/JIRS first submission: keep the current 3DOF Gate 1 technical core, replace the generic article class with the target template,",
            "add required declarations, and avoid turning future 6DOF/radar/missile extensions into current experimental claims.",
            "```",
            "",
        ]
    )
    return "\n".join(lines), hard_errors


def main() -> None:
    report, hard_errors = make_report()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(report, encoding="utf-8")
    print(OUT)
    if hard_errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
