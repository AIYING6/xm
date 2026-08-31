"""Audit the standalone English DRTP manuscript against its frozen evidence boundary.

This checker is intentionally separate from ``audit_english_manuscript_readiness.py``:
the latter targets the legacy EA-RG-MAPPO air-combat manuscript and must not be
used as evidence for the relay-failure DRTP paper.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper" / "q2_final_en"
REPORT = PAPER / "09_internal_audit.md"

SECTION_FILES = {
    "editorial canon": "00_editorial_canon.md",
    "abstract": "01_abstract.md",
    "problem formulation": "02_problem_formulation.md",
    "introduction and related work": "03_introduction_related_work.md",
    "method": "04_method.md",
    "experiments": "05_experiments.md",
    "discussion": "06_discussion.md",
    "conclusion": "07_conclusion.md",
    "references": "08_references.md",
    "supplementary information": "11_supplementary_information.md",
}


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    detail: str


def words(text: str) -> int:
    return len(re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)?", text))


def markdown_citations(text: str) -> set[int]:
    citations: set[int] = set()
    for bracket in re.findall(r"\[([0-9][0-9,\-\s]*)\]", text):
        for token in re.split(r",\s*", bracket):
            if "--" in token:
                start, end = token.split("--", maxsplit=1)
                citations.update(range(int(start), int(end) + 1))
            else:
                citations.add(int(token))
    return citations


def add_marker_check(
    checks: list[Check],
    name: str,
    haystack: str,
    marker: str,
    hard_errors: list[str],
) -> None:
    if marker in haystack:
        checks.append(Check(name, "PASS", f"found `{marker}`"))
    else:
        checks.append(Check(name, "FAIL", f"missing `{marker}`"))
        hard_errors.append(name)


def main() -> None:
    texts: dict[str, str] = {}
    hard_errors: list[str] = []
    warnings: list[str] = []
    checks: list[Check] = []

    for name, relative in SECTION_FILES.items():
        path = PAPER / relative
        if not path.exists():
            hard_errors.append(f"missing {relative}")
            checks.append(Check(f"file: {name}", "FAIL", f"missing `{relative}`"))
            continue
        texts[name] = path.read_text(encoding="utf-8")
        checks.append(Check(f"file: {name}", "PASS", relative))

    if hard_errors:
        write_report(checks, hard_errors, warnings, texts)
        raise SystemExit(1)

    manuscript = "\n".join(texts.values())
    primary = "\n".join(
        texts[name]
        for name in SECTION_FILES
        if name not in {"editorial canon", "references", "supplementary information"}
    )

    add_marker_check(
        checks,
        "canonical title",
        texts["editorial canon"],
        "Bounded Adaptive Topology-Perturbation Reweighting for Relay-Failure UAV Coordination",
        hard_errors,
    )
    add_marker_check(
        checks,
        "formal five-seed evidence",
        texts["experiments"],
        "seeds 2301--2305",
        hard_errors,
    )
    add_marker_check(
        checks,
        "independent cohort disclosure",
        primary,
        "independent three-method cohort",
        hard_errors,
    )
    add_marker_check(
        checks,
        "training-seed statistical unit",
        primary,
        "Training seed, rather than evaluation episode",
        hard_errors,
    )
    add_marker_check(
        checks,
        "NoGraph limitation",
        texts["experiments"],
        "35,771-parameter, no-message architecture",
        hard_errors,
    )
    add_marker_check(
        checks,
        "post hoc unseen-member boundary",
        primary,
        "post hoc",
        hard_errors,
    )
    add_marker_check(
        checks,
        "formal safety trade-off",
        primary,
        "timeout--collision trade-off",
        hard_errors,
    )
    add_marker_check(
        checks,
        "B-line location: Supplementary Table S5",
        texts["discussion"],
        "Supplementary Table S5",
        hard_errors,
    )
    add_marker_check(
        checks,
        "supplementary formal-cohort table",
        texts["supplementary information"],
        "Table S1. Formal paired seed effects",
        hard_errors,
    )
    add_marker_check(
        checks,
        "supplementary independent-cohort boundary",
        texts["supplementary information"],
        "must never be pooled into an apparent",
        hard_errors,
    )
    add_marker_check(
        checks,
        "supplementary B-line boundary",
        texts["supplementary information"],
        "Exploratory stabilization stress tests and negative-result boundary",
        hard_errors,
    )

    for numeric in ("+52.13", "+55.00", "+63.01", "0.874", "0.694", "0.005", "0.008"):
        add_marker_check(
            checks,
            f"numeric anchor {numeric}",
            texts["abstract"] + texts["experiments"],
            numeric,
            hard_errors,
        )

    refs = texts["references"]
    reference_ids = {int(value) for value in re.findall(r"^(\d+)\. ", refs, flags=re.MULTILINE)}
    cited_ids = markdown_citations(primary)
    missing_references = sorted(cited_ids - reference_ids)
    if missing_references:
        hard_errors.append(f"citations without reference entries: {missing_references}")
        checks.append(Check("citation mapping", "FAIL", str(missing_references)))
    else:
        checks.append(Check("citation mapping", "PASS", f"{len(cited_ids)} cited ids mapped to reference entries"))

    b_line_terms = re.compile(
        r"\b(?:KLR|KLB|PP-DRTP|PR-DRTP|CV-DRTP|counterfactual critic|paired probes?)\b",
        flags=re.IGNORECASE,
    )
    for forbidden_section in ("abstract", "problem formulation", "introduction and related work", "method"):
        matches = b_line_terms.findall(texts[forbidden_section])
        if matches:
            hard_errors.append(f"B-line term outside Discussion/S5: {forbidden_section}: {matches}")
            checks.append(Check(f"B-line placement: {forbidden_section}", "FAIL", str(matches)))
        else:
            checks.append(Check(f"B-line placement: {forbidden_section}", "PASS", "no B-line term"))

    claim_patterns = {
        "unqualified stable claim": r"DRTP\s+(?:is|was|remains|provides)\s+(?:a\s+)?stable",
        "universal robustness claim": r"(?:demonstrates|proves|establishes)\s+universal robustness",
        "strict-OOD success claim": r"(?:demonstrates|proves|establishes)\s+strict (?:OOD|out-of-distribution)",
        "general-DRO guarantee claim": (
            r"(?:DRTP|this (?:paper|study))\s+(?:provides?|achieves?|guarantees?)\s+"
            r"(?:a\s+)?(?:general|certified)\s+(?:distributionally robust|DRO)\s+(?:guarantee|optimality)"
        ),
    }
    for name, pattern in claim_patterns.items():
        matches = re.findall(pattern, primary, flags=re.IGNORECASE)
        if matches:
            warnings.append(f"potential {name}: {matches}")
            checks.append(Check(name, "WARN", str(matches)))
        else:
            checks.append(Check(name, "PASS", "no unqualified occurrence"))

    if words(texts["abstract"]) > 300:
        warnings.append(f"abstract has {words(texts['abstract'])} words; check the target journal limit")
        checks.append(Check("abstract length", "WARN", str(words(texts["abstract"]))))
    else:
        checks.append(Check("abstract length", "PASS", str(words(texts["abstract"]))))

    write_report(checks, hard_errors, warnings, texts)
    print(REPORT)
    if hard_errors:
        raise SystemExit(1)


def write_report(
    checks: list[Check],
    hard_errors: list[str],
    warnings: list[str],
    texts: dict[str, str],
) -> None:
    total_words = sum(
        words(text)
        for name, text in texts.items()
        if name not in {"references", "editorial canon", "supplementary information"}
    )
    lines = [
        "# DRTP English Manuscript Internal Audit",
        "",
        "This audit applies only to `paper/q2_final_en/`; it does not audit the legacy EA-RG-MAPPO English LaTeX manuscript.",
        "",
        "## Summary",
        "",
        f"- Status: `{'PASS' if not hard_errors else 'FAIL'}`",
        f"- Main-text words excluding references, editorial canon, and Supplementary Information: `{total_words}`",
        f"- Hard errors: `{len(hard_errors)}`",
        f"- Warnings: `{len(warnings)}`",
        "",
        "## Checks",
        "",
        "| Check | Status | Detail |",
        "| --- | --- | --- |",
    ]
    lines.extend(f"| {check.name} | `{check.status}` | {check.detail} |" for check in checks)
    lines.extend(["", "## Hard errors", ""])
    lines.extend(f"- {item}" for item in hard_errors) if hard_errors else lines.append("- None.")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in warnings) if warnings else lines.append("- None.")
    lines.extend(
        [
            "",
            "## Scope",
            "",
            "This structural audit does not replace a source-by-source literature verification, journal-template compilation, anonymous-repository access test, or a substantive reviewer simulation.",
            "",
        ]
    )
    with REPORT.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines))


if __name__ == "__main__":
    main()
