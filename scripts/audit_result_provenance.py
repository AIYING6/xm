from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / "results" / "result_provenance_audit.csv"
OUT_MD = ROOT / "docs" / "result_provenance_audit.md"


@dataclass(frozen=True)
class ProvenanceItem:
    artifact: str
    artifact_type: str
    source_data: str
    generator_script: str
    notes: str


ITEMS = [
    ProvenanceItem("results/latex_final_comm_300_table.tex", "table", "results/final_comm_300_summary.csv", "scripts/make_latex_tables.py", "Final 300-episode cross-radius main table."),
    ProvenanceItem("results/latex_final_300_paired_ci_table.tex", "table", "results/final_300_paired_statistics.csv", "scripts/analyze_final_300_statistics.py", "Seed-paired descriptive confidence interval table."),
    ProvenanceItem("results/latex_comm_dropout_robustness_table.tex", "table", "results/comm_dropout_robustness_summary.csv", "scripts/evaluate_comm_dropout_robustness.py", "Generated during communication-dropout diagnostic evaluation."),
    ProvenanceItem("results/latex_comm_dropout_paired_ci_table.tex", "table", "results/comm_dropout_paired_statistics.csv", "scripts/analyze_comm_dropout_statistics.py", "Communication-dropout seed-paired descriptive statistics."),
    ProvenanceItem("results/latex_aggregate_robustness_table.tex", "table", "results/aggregate_robustness_summary.csv", "scripts/analyze_aggregate_robustness.py", "Aggregate cross-condition robustness table."),
    ProvenanceItem("results/latex_radius_interpolation_table.tex", "table", "results/radius_interpolation_summary.csv", "scripts/evaluate_radius_interpolation.py", "Communication-radius interpolation diagnostic table."),
    ProvenanceItem("results/latex_ablation_comm_table.tex", "table", "results/paper_comm_results.csv", "scripts/make_latex_tables.py", "Legacy 100-episode communication ablation table."),
    ProvenanceItem("results/latex_main_comm_table.tex", "table", "results/paper_comm_results.csv", "scripts/make_latex_tables.py", "Legacy main communication table retained for appendix/backward compatibility."),
    ProvenanceItem("results/latex_speed_robustness_table.tex", "table", "results/speed_robustness_summary.csv", "scripts/make_latex_tables.py", "Target-speed robustness table."),
    ProvenanceItem("results/latex_edge_feature_ablation_table.tex", "table", "results/edge_feature_ablation_summary.csv", "scripts/make_latex_tables.py", "Evaluation-time edge feature masking table."),
    ProvenanceItem("results/latex_training_settings_table.tex", "table", "script_static", "scripts/make_latex_tables.py", "Training and evaluation settings are encoded in the table generator."),
    ProvenanceItem("results/figures/final_300_success_rate.png", "figure", "results/final_comm_300_summary.csv", "scripts/plot_final_300_results.py", "Final 300-episode success-rate figure."),
    ProvenanceItem("results/figures/final_300_collision_rate.png", "figure", "results/final_comm_300_summary.csv", "scripts/plot_final_300_results.py", "Final 300-episode collision-rate figure."),
    ProvenanceItem("results/figures/comm_success_rate.png", "figure", "results/paper_comm_results.csv", "scripts/plot_comm_results.py", "Legacy communication-radius success-rate figure."),
    ProvenanceItem("results/figures/comm_collision_rate.png", "figure", "results/paper_comm_results.csv", "scripts/plot_comm_results.py", "Legacy communication-radius collision-rate figure."),
    ProvenanceItem("results/figures/per_seed_success_scatter.png", "figure", "results/per_seed_comm_appendix.csv", "scripts/build_paper_appendix.py", "Per-seed success-rate appendix scatter."),
    ProvenanceItem("results/figures/per_seed_collision_scatter.png", "figure", "results/per_seed_comm_appendix.csv", "scripts/build_paper_appendix.py", "Per-seed collision-rate appendix scatter."),
    ProvenanceItem("results/figures/edge_feature_ablation_delta.png", "figure", "results/edge_feature_ablation_summary.csv", "scripts/plot_edge_feature_ablation.py", "Edge feature masking delta figure."),
    ProvenanceItem("results/figures/speed_robustness_success_r4.png", "figure", "results/speed_robustness_summary.csv", "scripts/plot_speed_robustness.py", "Target-speed success-rate robustness at radius 4."),
    ProvenanceItem("results/figures/speed_robustness_collision_r4.png", "figure", "results/speed_robustness_summary.csv", "scripts/plot_speed_robustness.py", "Target-speed collision-rate robustness at radius 4."),
    ProvenanceItem("results/figures/speed_robustness_success_r8.png", "figure", "results/speed_robustness_summary.csv", "scripts/plot_speed_robustness.py", "Target-speed success-rate robustness at radius 8."),
    ProvenanceItem("results/figures/speed_robustness_collision_r8.png", "figure", "results/speed_robustness_summary.csv", "scripts/plot_speed_robustness.py", "Target-speed collision-rate robustness at radius 8."),
    ProvenanceItem("results/figures/comm_dropout_success_rate.png", "figure", "results/comm_dropout_robustness_summary.csv", "scripts/plot_comm_dropout_robustness.py", "Communication-dropout success-rate figure."),
    ProvenanceItem("results/figures/comm_dropout_collision_rate.png", "figure", "results/comm_dropout_robustness_summary.csv", "scripts/plot_comm_dropout_robustness.py", "Communication-dropout collision-rate figure."),
    ProvenanceItem("results/figures/radius_interpolation_success_rate.png", "figure", "results/radius_interpolation_summary.csv", "scripts/plot_radius_interpolation.py", "Communication-radius interpolation success-rate figure."),
    ProvenanceItem("results/figures/radius_interpolation_collision_rate.png", "figure", "results/radius_interpolation_summary.csv", "scripts/plot_radius_interpolation.py", "Communication-radius interpolation collision-rate figure."),
    ProvenanceItem("results/figures/method_overview_ea_rg_mappo_s.png", "figure", "script_static", "scripts/plot_method_overview.py", "Method overview diagram generated from scripted layout."),
    ProvenanceItem("results/figures/trajectory_ri_advantage_r4.png", "figure", "results/final_comm_300_eval.csv", "scripts/plot_trajectory_cases.py", "Qualitative trajectory case at radius 4."),
    ProvenanceItem("results/figures/trajectory_ri_advantage_r10.png", "figure", "results/final_comm_300_eval.csv", "scripts/plot_trajectory_cases.py", "Qualitative trajectory case at radius 10."),
    ProvenanceItem("results/figures/ri_attention_heatmap_r4.png", "figure", "results/final_comm_300_eval.csv", "scripts/plot_ri_attention_heatmap.py", "Attention heatmap case at radius 4."),
    ProvenanceItem("results/figures/ri_attention_heatmap_r10.png", "figure", "results/final_comm_300_eval.csv", "scripts/plot_ri_attention_heatmap.py", "Attention heatmap case at radius 10."),
    ProvenanceItem("results/figures/intent_confusion_ri_staged_r8.png", "figure", "results/intent_confusion_ri_staged_r8.csv", "scripts/plot_intent_confusion.py", "Exploratory intent diagnostic figure; not a main contribution."),
    ProvenanceItem("results/figures/intent_confusion_ri_balanced_seed1_r8.png", "figure", "results/intent_confusion_ri_balanced_seed1_r8.csv", "scripts/plot_intent_confusion.py", "Exploratory balanced-intent diagnostic figure; not a main contribution."),
    ProvenanceItem("docs/figure_asset_audit.md", "audit", "results/figure_asset_audit.csv", "scripts/audit_figure_assets.py", "Figure readability/nonblank audit report."),
    ProvenanceItem("docs/evaluation_budget_audit.md", "audit", "results/evaluation_budget_audit.csv", "scripts/audit_evaluation_budget_consistency.py", "Evaluation episode-budget consistency audit report."),
    ProvenanceItem("docs/method_naming_audit.md", "audit", "results/method_naming_audit.csv", "scripts/audit_method_naming_consistency.py", "Method naming consistency audit report."),
    ProvenanceItem("docs/supplemental_csv_schema_audit.md", "audit", "results/supplemental_csv_schema_audit.csv", "scripts/audit_supplemental_csv_schema.py", "Supplemental CSV schema audit report."),
    ProvenanceItem("docs/lag_jsbsim_migration_probe.md", "report", "results/lag_jsbsim_migration_probe.csv", "scripts/probe_lag_jsbsim_migration.py", "Future LAG/JSBSim migration readiness report."),
    ProvenanceItem("docs/lag_role_graph_adapter_test.md", "report", "results/lag_role_graph_adapter_test.csv", "scripts/test_lag_role_graph_adapter.py", "LAG-like state-to-role-graph adapter test report."),
    ProvenanceItem("docs/lag_role_graph_wrapper_test.md", "report", "results/lag_role_graph_wrapper_test.csv", "scripts/test_lag_role_graph_wrapper.py", "LAG-like reset/step graph wrapper test report."),
    ProvenanceItem("docs/intercept_3d_smoke_test.md", "report", "results/intercept_3d_smoke_test.csv", "scripts/smoke_test_intercept_3d_env.py", "3DOF heterogeneous interception environment smoke-test report."),
    ProvenanceItem("results/intercept_3d_policy_eval.csv", "data", "results/ri_gmappo_3d_smoke/actor_critic_latest.pt", "scripts/evaluate_ri_gmappo_3d.py", "3DOF checkpoint evaluation smoke diagnostic; not a paper learning result."),
    ProvenanceItem("docs/intercept_3d_policy_eval.md", "report", "results/intercept_3d_policy_eval.csv", "scripts/evaluate_ri_gmappo_3d.py", "3DOF checkpoint evaluation metric summary."),
    ProvenanceItem("docs/claim_evidence_matrix.md", "report", "results/claim_evidence_matrix.csv", "scripts/write_claim_evidence_matrix.py", "Paper claim-to-evidence matrix."),
    ProvenanceItem("docs/manuscript_evidence_reference_audit.md", "audit", "results/manuscript_evidence_reference_audit.csv", "scripts/audit_manuscript_evidence_references.py", "Manuscript evidence-reference audit report."),
    ProvenanceItem("docs/bilingual_numeric_consistency_audit.md", "audit", "results/bilingual_numeric_consistency_audit.csv", "scripts/audit_bilingual_numeric_consistency.py", "Bilingual manuscript numeric consistency audit report."),
    ProvenanceItem("docs/latex_reference_integrity_audit.md", "audit", "results/latex_reference_integrity_audit.csv", "scripts/audit_latex_reference_integrity.py", "Bilingual LaTeX label/reference integrity audit report."),
    ProvenanceItem("docs/bilingual_manuscript_completeness_audit.md", "audit", "results/bilingual_manuscript_completeness_audit.csv", "scripts/audit_bilingual_manuscript_completeness.py", "Bilingual manuscript completeness audit report."),
    ProvenanceItem("docs/submission_action_register.md", "report", "results/submission_action_register.csv", "scripts/write_submission_action_register.py", "Submission-facing action item register."),
    ProvenanceItem("docs/experiment_extension_decision_plan.md", "report", "results/experiment_extension_decision_plan.csv", "scripts/write_experiment_extension_decision_plan.py", "Optional next-experiment decision plan."),
    ProvenanceItem("docs/reproducibility_checksum_manifest.md", "report", "results/reproducibility_checksum_manifest.csv", "scripts/write_reproducibility_checksum_manifest.py", "Stable artifact SHA256/size checksum manifest."),
    ProvenanceItem("docs/reproducibility_checksum_verification.md", "audit", "results/reproducibility_checksum_verification.csv", "scripts/verify_reproducibility_checksum_manifest.py", "Checksum manifest verification audit report."),
    ProvenanceItem("docs/submission_readiness_report.md", "report", "script_static", "scripts/write_submission_readiness_report.py", "Submission readiness checklist generated from expected project assets."),
    ProvenanceItem("docs/submission_package_manifest.md", "report", "script_static", "scripts/write_submission_package_manifest.py", "Submission package manifest generated from curated package lists."),
    ProvenanceItem("docs/supplemental_data_readme.md", "report", "script_static", "scripts/write_supplemental_data_readme.py", "Supplemental CSV inventory and interpretation-boundary README."),
    ProvenanceItem("docs/english_manuscript_readiness_audit.md", "audit", "script_static", "scripts/audit_english_manuscript_readiness.py", "English manuscript readiness audit generated from manuscript and LaTeX files."),
]


