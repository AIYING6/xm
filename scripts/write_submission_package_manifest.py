from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "submission_package_manifest.md"


@dataclass(frozen=True)
class PackageItem:
    rel: str
    note: str


CHINESE_MANUSCRIPT = [
    PackageItem("paper_latex/main.tex", "Chinese LaTeX manuscript entry point"),
    PackageItem("paper_latex/sections/", "Chinese LaTeX section files"),
    PackageItem("paper_latex/references.bib", "Shared BibTeX database"),
]


ENGLISH_MANUSCRIPT = [
    PackageItem("paper_latex_3d_en/main.tex", "Current 3DOF English LaTeX manuscript entry point"),
    PackageItem("paper_latex_3d_en/sections/", "Current 3DOF English LaTeX section files"),
    PackageItem("paper_latex_3d_en/references.bib", "Current 3DOF BibTeX database"),
]


SHARED_TABLES_FIGURES = [
    PackageItem("results/gate1_safety_fx60_paper_tables/main_results_latex.tex", "Gate 1 fixed-update-60 main comparison table"),
    PackageItem("results/gate1_safety_fx60_paper_tables/ablation_results_latex.tex", "Gate 1 mechanism-ablation table"),
    PackageItem("results/gate1_safety_fx60_paper_tables/seed_aware_deltas_latex.tex", "Gate 1 seed-aware delta table"),
    PackageItem("results/gate1_safety_fx60_paper_tables/capacity_control_latex.tex", "Parameter-matched single-graph capacity-control table"),
    PackageItem("results/gate1_safety_fx60_paper_tables/capacity_control_deltas_latex.tex", "Parameter-matched single-graph seed-aware delta table"),
    PackageItem("results/gate1_safety_fx60_paper_tables/role_identity_latex.tex", "Hardened role-identity ablation table"),
    PackageItem("results/gate1_safety_fx60_paper_tables/role_identity_deltas_latex.tex", "Hardened role-identity seed-aware delta table"),
    PackageItem("results/gate1_safety_fx60_failure_timing_generalization_formal_merged/timing_generalization_latex.tex", "Early relay-failure timing-generalization table"),
    PackageItem("results/gate1_safety_fx60_model_costs/model_costs_latex.tex", "Model-size and CPU actor-latency table"),
    PackageItem("results/figures/intercept_3d_multi_relation_graph.png", "3DOF multi-relation role-graph method figure"),
    PackageItem("results/figures/gate1_safety_fx60_mechanism_curves.png", "Failure-aligned mechanism curves"),
    PackageItem("results/figures/gate1_safety_fx60_representative_case_timeline.png", "Representative relay-failure recovery case"),
]


