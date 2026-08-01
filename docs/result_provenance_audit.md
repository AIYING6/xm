# Result Provenance Audit

Generated: 2026-08-02T01:41:06

Purpose:

```text
Check that publishable tables, figures, reports, and audits can be traced to source data and generator scripts.
Rows marked script_static are generated directly from curated constants or manuscript/project files rather than one CSV.
```

## Summary

```text
artifacts_checked = 56
failures = 0
audit = 10
data = 1
figure = 22
report = 12
table = 11
```

## Checked Artifacts

| Artifact | Type | Source | Generator | Status |
|---|---|---|---|---|
| `results/latex_final_comm_300_table.tex` | table | `results/final_comm_300_summary.csv` | `scripts/make_latex_tables.py` | OK |
| `results/latex_final_300_paired_ci_table.tex` | table | `results/final_300_paired_statistics.csv` | `scripts/analyze_final_300_statistics.py` | OK |
| `results/latex_comm_dropout_robustness_table.tex` | table | `results/comm_dropout_robustness_summary.csv` | `scripts/evaluate_comm_dropout_robustness.py` | OK |
| `results/latex_comm_dropout_paired_ci_table.tex` | table | `results/comm_dropout_paired_statistics.csv` | `scripts/analyze_comm_dropout_statistics.py` | OK |
| `results/latex_aggregate_robustness_table.tex` | table | `results/aggregate_robustness_summary.csv` | `scripts/analyze_aggregate_robustness.py` | OK |
| `results/latex_radius_interpolation_table.tex` | table | `results/radius_interpolation_summary.csv` | `scripts/evaluate_radius_interpolation.py` | OK |
| `results/latex_ablation_comm_table.tex` | table | `results/paper_comm_results.csv` | `scripts/make_latex_tables.py` | OK |
| `results/latex_main_comm_table.tex` | table | `results/paper_comm_results.csv` | `scripts/make_latex_tables.py` | OK |
| `results/latex_speed_robustness_table.tex` | table | `results/speed_robustness_summary.csv` | `scripts/make_latex_tables.py` | OK |
| `results/latex_edge_feature_ablation_table.tex` | table | `results/edge_feature_ablation_summary.csv` | `scripts/make_latex_tables.py` | OK |
| `results/latex_training_settings_table.tex` | table | `script_static` | `scripts/make_latex_tables.py` | OK |
| `results/figures/final_300_success_rate.png` | figure | `results/final_comm_300_summary.csv` | `scripts/plot_final_300_results.py` | OK |
| `results/figures/final_300_collision_rate.png` | figure | `results/final_comm_300_summary.csv` | `scripts/plot_final_300_results.py` | OK |
| `results/figures/comm_success_rate.png` | figure | `results/paper_comm_results.csv` | `scripts/plot_comm_results.py` | OK |
| `results/figures/comm_collision_rate.png` | figure | `results/paper_comm_results.csv` | `scripts/plot_comm_results.py` | OK |
| `results/figures/per_seed_success_scatter.png` | figure | `results/per_seed_comm_appendix.csv` | `scripts/build_paper_appendix.py` | OK |
| `results/figures/per_seed_collision_scatter.png` | figure | `results/per_seed_comm_appendix.csv` | `scripts/build_paper_appendix.py` | OK |
| `results/figures/edge_feature_ablation_delta.png` | figure | `results/edge_feature_ablation_summary.csv` | `scripts/plot_edge_feature_ablation.py` | OK |
| `results/figures/speed_robustness_success_r4.png` | figure | `results/speed_robustness_summary.csv` | `scripts/plot_speed_robustness.py` | OK |
| `results/figures/speed_robustness_collision_r4.png` | figure | `results/speed_robustness_summary.csv` | `scripts/plot_speed_robustness.py` | OK |
| `results/figures/speed_robustness_success_r8.png` | figure | `results/speed_robustness_summary.csv` | `scripts/plot_speed_robustness.py` | OK |
| `results/figures/speed_robustness_collision_r8.png` | figure | `results/speed_robustness_summary.csv` | `scripts/plot_speed_robustness.py` | OK |
| `results/figures/comm_dropout_success_rate.png` | figure | `results/comm_dropout_robustness_summary.csv` | `scripts/plot_comm_dropout_robustness.py` | OK |
| `results/figures/comm_dropout_collision_rate.png` | figure | `results/comm_dropout_robustness_summary.csv` | `scripts/plot_comm_dropout_robustness.py` | OK |
| `results/figures/radius_interpolation_success_rate.png` | figure | `results/radius_interpolation_summary.csv` | `scripts/plot_radius_interpolation.py` | OK |
| `results/figures/radius_interpolation_collision_rate.png` | figure | `results/radius_interpolation_summary.csv` | `scripts/plot_radius_interpolation.py` | OK |
| `results/figures/method_overview_ea_rg_mappo_s.png` | figure | `script_static` | `scripts/plot_method_overview.py` | OK |
| `results/figures/trajectory_ri_advantage_r4.png` | figure | `results/final_comm_300_eval.csv` | `scripts/plot_trajectory_cases.py` | OK |
| `results/figures/trajectory_ri_advantage_r10.png` | figure | `results/final_comm_300_eval.csv` | `scripts/plot_trajectory_cases.py` | OK |
| `results/figures/ri_attention_heatmap_r4.png` | figure | `results/final_comm_300_eval.csv` | `scripts/plot_ri_attention_heatmap.py` | OK |
| `results/figures/ri_attention_heatmap_r10.png` | figure | `results/final_comm_300_eval.csv` | `scripts/plot_ri_attention_heatmap.py` | OK |
| `results/figures/intent_confusion_ri_staged_r8.png` | figure | `results/intent_confusion_ri_staged_r8.csv` | `scripts/plot_intent_confusion.py` | OK |
| `results/figures/intent_confusion_ri_balanced_seed1_r8.png` | figure | `results/intent_confusion_ri_balanced_seed1_r8.csv` | `scripts/plot_intent_confusion.py` | OK |
| `docs/figure_asset_audit.md` | audit | `results/figure_asset_audit.csv` | `scripts/audit_figure_assets.py` | OK |
| `docs/evaluation_budget_audit.md` | audit | `results/evaluation_budget_audit.csv` | `scripts/audit_evaluation_budget_consistency.py` | OK |
| `docs/method_naming_audit.md` | audit | `results/method_naming_audit.csv` | `scripts/audit_method_naming_consistency.py` | OK |
| `docs/supplemental_csv_schema_audit.md` | audit | `results/supplemental_csv_schema_audit.csv` | `scripts/audit_supplemental_csv_schema.py` | OK |
| `docs/lag_jsbsim_migration_probe.md` | report | `results/lag_jsbsim_migration_probe.csv` | `scripts/probe_lag_jsbsim_migration.py` | OK |
| `docs/lag_role_graph_adapter_test.md` | report | `results/lag_role_graph_adapter_test.csv` | `scripts/test_lag_role_graph_adapter.py` | OK |
| `docs/lag_role_graph_wrapper_test.md` | report | `results/lag_role_graph_wrapper_test.csv` | `scripts/test_lag_role_graph_wrapper.py` | OK |
| `docs/intercept_3d_smoke_test.md` | report | `results/intercept_3d_smoke_test.csv` | `scripts/smoke_test_intercept_3d_env.py` | OK |
| `results/intercept_3d_policy_eval.csv` | data | `results/ri_gmappo_3d_smoke/actor_critic_latest.pt` | `scripts/evaluate_ri_gmappo_3d.py` | OK |
| `docs/intercept_3d_policy_eval.md` | report | `results/intercept_3d_policy_eval.csv` | `scripts/evaluate_ri_gmappo_3d.py` | OK |
| `docs/claim_evidence_matrix.md` | report | `results/claim_evidence_matrix.csv` | `scripts/write_claim_evidence_matrix.py` | OK |
| `docs/manuscript_evidence_reference_audit.md` | audit | `results/manuscript_evidence_reference_audit.csv` | `scripts/audit_manuscript_evidence_references.py` | OK |
| `docs/bilingual_numeric_consistency_audit.md` | audit | `results/bilingual_numeric_consistency_audit.csv` | `scripts/audit_bilingual_numeric_consistency.py` | OK |
| `docs/latex_reference_integrity_audit.md` | audit | `results/latex_reference_integrity_audit.csv` | `scripts/audit_latex_reference_integrity.py` | OK |
| `docs/bilingual_manuscript_completeness_audit.md` | audit | `results/bilingual_manuscript_completeness_audit.csv` | `scripts/audit_bilingual_manuscript_completeness.py` | OK |
| `docs/submission_action_register.md` | report | `results/submission_action_register.csv` | `scripts/write_submission_action_register.py` | OK |
| `docs/experiment_extension_decision_plan.md` | report | `results/experiment_extension_decision_plan.csv` | `scripts/write_experiment_extension_decision_plan.py` | OK |
| `docs/reproducibility_checksum_manifest.md` | report | `results/reproducibility_checksum_manifest.csv` | `scripts/write_reproducibility_checksum_manifest.py` | OK |
| `docs/reproducibility_checksum_verification.md` | audit | `results/reproducibility_checksum_verification.csv` | `scripts/verify_reproducibility_checksum_manifest.py` | OK |
| `docs/submission_readiness_report.md` | report | `script_static` | `scripts/write_submission_readiness_report.py` | OK |
| `docs/submission_package_manifest.md` | report | `script_static` | `scripts/write_submission_package_manifest.py` | OK |
| `docs/supplemental_data_readme.md` | report | `script_static` | `scripts/write_supplemental_data_readme.py` | OK |
| `docs/english_manuscript_readiness_audit.md` | audit | `script_static` | `scripts/audit_english_manuscript_readiness.py` | OK |
