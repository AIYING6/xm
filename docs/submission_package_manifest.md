# Submission Package Manifest

Generated: 2026-07-16T22:22:50

Purpose:

```text
Separate files for manuscript submission, supplemental evidence, and internal project tracking.
This manifest does not compile PDFs and does not select a journal template.
```

## Package Decision

```text
Use paper_latex_en/ for an English submission route.
Use paper_latex/ for a Chinese submission route.
Include shared results/ tables and figures required by the chosen LaTeX project.
Keep internal diagnostics and long-running progress logs out of the actual journal submission unless requested as supplementary material.
```

## Chinese Manuscript Package

| Item | Status | Note |
|---|---|---|
| `paper_latex/main.tex` | present | Chinese LaTeX manuscript entry point |
| `paper_latex/sections/` | present | Chinese LaTeX section files |
| `paper_latex/references.bib` | present | Shared BibTeX database |

## English Manuscript Package

| Item | Status | Note |
|---|---|---|
| `paper_latex_en/main.tex` | present | English LaTeX manuscript entry point |
| `paper_latex_en/sections/` | present | English LaTeX section files |
| `paper_latex/references.bib` | present | Shared BibTeX database |

## Shared Tables and Figures

| Item | Status | Note |
|---|---|---|
| `results/latex_training_settings_table.tex` | present | Training/evaluation settings table |
| `results/latex_final_comm_300_table.tex` | present | Final 300-episode main table |
| `results/latex_final_300_paired_ci_table.tex` | present | Seed-paired descriptive confidence-interval table |
| `results/latex_comm_dropout_robustness_table.tex` | present | Appendix communication-dropout diagnostic table |
| `results/latex_comm_dropout_paired_ci_table.tex` | present | Appendix communication-dropout paired confidence-interval table |
| `results/latex_aggregate_robustness_table.tex` | present | Appendix aggregate robustness diagnostic table |
| `results/latex_radius_interpolation_table.tex` | present | Appendix communication-radius interpolation table |
| `results/latex_ablation_comm_table.tex` | present | Ablation table |
| `results/latex_speed_robustness_table.tex` | present | Appendix target-speed robustness table |
| `results/latex_edge_feature_ablation_table.tex` | present | Appendix edge-feature masking table |
| `results/figures/method_overview_ea_rg_mappo_s.png` | present | Method overview figure |
| `results/figures/final_300_success_rate.png` | present | Final success-rate figure |
| `results/figures/final_300_collision_rate.png` | present | Final collision-rate figure |
| `results/figures/speed_robustness_success_r4.png` | present | Appendix robustness figure |
| `results/figures/speed_robustness_collision_r4.png` | present | Appendix robustness figure |
| `results/figures/speed_robustness_success_r8.png` | present | Appendix robustness figure |
| `results/figures/speed_robustness_collision_r8.png` | present | Appendix robustness figure |
| `results/figures/comm_dropout_success_rate.png` | present | Appendix communication-dropout figure |
| `results/figures/comm_dropout_collision_rate.png` | present | Appendix communication-dropout figure |
| `results/figures/radius_interpolation_success_rate.png` | present | Appendix communication-radius interpolation figure |
| `results/figures/radius_interpolation_collision_rate.png` | present | Appendix communication-radius interpolation figure |
| `results/figures/edge_feature_ablation_delta.png` | present | Appendix mechanism diagnostic figure |

## Supplemental Evidence Candidates