SUPPLEMENTAL_EVIDENCE = [
    PackageItem("results/final_comm_300_eval.csv", "Raw final evaluation rows"),
    PackageItem("results/final_comm_300_summary.csv", "Final evaluation summary"),
    PackageItem("results/final_300_paired_statistics.csv", "Seed-paired descriptive confidence-interval statistics"),
    PackageItem("results/final_300_paired_statistics.md", "Plain-language paired-statistics notes"),
    PackageItem("results/comm_dropout_robustness_eval.csv", "Communication-dropout diagnostic raw rows"),
    PackageItem("results/comm_dropout_robustness_summary.csv", "Communication-dropout diagnostic summary"),
    PackageItem("results/comm_dropout_robustness_notes.md", "Communication-dropout diagnostic notes"),
    PackageItem("results/comm_dropout_paired_statistics.csv", "Communication-dropout seed-paired descriptive statistics"),
    PackageItem("results/comm_dropout_paired_statistics.md", "Communication-dropout paired-statistics notes"),
    PackageItem("results/aggregate_robustness_summary.csv", "Aggregate cross-condition robustness summary"),
    PackageItem("results/aggregate_robustness_summary.md", "Aggregate robustness summary notes"),
    PackageItem("results/claim_evidence_matrix.csv", "Claim-to-evidence matrix"),
    PackageItem("docs/claim_evidence_matrix.md", "Claim-to-evidence matrix report"),
    PackageItem("results/manuscript_evidence_reference_audit.csv", "Manuscript evidence-reference audit"),
    PackageItem("docs/manuscript_evidence_reference_audit.md", "Manuscript evidence-reference audit report"),
    PackageItem("results/bilingual_numeric_consistency_audit.csv", "Bilingual manuscript numeric consistency audit"),
    PackageItem("docs/bilingual_numeric_consistency_audit.md", "Bilingual manuscript numeric consistency audit report"),
    PackageItem("results/latex_reference_integrity_audit.csv", "LaTeX label/reference integrity audit"),
    PackageItem("docs/latex_reference_integrity_audit.md", "LaTeX label/reference integrity audit report"),
    PackageItem("results/bilingual_manuscript_completeness_audit.csv", "Bilingual manuscript completeness audit"),
    PackageItem("docs/bilingual_manuscript_completeness_audit.md", "Bilingual manuscript completeness audit report"),
    PackageItem("results/submission_action_register.csv", "Submission-facing action item register"),
    PackageItem("docs/submission_action_register.md", "Submission-facing action item register report"),
    PackageItem("results/experiment_extension_decision_plan.csv", "Optional experiment extension decision plan"),
    PackageItem("docs/experiment_extension_decision_plan.md", "Optional experiment extension decision plan report"),
    PackageItem("results/reproducibility_checksum_manifest.csv", "Stable artifact SHA256/size checksum manifest"),
    PackageItem("docs/reproducibility_checksum_manifest.md", "Stable artifact checksum manifest report"),
    PackageItem("results/reproducibility_checksum_verification.csv", "Checksum manifest verification rows"),
    PackageItem("docs/reproducibility_checksum_verification.md", "Checksum manifest verification report"),
    PackageItem("results/radius_interpolation_summary.csv", "Communication-radius interpolation summary"),
    PackageItem("results/radius_interpolation_notes.md", "Communication-radius interpolation notes"),
    PackageItem("results/figure_asset_audit.csv", "Technical audit of generated figure assets"),
    PackageItem("docs/figure_asset_audit.md", "Figure asset audit report"),
    PackageItem("results/evaluation_budget_audit.csv", "Evaluation-budget consistency audit"),
    PackageItem("docs/evaluation_budget_audit.md", "Evaluation-budget audit report"),
    PackageItem("results/method_naming_audit.csv", "Method naming consistency audit"),
    PackageItem("docs/method_naming_audit.md", "Method naming audit report"),
    PackageItem("results/supplemental_csv_schema_audit.csv", "Supplemental CSV schema audit"),
    PackageItem("docs/supplemental_csv_schema_audit.md", "Supplemental CSV schema audit report"),
    PackageItem("results/result_provenance_audit.csv", "Result provenance audit"),
    PackageItem("docs/result_provenance_audit.md", "Result provenance audit report"),
    PackageItem("results/speed_robustness_summary.csv", "Target-speed robustness summary"),
    PackageItem("results/edge_feature_ablation_summary.csv", "Edge-feature diagnostic summary"),
    PackageItem("results/per_seed_comm_appendix.csv", "Per-seed appendix data"),
    PackageItem("docs/reproducibility_manifest.md", "Reproducibility command manifest"),
    PackageItem("docs/supplemental_data_readme.md", "Supplemental CSV inventory and interpretation boundaries"),
    PackageItem("docs/checkpoint_inventory.md", "Checkpoint-to-method mapping"),
    PackageItem("docs/runtime_environment_report.md", "Runtime and toolchain report"),
    PackageItem("docs/submission_readiness_report.md", "Current readiness audit"),
    PackageItem("docs/english_manuscript_readiness_audit.md", "English manuscript submission-facing audit"),
]