def is_existing_nonempty(rel: str) -> bool:
    path = ROOT / rel
    return path.exists() and path.stat().st_size > 0


def csv_rows(rel: str) -> int | None:
    if rel == "script_static" or not rel.endswith(".csv"):
        return None
    path = ROOT / rel
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8", newline="") as f:
        return sum(1 for _ in csv.DictReader(f))


def check_item(item: ProvenanceItem) -> dict[str, str]:
    errors = []
    if not is_existing_nonempty(item.artifact):
        errors.append("artifact_missing_or_empty")
    if item.source_data != "script_static":
        if not is_existing_nonempty(item.source_data):
            errors.append("source_missing_or_empty")
        elif item.source_data.endswith(".csv") and csv_rows(item.source_data) == 0:
            errors.append("source_csv_has_no_rows")
    if not is_existing_nonempty(item.generator_script):
        errors.append("generator_missing_or_empty")

    return {
        "artifact": item.artifact,
        "artifact_type": item.artifact_type,
        "source_data": item.source_data,
        "source_rows": "" if (rows := csv_rows(item.source_data)) is None else str(rows),
        "generator_script": item.generator_script,
        "status": "OK" if not errors else "FAILED",
        "notes": item.notes if not errors else f"{item.notes} Errors: {', '.join(errors)}",
    }


