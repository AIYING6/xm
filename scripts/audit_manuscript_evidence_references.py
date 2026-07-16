from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / "results" / "manuscript_evidence_reference_audit.csv"
OUT_MD = ROOT / "docs" / "manuscript_evidence_reference_audit.md"


@dataclass(frozen=True)
class ReferenceSpec:
    claim_id: str
    language: str
    manuscript_path: str
    evidence_type: str
    marker: str
    note: str


EN_EXP = "paper_latex_en/sections/05_experiments.tex"
EN_APP = "paper_latex_en/sections/08_appendix_experiments.tex"
EN_DISC = "paper_latex_en/sections/06_discussion.tex"
EN_CONC = "paper_latex_en/sections/07_conclusion.tex"
ZH_EXP = "paper_latex/sections/05_experiments.tex"
ZH_APP = "paper_latex/sections/08_appendix_experiments.tex"
ZH_DISC = "paper_latex/sections/06_discussion.tex"
ZH_CONC = "paper_latex/sections/07_conclusion.tex"


SPECS = [
    ReferenceSpec("C1", "en", EN_EXP, "table_input", r"\input{../results/latex_final_comm_300_table}", "Final 300-episode main table is included."),
    ReferenceSpec("C1", "en", EN_EXP, "figure", "final_300_success_rate.png", "Final success-rate figure is included."),
    ReferenceSpec("C1", "en", EN_EXP, "figure", "final_300_collision_rate.png", "Final collision-rate figure is included."),
    ReferenceSpec("C1", "en", EN_EXP, "budget_marker", "300 evaluation episodes per seed", "Main evaluation budget is explicitly stated."),
    ReferenceSpec("C1", "en", EN_EXP, "value_marker", "0.054", "Key low-collision value is stated."),
    ReferenceSpec("C1", "zh", ZH_EXP, "table_input", r"\input{../results/latex_final_comm_300_table}", "Final 300-episode main table is included."),
    ReferenceSpec("C1", "zh", ZH_EXP, "figure", "final_300_success_rate.png", "Final success-rate figure is included."),
    ReferenceSpec("C1", "zh", ZH_EXP, "figure", "final_300_collision_rate.png", "Final collision-rate figure is included."),
    ReferenceSpec("C1", "zh", ZH_EXP, "budget_marker", "300", "Main evaluation budget is stated in Chinese manuscript."),
    ReferenceSpec("C2", "en", EN_APP, "table_input", r"\input{../results/latex_final_300_paired_ci_table}", "Seed-paired descriptive interval table is included."),
    ReferenceSpec("C2", "en", EN_APP, "boundary_marker", "supplementary evidence rather than as a definitive statistical-significance test", "Seed-paired interval boundary is stated."),
    ReferenceSpec("C2", "zh", ZH_APP, "table_input", r"\input{../results/latex_final_300_paired_ci_table}", "Seed-paired descriptive interval table is included."),
    ReferenceSpec("C2", "zh", ZH_APP, "boundary_marker", "不作为独立的强显著性检验", "Seed-paired interval boundary is stated."),
    ReferenceSpec("C3", "en", EN_APP, "table_input", r"\input{../results/latex_comm_dropout_robustness_table}", "Communication-dropout table is included."),
    ReferenceSpec("C3", "en", EN_APP, "figure", "comm_dropout_collision_rate.png", "Communication-dropout collision figure is included."),
    ReferenceSpec("C3", "en", EN_APP, "budget_marker", "50-episode-per-seed diagnostic", "Dropout diagnostic budget is stated."),
    ReferenceSpec("C3", "zh", ZH_APP, "table_input", r"\input{../results/latex_comm_dropout_robustness_table}", "Communication-dropout table is included."),
    ReferenceSpec("C3", "zh", ZH_APP, "figure", "comm_dropout_collision_rate.png", "Communication-dropout collision figure is included."),
    ReferenceSpec("C3", "zh", ZH_APP, "budget_marker", "50 回合每种子的轻量诊断", "Dropout diagnostic budget is stated."),
    ReferenceSpec("C4", "en", EN_APP, "table_input", r"\input{../results/latex_aggregate_robustness_table}", "Aggregate robustness table is included."),
    ReferenceSpec("C4", "en", EN_APP, "boundary_marker", "not introduce a new training run or a weighted optimization objective", "Aggregate summary boundary is stated."),
    ReferenceSpec("C4", "zh", ZH_APP, "table_input", r"\input{../results/latex_aggregate_robustness_table}", "Aggregate robustness table is included."),
    ReferenceSpec("C4", "zh", ZH_APP, "boundary_marker", "不引入新的训练或加权优化目标", "Aggregate summary boundary is stated."),
    ReferenceSpec("C5", "en", EN_APP, "table_input", r"\input{../results/latex_radius_interpolation_table}", "Radius interpolation table is included."),
    ReferenceSpec("C5", "en", EN_APP, "figure", "radius_interpolation_collision_rate.png", "Radius interpolation collision figure is included."),
    ReferenceSpec("C5", "en", EN_APP, "boundary_marker", "does not replace the 300-episode main table", "Interpolation boundary is stated."),
    ReferenceSpec("C5", "zh", ZH_APP, "table_input", r"\input{../results/latex_radius_interpolation_table}", "Radius interpolation table is included."),
    ReferenceSpec("C5", "zh", ZH_APP, "figure", "radius_interpolation_collision_rate.png", "Radius interpolation collision figure is included."),
    ReferenceSpec("C5", "zh", ZH_APP, "boundary_marker", "不替代 300-episode 主表", "Interpolation boundary is stated."),
    ReferenceSpec("C6", "en", EN_APP, "table_input", r"\input{../results/latex_speed_robustness_table}", "Target-speed robustness table is included."),
    ReferenceSpec("C6", "en", EN_APP, "figure", "speed_robustness_collision_r8.png", "Target-speed collision figure is included."),
    ReferenceSpec("C6", "en", EN_APP, "budget_marker", "100 episodes per seed", "Target-speed robustness budget is stated."),
    ReferenceSpec("C6", "zh", ZH_APP, "table_input", r"\input{../results/latex_speed_robustness_table}", "Target-speed robustness table is included."),
    ReferenceSpec("C6", "zh", ZH_APP, "figure", "speed_robustness_collision_r8.png", "Target-speed collision figure is included."),
    ReferenceSpec("C6", "zh", ZH_APP, "budget_marker", "100 回合每种子的附录级评估", "Target-speed robustness budget is stated."),
    ReferenceSpec("C7", "en", EN_APP, "table_input", r"\input{../results/latex_edge_feature_ablation_table}", "Edge-feature masking table is included."),
    ReferenceSpec("C7", "en", EN_APP, "figure", "edge_feature_ablation_delta.png", "Edge-feature masking delta figure is included."),
    ReferenceSpec("C7", "en", EN_APP, "boundary_marker", "not a retrained structural ablation", "Edge masking boundary is stated."),
    ReferenceSpec("C7", "zh", ZH_APP, "table_input", r"\input{../results/latex_edge_feature_ablation_table}", "Edge-feature masking table is included."),
    ReferenceSpec("C7", "zh", ZH_APP, "figure", "edge_feature_ablation_delta.png", "Edge-feature masking delta figure is included."),
    ReferenceSpec("C7", "zh", ZH_APP, "boundary_marker", "不等同于重新训练的结构消融", "Edge masking boundary is stated."),
    ReferenceSpec("C8", "en", EN_DISC, "boundary_marker", "not be treated as a full air-combat system", "LAG/JSBSim extension boundary is stated in discussion."),
    ReferenceSpec("C8", "en", EN_DISC, "extension_marker", "LAG/JSBSim", "LAG/JSBSim future-extension context is stated."),
    ReferenceSpec("C8", "zh", ZH_DISC, "boundary_marker", "不能被写成完整 6DOF 空战验证", "LAG/JSBSim extension boundary is stated in Chinese discussion."),
    ReferenceSpec("C8", "zh", ZH_DISC, "extension_marker", "LAG/JSBSim", "LAG/JSBSim future-extension context is stated."),
    ReferenceSpec("C9", "en", EN_EXP, "boundary_marker", "cannot support a high-accuracy intent-recognition claim", "Intent diagnostic boundary is stated in experiments."),
    ReferenceSpec("C9", "en", EN_EXP, "value_marker", "balanced accuracy of 0.200", "Intent balanced-accuracy diagnostic value is stated."),
    ReferenceSpec("C9", "zh", ZH_EXP, "boundary_marker", "不能作为强主张", "Intent diagnostic boundary is stated in Chinese experiments."),
    ReferenceSpec("C9", "zh", ZH_EXP, "value_marker", "balanced accuracy = 0.200", "Intent balanced-accuracy diagnostic value is stated."),
    ReferenceSpec("C9", "en", EN_DISC, "boundary_marker", "not used as a main contribution", "Intent branch is excluded as a main contribution in discussion."),
    ReferenceSpec("C9", "zh", ZH_DISC, "boundary_marker", "不作为本文主贡献", "Intent branch is excluded as a main contribution in Chinese discussion."),
]


