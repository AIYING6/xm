from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_FILES = [
    # Final checkpoints
    "results/mappo_curriculum_slow_150/actor_critic_latest.pt",
    "results/mappo_curriculum_slow_seed1_150/actor_critic_latest.pt",
    "results/mappo_curriculum_slow_seed2_150/actor_critic_latest.pt",
    "results/gat_mappo_hybrid_slow_60_plus90/actor_critic_latest.pt",
    "results/gat_mappo_hybrid_slow_seed1_60_plus90/actor_critic_latest.pt",
    "results/gat_mappo_hybrid_slow_seed2_60_plus90/actor_critic_latest.pt",
    "results/ri_gmappo_edge_stage2_rand_seed0_20/actor_critic_latest.pt",
    "results/ri_gmappo_edge_stage2_rand_seed1_20/actor_critic_latest.pt",
    "results/ri_gmappo_edge_stage2_rand_seed2_20/actor_critic_latest.pt",
    "results/ri_gmappo_3d_smoke/actor_critic_latest.pt",
    # Final results
    "results/final_comm_300_eval.csv",
    "results/final_comm_300_summary.csv",
    "results/latex_final_comm_300_table.tex",
    "results/final_300_paired_statistics.csv",
    "results/final_300_paired_statistics.md",
    "results/latex_final_300_paired_ci_table.tex",
    "results/comm_dropout_robustness_eval.csv",
    "results/comm_dropout_robustness_summary.csv",
    "results/comm_dropout_robustness_notes.md",
    "results/latex_comm_dropout_robustness_table.tex",
    "results/comm_dropout_paired_statistics.csv",
    "results/comm_dropout_paired_statistics.md",
    "results/latex_comm_dropout_paired_ci_table.tex",
    "results/aggregate_robustness_summary.csv",
    "results/aggregate_robustness_summary.md",
    "results/latex_aggregate_robustness_table.tex",
    "results/claim_evidence_matrix.csv",
    "results/manuscript_evidence_reference_audit.csv",
    "results/bilingual_numeric_consistency_audit.csv",
    "results/latex_reference_integrity_audit.csv",
    "results/bilingual_manuscript_completeness_audit.csv",
    "results/submission_action_register.csv",
    "results/experiment_extension_decision_plan.csv",
    "results/reproducibility_checksum_manifest.csv",
    "results/reproducibility_checksum_verification.csv",
    "results/radius_interpolation_eval.csv",
    "results/radius_interpolation_summary.csv",
    "results/radius_interpolation_notes.md",
    "results/latex_radius_interpolation_table.tex",
    "results/latex_ablation_comm_table.tex",
    "results/latex_speed_robustness_table.tex",
    "results/latex_edge_feature_ablation_table.tex",
    "results/latex_training_settings_table.tex",
    "results/final_300_eval_notes.md",
    "results/lag_graph_smoke_stats.csv",
    "results/lag_jsbsim_migration_probe.csv",
    "results/lag_role_graph_adapter_test.csv",
    "results/lag_role_graph_wrapper_test.csv",
    "results/intercept_3d_smoke_test.csv",
    "results/intercept_3d_policy_eval.csv",
    "results/intercept_3d_paper_main_table.csv",
    "results/intercept_3d_relay_failure_case_candidates.csv",
    "results/intercept_3d_relay_failure_case_replay.csv",
    "results/edge_feature_ablation_eval.csv",
    "results/edge_feature_ablation_summary.csv",
    "results/edge_feature_ablation_notes.md",
    "results/speed_robustness_eval.csv",
    "results/speed_robustness_summary.csv",
    "results/speed_robustness_notes.md",
    "results/figure_asset_audit.csv",
    "results/evaluation_budget_audit.csv",
    "results/method_naming_audit.csv",
    "results/supplemental_csv_schema_audit.csv",
    "results/result_provenance_audit.csv",
    # Figures
    "results/figures/final_300_success_rate.png",
    "results/figures/final_300_collision_rate.png",
    "results/figures/method_overview_ea_rg_mappo_s.png",
    "results/figures/per_seed_success_scatter.png",
    "results/figures/per_seed_collision_scatter.png",
    "results/figures/trajectory_ri_advantage_r4.png",
    "results/figures/trajectory_ri_advantage_r10.png",
    "results/figures/ri_attention_heatmap_r4.png",
    "results/figures/ri_attention_heatmap_r10.png",
    "results/figures/edge_feature_ablation_delta.png",
    "results/figures/speed_robustness_success_r4.png",
    "results/figures/speed_robustness_collision_r4.png",
    "results/figures/speed_robustness_success_r8.png",
    "results/figures/speed_robustness_collision_r8.png",
    "results/figures/comm_dropout_success_rate.png",
    "results/figures/comm_dropout_collision_rate.png",
    "results/figures/radius_interpolation_success_rate.png",
    "results/figures/radius_interpolation_collision_rate.png",
    "results/figures/intercept_3d_relay_failure_case_replay.png",
    # Manuscript
    "docs/paper_manuscript_zh_v1.md",
    "docs/english_abstract_and_contributions.md",
    "docs/english_introduction_draft.md",
    "docs/english_related_work_draft.md",
    "docs/english_problem_method_draft.md",
    "docs/english_experiments_draft.md",
    "docs/english_discussion_conclusion_draft.md",
    "docs/english_manuscript_draft.md",
    "docs/reproducibility_manifest.md",
    "docs/claim_evidence_matrix.md",
    "docs/manuscript_evidence_reference_audit.md",
    "docs/bilingual_numeric_consistency_audit.md",
    "docs/latex_reference_integrity_audit.md",
    "docs/bilingual_manuscript_completeness_audit.md",
    "docs/submission_action_register.md",
    "docs/experiment_extension_decision_plan.md",
    "docs/reproducibility_checksum_manifest.md",
    "docs/reproducibility_checksum_verification.md",
    "docs/supplemental_data_readme.md",
    "docs/paper_asset_build_report.md",
    "docs/runtime_environment_report.md",
    "docs/checkpoint_inventory.md",
    "docs/submission_readiness_report.md",
    "docs/submission_package_manifest.md",
    "docs/english_manuscript_readiness_audit.md",
    "docs/figure_asset_audit.md",
    "docs/evaluation_budget_audit.md",
    "docs/method_naming_audit.md",
    "docs/supplemental_csv_schema_audit.md",
    "docs/result_provenance_audit.md",
    "docs/evidence_chain_status.md",
    "docs/journal_target_shortlist.md",
    "docs/journal_template_migration_plan.md",
    "docs/related_work_literature_review.md",
    "docs/reference_quality_audit.md",
    "docs/lag_migration_checklist.md",
    "docs/lag_jsbsim_migration_probe.md",
    "docs/lag_role_graph_adapter_test.md",
    "docs/lag_role_graph_wrapper_test.md",
    "docs/intercept_3d_smoke_test.md",
    "docs/intercept_3d_policy_eval.md",
    "docs/intercept_3d_paper_main_table.md",
    "docs/intercept_3d_paper_main_table.tex",
    "docs/intercept_3d_relay_failure_case_candidates.md",
    "docs/intercept_3d_relay_failure_case_replay.md",
    "envs/lag_role_graph_adapter.py",
    "envs/lag_role_graph_wrapper.py",
    "envs/uav_intercept_3d_env.py",
    "paper_latex/main.tex",
    "paper_latex/sections/08_appendix_experiments.tex",
    "paper_latex/references.bib",
    "paper_latex_en/main.tex",
    "paper_latex_en/sections/01_introduction.tex",
    "paper_latex_en/sections/02_related_work.tex",
    "paper_latex_en/sections/03_problem.tex",
    "paper_latex_en/sections/04_method.tex",
    "paper_latex_en/sections/05_experiments.tex",
    "paper_latex_en/sections/06_discussion.tex",
    "paper_latex_en/sections/07_conclusion.tex",
    "paper_latex_en/sections/08_appendix_experiments.tex",
    "paper_latex_en/README.md",
]