def write_csv(rows: list[dict[str, str]]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "artifact",
                "artifact_type",
                "source_data",
                "source_rows",
                "generator_script",
                "status",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: list[dict[str, str]]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    failed = [r for r in rows if r["status"] != "OK"]
    type_counts: dict[str, int] = {}
    for row in rows:
        type_counts[row["artifact_type"]] = type_counts.get(row["artifact_type"], 0) + 1

    lines = [
        "# Result Provenance Audit",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Purpose:",
        "",
        "```text",
        "Check that publishable tables, figures, reports, and audits can be traced to source data and generator scripts.",
        "Rows marked script_static are generated directly from curated constants or manuscript/project files rather than one CSV.",
        "```",
        "",
        "## Summary",
        "",
        "```text",
        f"artifacts_checked = {len(rows)}",
        f"failures = {len(failed)}",
        *[f"{key} = {value}" for key, value in sorted(type_counts.items())],
        "```",
        "",
        "## Checked Artifacts",
        "",
        "| Artifact | Type | Source | Generator | Status |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['artifact']}` | {row['artifact_type']} | `{row['source_data']}` | `{row['generator_script']}` | {row['status']} |"
        )

    if failed:
        lines.extend(["", "## Failures", ""])
        for row in failed:
            lines.append(f"- `{row['artifact']}`: {row['notes']}")

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = [check_item(item) for item in ITEMS]
    write_csv(rows)
    write_markdown(rows)
    failures = [row for row in rows if row["status"] != "OK"]
    print(f"artifacts checked: {len(rows)}")
    print(f"failures: {len(failures)}")
    if failures:
        for row in failures:
            print(f"- {row['artifact']}: {row['notes']}")
        raise SystemExit(1)
    print("OK")


if __name__ == "__main__":
    main()