def check_spec(spec: ReferenceSpec) -> dict[str, str]:
    path = ROOT / spec.manuscript_path
    if not path.exists() or path.stat().st_size <= 0:
        return {
            "claim_id": spec.claim_id,
            "language": spec.language,
            "manuscript_path": spec.manuscript_path,
            "evidence_type": spec.evidence_type,
            "marker": spec.marker,
            "status": "failed",
            "notes": "missing_or_empty_manuscript_file",
        }
    text = path.read_text(encoding="utf-8")
    ok = spec.marker in text
    return {
        "claim_id": spec.claim_id,
        "language": spec.language,
        "manuscript_path": spec.manuscript_path,
        "evidence_type": spec.evidence_type,
        "marker": spec.marker,
        "status": "ok" if ok else "failed",
        "notes": spec.note if ok else f"marker_not_found: {spec.marker}",
    }


def write_csv(rows: list[dict[str, str]]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fields = ["claim_id", "language", "manuscript_path", "evidence_type", "marker", "status", "notes"]
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
        "# Manuscript Evidence Reference Audit",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Purpose:",
        "",
        "```text",
        "Check that Chinese and English LaTeX manuscripts actually reference the evidence required by the claim-evidence matrix.",
        "This audit checks manuscript markers only; it does not compile PDFs.",
        "```",
        "",
        "## Summary",
        "",
        "```text",
        f"references_checked = {len(rows)}",
        f"failures = {len(failures)}",
        *[f"{claim_id} = {count}" for claim_id, count in sorted(by_claim.items())],
        "```",
        "",
        "## Rows",
        "",
        "| Claim | Lang | Type | Manuscript | Status | Notes |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['claim_id']} | {row['language']} | {row['evidence_type']} | "
            f"`{row['manuscript_path']}` | {row['status']} | {row['notes']} |"
        )
    if failures:
        lines.extend(["", "## Failures", ""])
        for row in failures:
            lines.append(f"- {row['claim_id']} `{row['manuscript_path']}` missing `{row['marker']}`")
    lines.extend(
        [
            "",
            "## Use Boundary",
            "",
            "```text",
            "Passing this audit means required evidence markers are present in manuscript sources.",
            "It does not guarantee final PDF layout quality or journal-specific formatting.",
            "```",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = [check_spec(spec) for spec in SPECS]
    write_csv(rows)
    write_report(rows)
    failures = [row for row in rows if row["status"] != "ok"]
    print(OUT_CSV)
    print(OUT_MD)
    print(f"references checked: {len(rows)}")
    print(f"failures: {len(failures)}")
    if failures:
        for row in failures:
            print(f"failed: {row['claim_id']} {row['manuscript_path']} missing {row['marker']}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