INTERNAL_ONLY = [
    PackageItem("docs/current_progress_and_next_plan.md", "Long-running project log"),
    PackageItem("docs/paper_asset_build_report.md", "Local build report"),
    PackageItem("docs/evidence_chain_status.md", "Internal evidence tracking"),
    PackageItem("docs/journal_target_shortlist.md", "Submission target planning"),
    PackageItem("docs/journal_template_migration_plan.md", "Target-template migration planning"),
    PackageItem("docs/lag_jsbsim_migration_probe.md", "Future LAG/JSBSim migration readiness probe"),
    PackageItem("docs/lag_role_graph_adapter_test.md", "Duck-typed LAG state-to-role-graph adapter test"),
    PackageItem("results/lag_role_graph_adapter_test.csv", "LAG adapter tensor-shape and graph-invariant checks"),
    PackageItem("docs/lag_role_graph_wrapper_test.md", "Thin reset/step wrapper test for future LAG integration"),
    PackageItem("results/lag_role_graph_wrapper_test.csv", "LAG wrapper reset/step graph refresh checks"),
    PackageItem("envs/uav_intercept_3d_env.py", "Prototype 3DOF heterogeneous interception environment"),
    PackageItem("scripts/smoke_test_intercept_3d_env.py", "3DOF environment interface smoke test"),
    PackageItem("docs/intercept_3d_smoke_test.md", "3DOF environment smoke-test report"),
    PackageItem("results/intercept_3d_smoke_test.csv", "3DOF environment smoke-test rows"),
    PackageItem("results/visualization_and_intent_diagnostics.md", "Internal intent diagnostic notes"),
    PackageItem("docs/lag_migration_checklist.md", "Future migration planning"),
]


NOT_READY_FOR_SUBMISSION = [
    PackageItem("PDF files", "Not generated in current runtime because xelatex/bibtex are unavailable"),
    PackageItem("Journal-specific template files", "Target journal has not been selected or adapted yet"),
    PackageItem("Real LAG/JSBSim validation output", "Blocked by missing JSBSim data/submodule"),
]


def status(rel: str) -> str:
    if rel.endswith("/"):
        path = ROOT / rel.rstrip("/")
        return "present" if path.exists() and any(path.iterdir()) else "missing"
    if rel in {"PDF files", "Journal-specific template files", "Real LAG/JSBSim validation output"}:
        return "not ready"
    path = ROOT / rel
    return "present" if path.exists() and path.stat().st_size > 0 else "missing"


def section(title: str, items: list[PackageItem]) -> list[str]:
    lines = [
        f"## {title}",
        "",
        "| Item | Status | Note |",
        "|---|---|---|",
    ]
    for item in items:
        lines.append(f"| `{item.rel}` | {status(item.rel)} | {item.note} |")
    lines.append("")
    return lines


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Submission Package Manifest",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Purpose:",
        "",
        "```text",
        "Separate files for manuscript submission, supplemental evidence, and internal project tracking.",
        "This manifest does not compile PDFs and does not select a journal template.",
        "```",
        "",
        "## Package Decision",
        "",
        "```text",
        "Use paper_latex_3d_en/ for the current English Gate 1 submission route.",
        "Use paper_latex/ only if a Chinese route is explicitly selected and updated to the same Gate 1 claim boundary.",
        "Include the Gate 1 result tables and figures required by the chosen LaTeX project.",
        "Keep internal diagnostics and long-running progress logs out of the actual journal submission unless requested as supplementary material.",
        "```",
        "",
    ]
    lines.extend(section("Chinese Manuscript Package", CHINESE_MANUSCRIPT))
    lines.extend(section("English Manuscript Package", ENGLISH_MANUSCRIPT))
    lines.extend(section("Shared Tables and Figures", SHARED_TABLES_FIGURES))
    lines.extend(section("Supplemental Evidence Candidates", SUPPLEMENTAL_EVIDENCE))
    lines.extend(section("Internal-Only Project Materials", INTERNAL_ONLY))
    lines.extend(section("Not Ready in Current Runtime", NOT_READY_FOR_SUBMISSION))
    lines.extend(
        [
            "## Recommended Submission Packaging Order",
            "",
            "1. Choose Chinese or English route.",
            "2. Compile the selected LaTeX project in a machine with `xelatex` and `bibtex`.",
            "3. Inspect generated PDF layout manually.",
            "4. Adapt to the target journal template.",
            "5. Attach only necessary supplemental CSVs/reports if the venue permits supplementary files.",
            "",
        ]
    )
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
