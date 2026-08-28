"""Fail-closed checks for the Q2 Chinese manuscript workspace.

This checker validates the completed Chinese-manuscript evidence package. It does
not run experiments, evaluate checkpoints, or authorize new training.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from PIL import Image


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
    "14_formal_result_integration_audit.md",
    "15_formal_statistics_and_figure_legend_contract.md",
    "16_no_training_evidence_enhancement_audit.md",
    "17_major_revision_rectification_log.md",
    "18_p1_review_response_and_submission_gap.md",
    "19_v112_reviewer_reconciliation_and_submission_blockers.md",
    "20_evidence_architecture_writing_upgrade.md",
    "21_external_reference_integration_contract.md",
    "22_submission_evidence_layer_freeze_audit.md",
    "23_claim_evidence_audit.md",
    "24_anonymous_reproducibility_package.md",
    "25_final_evidence_manifest.json",
    "26_novelty_and_prior_art_positioning.md",
    "27_presubmission_reviewer_simulation.md",
    "28_anonymous_package_staging_audit.md",
    "29_submission_release_gate.md",
    "30_final_scientific_version_reviewer_assessment.md",
    "31_target_chinese_journal_shortlist.md",
    "32_preselection_submission_package.md",
    "33_project_side_completion_audit.md",
    "submission_release_metadata.template.json",
    "supplementary/S1_full_formal_condition_and_safety.md",
    "supplementary/S2_training_and_ppo_diagnostics.md",
    "supplementary/S3_hyperparameters_projection_and_provenance.md",
    "supplementary/S4_independent_three_arm_replication.md",
    "supplementary/source_data/snr_independent_replication/archive_provenance.json",
    "supplementary/source_data/snr_independent_replication/raw_episode_metrics.csv",
    "supplementary/source_data/snr_independent_replication/per_seed_condition_summary.csv",
    "supplementary/source_data/snr_independent_replication/per_seed_endpoint_summary.csv",
    "supplementary/source_data/snr_independent_replication/drtp_minus_utr_paired_seed_effects.csv",
    "supplementary/source_data/snr_independent_replication/drtp_minus_utr_paired_summary.csv",
    "supplementary/source_data/snr_independent_replication/pooled_endpoint_summary.csv",
    "supplementary/source_data/snr_independent_replication/evaluation_manifest.json",
    "formal_results/external_reference_summary.md",
    "formal_results/integration_manifest.json",
    "formal_results/formal_result_tables.md",
    "formal_results/source_data/DRTP_UTR_Q2_FORMAL_DECISION.json",
    "formal_results/source_data/evaluation_manifest.json",
    "formal_results/source_data/formal_tape_manifest.json",
    "formal_results/source_data/paired_seed_results.csv",
    "formal_results/source_data/per_seed_condition_summary.csv",
    "formal_results/source_data/sampler_telemetry_summary.json",
    "formal_results/source_data/formal_terminal_outcomes_by_seed_family.csv",
    "formal_results/source_data/formal_failure_safety_by_seed.csv",
    "formal_results/source_data/formal_training_monitor_binned.csv",
    "formal_results/figures/fig3_formal_primary_performance.svg",
    "formal_results/figures/fig4_ood_condition_decomposition.svg",
    "formal_results/figures/fig5_seed_reliability_and_safety.svg",
    "formal_results/figures/fig6_adaptive_weight_telemetry.svg",
    "formal_results/figures/fig7_formal_terminal_outcomes.svg",
    "formal_results/figures/figS1_training_diagnostics.svg",
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
    require(placeholder_count == 0, "formal-result placeholders remain in the manuscript")
    require("[PENDING]" not in manuscript, "unresolved PENDING marker remains in the manuscript")
    require(FORMAL_SEEDS.issubset(set(re.findall(r"\b23\d{2}\b", manuscript))),
            "formal seed table does not contain every frozen seed")
    require("490000–490099" in manuscript, "formal evaluation tape is not stated")
    require("10,000,128" in manuscript, "formal training budget is not stated")
    require("116,728" in manuscript, "matched parameter count is not stated")
    require("总体门槛，而非“每个种子均不退化”的承诺" in manuscript,
            "aggregate nominal-retention boundary is not explicit")
    require("0.760" in manuscript and "seed2302" in manuscript,
            "formal seed2302 nominal regression is not retained")
    require("**表1｜对照与证据层级。**" in manuscript,
            "comparison and evidence hierarchy is not explicit")
    external_summary = (PAPER / "formal_results" / "external_reference_summary.md").read_text(
        encoding="utf-8"
    )
    for token in (
        "EXTERNAL_REFERENCE_COMPLETE",
        "2f8b5f1e3025221e70652a6c4d0bcaa05d239cc81f5c70d59301d4f9e66afad5",
        "84e31ed185ced0608a30c9cb9f9659c7423c952e4603aac53cf691c54fc64ac2",
        "6,000 条原始 episode 记录",
        "35,771",
        "UTR–DRTP 仍是本文唯一的参数匹配主因果消融",
    ):
        require(token in external_summary, f"external-reference summary missing: {token}")
    require("MAPPO-NoGraph 外部参考已进入表2b和有限讨论" in
            (PAPER / "20_evidence_architecture_writing_upgrade.md").read_text(encoding="utf-8"),
            "external-reference manuscript integration is not recorded")
    external_contract = (PAPER / "21_external_reference_integration_contract.md").read_text(encoding="utf-8")
    for token in ("EXTERNAL_REFERENCE_COMPLETE", "UTR–DRTP", "不得以训练日志、截图或部分 seed 替代"):
        require(token in external_contract, f"external-reference integration boundary missing: {token}")
    require("100 次二分" in manuscript and "有界单纯形投影" in manuscript,
            "bounded-simplex implementation detail is missing")
    require("### 6.3 无图 MAPPO 性能参考（Non-Graph MAPPO Performance Reference）" in manuscript and
            "**表2b｜无图 MAPPO 性能参考结果。**" in manuscript,
            "completed external reference is not integrated in the Results section")
    require("不能据此将 UTR 与 MAPPO 的差异归因于图结构本身" in manuscript and
            "不能建立图结构或自适应权重的单独因果归因" in manuscript,
            "external-reference causal boundary is not explicit")
    require("max(|\\bar J_{N,u}|,\\epsilon)" in manuscript and
            "(1-\\beta)q_u+\\beta\\tilde q_{u+1}" in manuscript,
            "difficulty denominator or smoothing equation is not explicit")
    require("FORMAL_CONFIRMATION_PASS_SEED_SENSITIVE" not in manuscript,
            "machine verdict must not leak into the submission manuscript")
    # The completed SNR cohort is now an explicit, complete independent
    # replication stratum.  It must be present with all seeds and must never
    # be pooled with the formal 2301--2305 cohort.  Unvalidated stabilization
    # candidates remain excluded.
    for forbidden in ("R-DRTP", "R_DRTP", "EGTR", "Reliability-Gated"):
        require(forbidden not in manuscript,
                f"unvalidated stabilization method leaked into manuscript: {forbidden}")
    require("### 6.9 独立三方法重复 cohort 与跨 cohort 可靠性" in manuscript and
            "固定非均匀 SNR-SG-MAPPO" in manuscript and
            "18,000 条原始 episode 记录" in manuscript,
            "complete independent SNR replication cohort is not disclosed")
    require(all(seed in manuscript for seed in ("2401", "2402", "2403", "2404", "2405")),
            "independent replication seed set is incomplete")
    require("不与表2的正式种子 2301--2305 合并为 (n=10)" in manuscript,
            "cross-cohort pooling prohibition is not explicit")
    require("J_pert,mean" in manuscript and "J_pert,worst" in manuscript,
            "paper-facing cross-perturbation endpoint names are missing")
    require("## 参考文献" in manuscript and "[16] Xiao H" in manuscript,
            "submission manuscript does not contain the completed real reference list")
    require("[R" not in manuscript,
            "placeholder-style R citations remain in the submission manuscript")
    require(manuscript.count("J_OOD_mean") == 2 and manuscript.count("J_OOD_worst") == 2,
            "machine OOD fields must appear only in the two explicit archive mappings")
    require("不是严格未见分布外（OOD）指标" in manuscript and
            "不作为严格 OOD 证据" in manuscript,
            "cross-perturbation conditions are not protected from OOD overclaiming")
    require("### 6.8 历史可靠性证据" in manuscript and
            "这些历史结果不能与正式五种子作为一个同质样本合并" in manuscript,
            "historical reliability stratum is not explicitly separated")
    require("### 6.10 跨评价带可靠性诊断" in manuscript and
            "48,000 条原始 episode 记录" in manuscript and
            "正式 2301--2305 cohort 在 tape490 和 tape500 上均保持正向" in manuscript,
            "cross-tape reliability diagnostic is not integrated")
    claim_audit = (PAPER / "23_claim_evidence_audit.md").read_text(encoding="utf-8")
    for token in (
        "PASS WITH BOUNDED CROSS-COHORT CLAIMS",
        "跨 cohort 尚未稳定复现",
        "strict OOD",
        "R-DRTP、EGTR",
        "episode",
    ):
        require(token in claim_audit, f"claim-evidence audit missing: {token}")

    state = json.loads((PAPER / "state.json").read_text(encoding="utf-8"))
    require(state.get("nonresult_manuscript_sections_drafted") is True,
            "writing state does not record the completed non-result draft")
    require(state.get("formal_confirmation_completed") is True,
            "writing state does not record completed formal confirmation")
    require(state.get("formal_result_integration_completed") is True,
            "writing state does not record formal-result integration")
    require(state.get("formal_verdict") == "FORMAL_CONFIRMATION_PASS_SEED_SENSITIVE",
            "formal manuscript verdict mismatch")
    require(state.get("cross_tape_reliability_status") ==
            "COMPLETE_ZERO_TRAINING_DIAGNOSTIC_COHORT_DIRECTION_PERSISTS_ACROSS_TAPES",
            "cross-tape diagnostic status is missing or incorrect")
    require(state.get("formal_confirmation_contract") ==
            "DRTP-UTR-Q2-FORMAL-PAIRED-5SEED-V1",
            "formal confirmation contract mismatch")
    require(state.get("publication_language_route") == "chinese_only",
            "publication route is not frozen to Chinese")
    require(state.get("parallel_english_full_manuscript") is False,
            "parallel English full manuscript must remain disabled")
    require(state.get("external_reference_integration_contract") ==
            "paper/q2_final_zh/21_external_reference_integration_contract.md",
            "external-reference integration contract is not registered")
    require("independently SHA256-verified and integrated" in
            state.get("external_reference_status", ""),
            "writing state does not record completed external-reference integration")
    require(state.get("snr_cohort_publication_disposition") ==
            "transparent_independent_replication_disclosure_by_current_publication_goal_2026-08-27",
            "SNR publication disposition is not frozen to transparent disclosure")
    require("never pooled with the formal 2301-2305" in
            state.get("snr_cohort_publication_boundary", ""),
            "SNR cohort pooling boundary is not explicit in writing state")
    require(state.get("snr_replication_supplement") ==
            "paper/q2_final_zh/supplementary/S4_independent_three_arm_replication.md",
            "SNR replication supplement is not registered")
    require(state.get("anonymous_reproducibility_package") ==
            "paper/q2_final_zh/24_anonymous_reproducibility_package.md",
            "anonymous reproducibility package is not registered")
    require(state.get("final_evidence_manifest") ==
            "paper/q2_final_zh/25_final_evidence_manifest.json",
            "final evidence manifest is not registered")
    require(state.get("novelty_and_prior_art_positioning") ==
            "paper/q2_final_zh/26_novelty_and_prior_art_positioning.md",
            "novelty positioning is not registered")
    require(state.get("presubmission_reviewer_simulation") ==
            "paper/q2_final_zh/27_presubmission_reviewer_simulation.md",
            "presubmission reviewer simulation is not registered")
    require(state.get("target_chinese_journal_shortlist") ==
            "paper/q2_final_zh/31_target_chinese_journal_shortlist.md",
            "target Chinese-journal shortlist is not registered")
    require(state.get("preselection_submission_package") ==
            "paper/q2_final_zh/32_preselection_submission_package.md",
            "preselection submission package is not registered")
    require(state.get("project_side_completion_audit") ==
            "paper/q2_final_zh/33_project_side_completion_audit.md",
            "project-side completion audit is not registered")
    require(state.get("stage") ==
            "project_side_submission_closeout_completed_author_actions_pending",
            "writing state does not distinguish project completion from author actions")

    reproducibility_plan = (PAPER / "24_anonymous_reproducibility_package.md").read_text(
        encoding="utf-8"
    )
    for token in (
        "PREPARED_FOR_AUTHOR_HOSTING",
        "18,000",
        "n=10",
        "Data Availability",
    ):
        require(token in reproducibility_plan,
                f"anonymous reproducibility plan missing: {token}")
    evidence_manifest = json.loads((PAPER / "25_final_evidence_manifest.json").read_text(
        encoding="utf-8"
    ))
    require(evidence_manifest.get("new_training_authorized") is False,
            "final evidence manifest must not authorize new training")
    require(len(evidence_manifest.get("evidence_strata", [])) >= 3 and
            {item.get("name") for item in evidence_manifest.get("evidence_strata", [])} >=
            {"formal_paired_primary_cohort", "non_graph_mappo_performance_reference",
             "independent_three_arm_reliability_replication"},
            "final evidence manifest must retain the three training evidence strata")
    require("No n=10 pooling across cohorts" in
            evidence_manifest.get("required_transparency", []),
            "final evidence manifest does not prohibit cross-cohort pooling")
    novelty_map = (PAPER / "26_novelty_and_prior_art_positioning.md").read_text(
        encoding="utf-8"
    )
    for token in ("PPO", "SNR", "116,728", "cohort", "DRO"):
        require(token in novelty_map, f"novelty map is incomplete: {token}")
    reviewer_simulation = (PAPER / "27_presubmission_reviewer_simulation.md").read_text(
        encoding="utf-8"
    )
    for token in ("Reviewer 1", "Reviewer 2", "Reviewer 3", "Cross-review synthesis",
                  "Risk / unsupported claims", "reproducibility"):
        require(token in reviewer_simulation,
                f"presubmission reviewer simulation is incomplete: {token}")
    final_review = (PAPER / "30_final_scientific_version_reviewer_assessment.md").read_text(
        encoding="utf-8"
    )
    for token in ("Reviewer 1", "Reviewer 2", "Reviewer 3", "Cross-review synthesis",
                  "Risk / unsupported claims", "2401--2405"):
        require(token in final_review,
                f"final scientific-version reviewer assessment is incomplete: {token}")
    journal_shortlist = (PAPER / "31_target_chinese_journal_shortlist.md").read_text(
        encoding="utf-8"
    )
    for token in (
        "AUTHOR_SELECTION_REQUIRED",
        "2301--2305",
        "2401--2405",
        "`n=10`",
        "《航空学报》",
        "《系统工程与电子技术》",
        "《控制与决策》",
        "《航空工程进展》",
    ):
        require(token in journal_shortlist,
                f"target-journal shortlist is incomplete: {token}")
    submission_package = (PAPER / "32_preselection_submission_package.md").read_text(
        encoding="utf-8"
    )
    for token in (
        "READY_WITH_AUTHOR_CHECKS",
        "2401--2405",
        "不与主 cohort 合并为 `n=10`",
        "初次投稿信模板",
        "AUTHOR_INPUT_NEEDED",
        "SUBMISSION_RELEASE_READY",
    ):
        require(token in submission_package,
                f"preselection submission package is incomplete: {token}")

    project_completion = (PAPER / "33_project_side_completion_audit.md").read_text(
        encoding="utf-8"
    )
    for token in (
        "PROJECT_SIDE_COMPLETE_AUTHOR_ACTION_REMAINS",
        "TECHNICAL_READY_AUTHOR_ACTION_REQUIRED",
        "2401--2405",
        "不得与 2301--2305 合并",
        "19 页 PDF",
        "未启动训练",
    ):
        require(token in project_completion,
                f"project-side completion audit is incomplete: {token}")

    for supplement_name, token in (
        ("S1_full_formal_condition_and_safety.md", "risk-set"),
        ("S2_training_and_ppo_diagnostics.md", "PPO"),
        ("S3_hyperparameters_projection_and_provenance.md", "100"),
        ("S4_independent_three_arm_replication.md", "18,000"),
    ):
        supplement = (PAPER / "supplementary" / supplement_name).read_text(encoding="utf-8")
        require(token in supplement,
                f"supplementary package is incomplete: {supplement_name}")

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
    require("目标期刊" in citation_ledger,
            "citation ledger does not retain target-journal adaptation boundary")
    require(all(f"R{idx}" in citation_ledger for idx in range(1, 17)),
            "verified core citation ledger is incomplete")

    reference_export = (PAPER / "references_core.enw").read_text(encoding="utf-8")
    require(reference_export.count("%0 ") == 16,
            "EndNote core-reference export must contain sixteen records")

    chinese_contract = (PAPER / "10_chinese_submission_contract.md").read_text(
        encoding="utf-8"
    )
    require("只建设中文主稿" in chinese_contract,
            "Chinese-only manuscript route is not explicit")
    require("英文题名、英文摘要和英文关键词" in chinese_contract,
            "Chinese-journal English metadata boundary is missing")

    decision = json.loads((PAPER / "formal_results" / "source_data" /
                           "DRTP_UTR_Q2_FORMAL_DECISION.json").read_text(encoding="utf-8"))
    require(decision.get("verdict") == "FORMAL_CONFIRMATION_PASS_SEED_SENSITIVE",
            "paper-facing formal decision differs from frozen verdict")
    require(decision.get("catastrophic_seed_count") == 0,
            "paper-facing decision reports unexpected catastrophic seeds")
    require(all(decision.get("gates", {}).values()),
            "paper-facing decision has a failed frozen gate")

    figures = PAPER / "formal_results" / "figures"
    figure_stems = (
        "fig1_relay_failure_topology_reconfiguration",
        "fig2_utr_drtp_training_distribution",
        "fig3_formal_primary_performance",
        "fig4_ood_condition_decomposition",
        "fig5_seed_reliability_and_safety",
        "fig6_adaptive_weight_telemetry",
        "fig7_formal_terminal_outcomes",
        "figS1_training_diagnostics",
    )
    for stem in figure_stems:
        # SVG/PDF/PNG are the committed figure contract. TIFF exports are
        # intentionally ignored by .gitignore because they are reproducible
        # from the committed figure scripts; validate one when present, but
        # do not make a clean clone depend on an untracked local raster.
        for extension in (".svg", ".pdf", ".png"):
            require((figures / f"{stem}{extension}").is_file(),
                    f"missing figure artifact: {stem}{extension}")
        raster = figures / f"{stem}.tiff"
        if not raster.is_file():
            raster = figures / f"{stem}.png"
        with Image.open(raster) as image:
            dpi = image.info.get("dpi", (0, 0))
            require(min(dpi) >= 599, f"{stem} raster DPI below 600: {dpi}")
            require(min(image.size) >= 1400,
                    f"{stem} raster dimensions unexpectedly small: {image.size}")

    print(
        "PASS: Chinese manuscript evidence package is integrated; no formal-result "
        "placeholders remain, all eight figures pass artifact checks, and the independent "
        "three-arm replication is transparently retained without cross-cohort pooling."
    )


if __name__ == "__main__":
    main()