REQUIRED_SCRIPTS = [
    "scripts/evaluate_final_comm_300.py",
    "scripts/analyze_final_300_statistics.py",
    "scripts/analyze_comm_dropout_statistics.py",
    "scripts/analyze_aggregate_robustness.py",
    "scripts/evaluate_radius_interpolation.py",
    "scripts/evaluate_comm_dropout_robustness.py",
    "scripts/plot_comm_dropout_robustness.py",
    "scripts/plot_radius_interpolation.py",
    "scripts/audit_figure_assets.py",
    "scripts/audit_evaluation_budget_consistency.py",
    "scripts/audit_method_naming_consistency.py",
    "scripts/audit_supplemental_csv_schema.py",
    "scripts/audit_result_provenance.py",
    "scripts/make_latex_tables.py",
    "scripts/plot_final_300_results.py",
    "scripts/plot_comm_results.py",
    "scripts/build_paper_appendix.py",
    "scripts/check_latex_project.py",
    "scripts/lag_graph_smoke_test.py",
    "scripts/probe_lag_jsbsim_migration.py",
    "scripts/test_lag_role_graph_adapter.py",
    "scripts/test_lag_role_graph_wrapper.py",
    "scripts/smoke_test_intercept_3d_env.py",
    "scripts/evaluate_ri_gmappo_3d.py",
    "scripts/build_3d_paper_tables.py",
    "scripts/find_3d_relay_failure_case_candidates.py",
    "scripts/replay_3d_relay_failure_case.py",
    "scripts/evaluate_edge_feature_ablation.py",
    "scripts/plot_edge_feature_ablation.py",
    "scripts/evaluate_speed_robustness.py",
    "scripts/plot_speed_robustness.py",
    "scripts/check_paper_claim_consistency.py",
    "scripts/check_english_latex_consistency.py",
    "scripts/check_paper_text_risk.py",
    "scripts/build_paper_assets.py",
    "scripts/write_claim_evidence_matrix.py",
    "scripts/audit_manuscript_evidence_references.py",
    "scripts/audit_bilingual_numeric_consistency.py",
    "scripts/audit_latex_reference_integrity.py",
    "scripts/audit_bilingual_manuscript_completeness.py",
    "scripts/write_submission_action_register.py",
    "scripts/write_experiment_extension_decision_plan.py",
    "scripts/write_reproducibility_checksum_manifest.py",
    "scripts/verify_reproducibility_checksum_manifest.py",
    "scripts/write_supplemental_data_readme.py",
    "scripts/write_runtime_environment_report.py",
    "scripts/write_checkpoint_inventory.py",
    "scripts/write_submission_readiness_report.py",
    "scripts/write_submission_package_manifest.py",
    "scripts/audit_english_manuscript_readiness.py",
]


