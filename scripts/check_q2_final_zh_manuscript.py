"""Fail-closed checks for the Q2 Chinese manuscript workspace.

This checker validates writing-state integrity only. It does not run experiments,
evaluate checkpoints, or authorize result integration.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper" / "q2_final_zh"

REQUIRED_FILES = [
    "00_scope.md",
    "01_research_canon.md",
    "02_evidence_table.md",
    "03_argument_map.md",
    "04_section_contracts.md",
    "05_terminology_ledger.md",
    "06_statistical_reporting_contract.md",
    "07_style_guide.md",
    "08_formal_result_integration_contract.md",
    "09_citation_ledger.md",
    "10_chinese_submission_contract.md",
    "11_chinese_figure_table_plan.md",
    "12_author_input_checklist.md",
    "references_core.enw",
    "13_chinese_manuscript_readiness_audit.md",
    "main_zh.md",
    "state.json",
]

REQUIRED_HEADINGS = [
    "## 摘要",
    "## 1 引言",
    "## 2 相关工作",
    "## 3 问题建模",
    "## 4 方法",
    "## 5 实验协议",
    "## 6 结果",
    "## 7 讨论",
    "## 8 结论",
]

FORMAL_SEEDS = {"2301", "2302", "2303", "2304", "2305"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    missing = [name for name in REQUIRED_FILES if not (PAPER / name).is_file()]
    require(not missing, f"missing manuscript files: {missing}")

    manuscript = (PAPER / "main_zh.md").read_text(encoding="utf-8")
    for heading in REQUIRED_HEADINGS:
        require(heading in manuscript, f"missing required heading: {heading}")

    placeholder_count = manuscript.count("[正式结果待回填")
    require(placeholder_count >= 7, "formal-result placeholders are incomplete")
    require(FORMAL_SEEDS.issubset(set(re.findall(r"\b23\d{2}\b", manuscript))),
            "formal seed table does not contain every frozen seed")
    require("490000–490099" in manuscript, "formal evaluation tape is not stated")
    require("10,000,128" in manuscript, "formal training budget is not stated")
    require("116,728" in manuscript, "matched parameter count is not stated")

    state = json.loads((PAPER / "state.json").read_text(encoding="utf-8"))
    require(state.get("nonresult_manuscript_sections_drafted") is True,
            "writing state does not record the completed non-result draft")
    require(state.get("formal_result_placeholders_frozen") is True,
            "writing state does not freeze formal-result placeholders")
    require(state.get("formal_confirmation_contract") ==
            "DRTP-UTR-Q2-FORMAL-PAIRED-5SEED-V1",
            "formal confirmation contract mismatch")
    require(state.get("publication_language_route") == "chinese_only",
            "publication route is not frozen to Chinese")
    require(state.get("parallel_english_full_manuscript") is False,
            "parallel English full manuscript must remain disabled")

    integration = (PAPER / "08_formal_result_integration_contract.md").read_text(
        encoding="utf-8"
    )
    for token in (
        "FORMAL_CONFIRMATION_PASS_SEED_SENSITIVE",
        "FORMAL_CONFIRMATION_LIMITATION_ONLY",
        "FORMAL_CONFIRMATION_FAIL_DEMOTE_DRTP",
        "FORMAL_CONFIRMATION_TECHNICAL_INVALID",
    ):
        require(token in integration, f"missing formal verdict branch: {token}")

    citation_ledger = (PAPER / "09_citation_ledger.md").read_text(encoding="utf-8")
    require("仍待补充的引用主题" in citation_ledger,
            "citation debt is not explicitly marked")
    require("不等同于最终参考文献表" in citation_ledger,
            "citation ledger boundary is missing")
    require(all(f"R{idx}" in citation_ledger for idx in range(1, 10)),
            "verified core citation ledger is incomplete")

    reference_export = (PAPER / "references_core.enw").read_text(encoding="utf-8")
    require(reference_export.count("%0 ") == 9,
            "EndNote core-reference export must contain nine records")

    chinese_contract = (PAPER / "10_chinese_submission_contract.md").read_text(
        encoding="utf-8"
    )
    require("只建设中文主稿" in chinese_contract,
            "Chinese-only manuscript route is not explicit")
    require("英文题名、英文摘要和英文关键词" in chinese_contract,
            "Chinese-journal English metadata boundary is missing")

    print(
        "PASS: Q2 Chinese manuscript workspace is complete, formal-result "
        f"placeholders are frozen ({placeholder_count}), and integration is fail-closed."
    )


if __name__ == "__main__":
    main()
