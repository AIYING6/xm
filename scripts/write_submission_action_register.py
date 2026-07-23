from __future__ import annotations

import csv
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / "results" / "submission_action_register.csv"
OUT_MD = ROOT / "docs" / "submission_action_register.md"


@dataclass(frozen=True)
class ActionItem:
    item_id: str
    priority: str
    status: str
    category: str
    action: str
    evidence: str
    next_step: str


def file_contains(rel: str, marker: str) -> bool:
    path = ROOT / rel
    return path.exists() and marker in path.read_text(encoding="utf-8")


def tool_status(tool: str) -> str:
    return "available" if shutil.which(tool) else "missing"


def build_items() -> list[ActionItem]:
    xelatex = tool_status("xelatex")
    latexmk = tool_status("latexmk")
    bibtex = tool_status("bibtex")
    english_author_open = file_contains("paper_latex_3d_en/main.tex", "To be completed")
    chinese_author_open = file_contains("paper_latex/main.tex", "待补充")
    plain_bib_en = file_contains("paper_latex_3d_en/main.tex", r"\bibliographystyle{plain}")
    plain_bib_zh = file_contains("paper_latex/main.tex", r"\bibliographystyle{plain}")
    jsbsim_data_missing = not (ROOT.parent / "LAG" / "envs" / "JSBSim" / "data").exists()

    return [
        ActionItem(
            "A1",
            "high",
            "blocked" if xelatex == "missing" or bibtex == "missing" else "open",
            "pdf_validation",
            "Compile Chinese and English LaTeX projects and visually inspect PDFs.",
            f"xelatex={xelatex}; latexmk={latexmk}; bibtex={bibtex}",
            "Run xelatex/bibtex in a full LaTeX environment, then inspect tables, figures, captions, references, and page breaks.",
        ),
        ActionItem(
            "A2",
            "high",
            "open",
            "journal_target",
            "Choose the target journal and migrate the English manuscript to its template.",
            "docs/journal_target_shortlist.md and docs/journal_template_migration_plan.md exist.",
            "Select one target venue, then replace the generic article class, bibliography style, declarations, and formatting.",
        ),
        ActionItem(
            "A3",
            "high",
            "open" if english_author_open or chinese_author_open else "done",
            "metadata",
            "Replace author placeholders in Chinese and English manuscripts.",
            f"english_placeholder={english_author_open}; chinese_placeholder={chinese_author_open}",
            "Fill author names, affiliations, corresponding author, and acknowledgements after the submission route is chosen.",
        ),
        ActionItem(
            "A4",
            "medium",
            "open",
            "declarations",
            "Add data/code availability statements.",
            "bilingual_manuscript_completeness_audit marks data_availability as action_item.",
            "State which CSVs, scripts, checkpoints, and generated assets can be shared as supplementary material.",
        ),
        ActionItem(
            "A5",
            "medium",
            "open",
            "declarations",
            "Add funding, conflict-of-interest, and author-contribution statements if required.",
            "bilingual_manuscript_completeness_audit marks funding_conflict_statement as action_item.",
            "Use the selected journal's declaration wording and leave unknown funding as 'not applicable' only if true.",
        ),
        ActionItem(
            "A6",
            "medium",
            "open" if plain_bib_en or plain_bib_zh else "done",
            "formatting",
            "Replace generic plain bibliography style with the target journal style.",
            f"english_plain_bib={plain_bib_en}; chinese_plain_bib={plain_bib_zh}",
            "Switch BibTeX style or bibliography package after target template migration.",
        ),
        ActionItem(
            "A7",
            "medium",
            "open",
            "supplement",
            "Decide which audit CSVs and result CSVs should be included as supplementary material.",
            "docs/supplemental_data_readme.md lists current CSV inventory and interpretation boundaries.",
            "Keep internal audits out of the journal package unless the venue permits or requests reproducibility supplements.",
        ),
        ActionItem(
            "A8",
            "medium",
            "deferred",
            "statistics",
            "Decide whether to add a larger scenario-depth formal evaluation beyond the completed five-seed Gate 1 package.",
            "Current Gate 1 main evidence already uses five seeds, 100 matched test episodes per seed, and seed-aware hierarchical bootstrap.",
            "Only run a new formal scenario-depth budget if the target venue or adviser requires stronger realism beyond the current 3v1 mechanism package.",
        ),
        ActionItem(
            "A9",
            "medium",
            "blocked" if jsbsim_data_missing else "open",
            "lag_jsbsim",
            "Run real LAG/JSBSim reset/one-step probe before claiming 6DOF validation.",
            f"jsbsim_data_missing={jsbsim_data_missing}; docs/lag_jsbsim_migration_probe.md records current blocker.",
            "Restore/install LAG envs/JSBSim/data and missing imports, then run a real MultipleCombatEnv smoke test.",
        ),
        ActionItem(
            "A10",
            "high",
            "open",
            "review",
            "Perform adviser/manual technical review of final claims, tables, and figures.",
            "Automated gates pass, but they do not replace expert review.",
            "Review claim_evidence_matrix.md, final main table, appendix diagnostics, and the target journal scope before submission.",
        ),
    ]


def write_csv(items: list[ActionItem]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fields = list(ActionItem.__dataclass_fields__.keys())
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in items:
            writer.writerow(item.__dict__)


def write_report(items: list[ActionItem]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    for item in items:
        counts[item.status] = counts.get(item.status, 0) + 1
    lines = [
        "# Submission Action Register",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Purpose:",
        "",
        "```text",
        "Track remaining submission-facing actions separately from reproducibility gates.",
        "Open/deferred/blocked items do not mean the evidence chain is broken; they identify work needed before an actual journal submission.",
        "```",
        "",
        "## Summary",
        "",
        "```text",
        f"items = {len(items)}",
        *[f"{key} = {value}" for key, value in sorted(counts.items())],
        "```",
        "",
        "## Action Items",
        "",
        "| ID | Priority | Status | Category | Action | Evidence | Next step |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in items:
        lines.append(
            f"| {item.item_id} | {item.priority} | {item.status} | {item.category} | "
            f"{item.action} | {item.evidence} | {item.next_step} |"
        )
    lines.extend(
        [
            "",
            "## Use Boundary",
            "",
            "```text",
            "Use this register to plan submission work. Do not use it to weaken current evidence boundaries.",
            "The current paper still cannot claim real 6DOF/JSBSim validation until A9 is resolved and new evidence is generated.",
            "```",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    items = build_items()
    write_csv(items)
    write_report(items)
    print(OUT_CSV)
    print(OUT_MD)
    print(f"items: {len(items)}")
    for status in sorted({item.status for item in items}):
        print(f"{status}: {sum(1 for item in items if item.status == status)}")


if __name__ == "__main__":
    main()