def check_exists(paths: list[str]) -> list[str]:
    errors = []
    for rel in paths:
        path = ROOT / rel
        if not path.exists():
            errors.append(f"missing: {rel}")
        elif path.stat().st_size <= 0:
            errors.append(f"empty: {rel}")
    return errors


def count_csv_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8", newline="") as f:
        return sum(1 for _ in csv.DictReader(f))


def check_csv_shapes() -> list[str]:
    errors = []
    expected = {
        "results/final_comm_300_eval.csv": 36,
        "results/final_comm_300_summary.csv": 12,
        "results/final_300_paired_statistics.csv": 16,
        "results/comm_dropout_robustness_eval.csv": 54,
        "results/comm_dropout_robustness_summary.csv": 18,
        "results/comm_dropout_paired_statistics.csv": 24,
        "results/aggregate_robustness_summary.csv": 6,
        "results/claim_evidence_matrix.csv": 9,
        "results/manuscript_evidence_reference_audit.csv": 51,
        "results/bilingual_numeric_consistency_audit.csv": 47,
        "results/latex_reference_integrity_audit.csv": 86,
        "results/bilingual_manuscript_completeness_audit.csv": 36,
        "results/submission_action_register.csv": 10,
        "results/experiment_extension_decision_plan.csv": 7,
        "results/reproducibility_checksum_manifest.csv": 184,
        "results/reproducibility_checksum_verification.csv": 184,
        "results/radius_interpolation_eval.csv": 27,
        "results/radius_interpolation_summary.csv": 9,
        "results/figure_asset_audit.csv": 27,
        "results/evaluation_budget_audit.csv": 6,
        "results/method_naming_audit.csv": 28,
        "results/supplemental_csv_schema_audit.csv": 32,
        "results/result_provenance_audit.csv": 56,
        "results/paper_comm_results.csv": 20,
        "results/per_seed_comm_appendix.csv": 36,
        "results/lag_graph_smoke_stats.csv": 400,
        "results/lag_jsbsim_migration_probe.csv": 29,
        "results/lag_role_graph_adapter_test.csv": 26,
        "results/lag_role_graph_wrapper_test.csv": 11,
        "results/intercept_3d_smoke_test.csv": 15,
        "results/intercept_3d_policy_eval.csv": 3,
        "results/intercept_3d_paper_main_table.csv": 6,
        "results/intercept_3d_relay_failure_case_candidates.csv": 10,
        "results/intercept_3d_relay_failure_case_replay.csv": 308,
        "results/edge_feature_ablation_eval.csv": 42,
        "results/edge_feature_ablation_summary.csv": 14,
        "results/speed_robustness_eval.csv": 54,
        "results/speed_robustness_summary.csv": 18,
    }
    for rel, rows in expected.items():
        path = ROOT / rel
        if not path.exists():
            errors.append(f"missing csv for row check: {rel}")
            continue
        actual = count_csv_rows(path)
        if actual != rows:
            errors.append(f"unexpected row count: {rel} expected={rows} actual={actual}")
    return errors