| Item | Status | Note |
|---|---|---|
| `results/final_comm_300_eval.csv` | present | Raw final evaluation rows |
| `results/final_comm_300_summary.csv` | present | Final evaluation summary |
| `results/final_300_paired_statistics.csv` | present | Seed-paired descriptive confidence-interval statistics |
| `results/final_300_paired_statistics.md` | present | Plain-language paired-statistics notes |
| `results/comm_dropout_robustness_eval.csv` | present | Communication-dropout diagnostic raw rows |
| `results/comm_dropout_robustness_summary.csv` | present | Communication-dropout diagnostic summary |
| `results/comm_dropout_robustness_notes.md` | present | Communication-dropout diagnostic notes |
| `results/comm_dropout_paired_statistics.csv` | present | Communication-dropout seed-paired descriptive statistics |
| `results/comm_dropout_paired_statistics.md` | present | Communication-dropout paired-statistics notes |
| `results/aggregate_robustness_summary.csv` | present | Aggregate cross-condition robustness summary |
| `results/aggregate_robustness_summary.md` | present | Aggregate robustness summary notes |
| `results/claim_evidence_matrix.csv` | present | Claim-to-evidence matrix |
| `docs/claim_evidence_matrix.md` | present | Claim-to-evidence matrix report |
| `results/manuscript_evidence_reference_audit.csv` | present | Manuscript evidence-reference audit |
| `docs/manuscript_evidence_reference_audit.md` | present | Manuscript evidence-reference audit report |
| `results/bilingual_numeric_consistency_audit.csv` | present | Bilingual manuscript numeric consistency audit |
| `docs/bilingual_numeric_consistency_audit.md` | present | Bilingual manuscript numeric consistency audit report |
| `results/latex_reference_integrity_audit.csv` | present | LaTeX label/reference integrity audit |
| `docs/latex_reference_integrity_audit.md` | present | LaTeX label/reference integrity audit report |
| `results/bilingual_manuscript_completeness_audit.csv` | present | Bilingual manuscript completeness audit |
| `docs/bilingual_manuscript_completeness_audit.md` | present | Bilingual manuscript completeness audit report |
| `results/submission_action_register.csv` | present | Submission-facing action item register |
| `docs/submission_action_register.md` | present | Submission-facing action item register report |
| `results/experiment_extension_decision_plan.csv` | present | Optional experiment extension decision plan |
| `docs/experiment_extension_decision_plan.md` | present | Optional experiment extension decision plan report |
| `results/reproducibility_checksum_manifest.csv` | present | Stable artifact SHA256/size checksum manifest |
| `docs/reproducibility_checksum_manifest.md` | present | Stable artifact checksum manifest report |
| `results/reproducibility_checksum_verification.csv` | present | Checksum manifest verification rows |
| `docs/reproducibility_checksum_verification.md` | present | Checksum manifest verification report |
| `results/radius_interpolation_summary.csv` | present | Communication-radius interpolation summary |
| `results/radius_interpolation_notes.md` | present | Communication-radius interpolation notes |
| `results/figure_asset_audit.csv` | present | Technical audit of generated figure assets |
| `docs/figure_asset_audit.md` | present | Figure asset audit report |
| `results/evaluation_budget_audit.csv` | present | Evaluation-budget consistency audit |
| `docs/evaluation_budget_audit.md` | present | Evaluation-budget audit report |
| `results/method_naming_audit.csv` | present | Method naming consistency audit |
| `docs/method_naming_audit.md` | present | Method naming audit report |
| `results/supplemental_csv_schema_audit.csv` | present | Supplemental CSV schema audit |
| `docs/supplemental_csv_schema_audit.md` | present | Supplemental CSV schema audit report |
| `results/result_provenance_audit.csv` | present | Result provenance audit |
| `docs/result_provenance_audit.md` | present | Result provenance audit report |
| `results/speed_robustness_summary.csv` | present | Target-speed robustness summary |
| `results/edge_feature_ablation_summary.csv` | present | Edge-feature diagnostic summary |
| `results/per_seed_comm_appendix.csv` | present | Per-seed appendix data |
| `docs/reproducibility_manifest.md` | present | Reproducibility command manifest |
| `docs/supplemental_data_readme.md` | present | Supplemental CSV inventory and interpretation boundaries |
| `docs/checkpoint_inventory.md` | present | Checkpoint-to-method mapping |
| `docs/runtime_environment_report.md` | present | Runtime and toolchain report |
| `docs/submission_readiness_report.md` | present | Current readiness audit |
| `docs/english_manuscript_readiness_audit.md` | present | English manuscript submission-facing audit |

## Internal-Only Project Materials

| Item | Status | Note |
|---|---|---|
| `docs/current_progress_and_next_plan.md` | present | Long-running project log |
| `docs/paper_asset_build_report.md` | present | Local build report |
| `docs/evidence_chain_status.md` | present | Internal evidence tracking |
| `docs/journal_target_shortlist.md` | present | Submission target planning |
| `docs/journal_template_migration_plan.md` | present | Target-template migration planning |
| `docs/lag_jsbsim_migration_probe.md` | present | Future LAG/JSBSim migration readiness probe |
| `docs/lag_role_graph_adapter_test.md` | present | Duck-typed LAG state-to-role-graph adapter test |
| `results/lag_role_graph_adapter_test.csv` | present | LAG adapter tensor-shape and graph-invariant checks |
| `docs/lag_role_graph_wrapper_test.md` | present | Thin reset/step wrapper test for future LAG integration |
| `results/lag_role_graph_wrapper_test.csv` | present | LAG wrapper reset/step graph refresh checks |
| `envs/uav_intercept_3d_env.py` | present | Prototype 3DOF heterogeneous interception environment |
| `scripts/smoke_test_intercept_3d_env.py` | present | 3DOF environment interface smoke test |
| `docs/intercept_3d_smoke_test.md` | present | 3DOF environment smoke-test report |
| `results/intercept_3d_smoke_test.csv` | present | 3DOF environment smoke-test rows |
| `results/visualization_and_intent_diagnostics.md` | present | Internal intent diagnostic notes |
| `docs/lag_migration_checklist.md` | present | Future migration planning |

## Not Ready in Current Runtime

| Item | Status | Note |
|---|---|---|
| `PDF files` | not ready | Not generated in current runtime because xelatex/bibtex are unavailable |
| `Journal-specific template files` | not ready | Target journal has not been selected or adapted yet |
| `Real LAG/JSBSim validation output` | not ready | Blocked by missing JSBSim data/submodule |

## Recommended Submission Packaging Order

1. Choose Chinese or English route.
2. Compile the selected LaTeX project in a machine with `xelatex` and `bibtex`.
3. Inspect generated PDF layout manually.
4. Adapt to the target journal template.
5. Attach only necessary supplemental CSVs/reports if the venue permits supplementary files.