def check_final_summary_values() -> list[str]:
    path = ROOT / "results/final_comm_300_summary.csv"
    if not path.exists():
        return ["missing final summary"]
    with path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    target_rows = [r for r in rows if r["method"] == "EA-RG-MAPPO-S"]
    errors = []
    if len(target_rows) != 4:
        errors.append(f"EA-RG-MAPPO-S summary rows expected=4 actual={len(target_rows)}")
    for row in target_rows:
        success = float(row["success_mean"])
        collision = float(row["collision_mean"])
        if success < 0.85:
            errors.append(f"low EA-RG success at radius {row['radius']}: {success}")
        if collision > 0.10:
            errors.append(f"high EA-RG collision at radius {row['radius']}: {collision}")
    return errors


def check_claim_consistency_script() -> list[str]:
    script = ROOT / "scripts" / "check_paper_claim_consistency.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        return [
            "claim consistency check failed",
            result.stdout.strip(),
            result.stderr.strip(),
        ]
    return []


def check_text_risk_script() -> list[str]:
    script = ROOT / "scripts" / "check_paper_text_risk.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        return [
            "paper text risk check failed",
            result.stdout.strip(),
            result.stderr.strip(),
        ]
    return []


def main() -> None:
    errors = []
    errors.extend(check_exists(REQUIRED_FILES))
    errors.extend(check_exists(REQUIRED_SCRIPTS))
    errors.extend(check_csv_shapes())
    errors.extend(check_final_summary_values())
    errors.extend(check_claim_consistency_script())
    errors.extend(check_text_risk_script())

    print(f"required files checked: {len(REQUIRED_FILES)}")
    print(f"required scripts checked: {len(REQUIRED_SCRIPTS)}")
    if errors:
        print("FAILED")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print("OK")


if __name__ == "__main__":
    main()
