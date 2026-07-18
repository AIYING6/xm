# Supplemental Data README

Generated: 2026-07-16T22:22:50

Purpose:

```text
Describe the CSV files that may be included as supplementary evidence for EA-RG-MAPPO-S.
The main claim should rely on the 300-episode final evaluation; lower-budget files are appendix or diagnostic evidence.
```

## Data Inventory

| File | Rows | Role | Budget | Paper Use |
|---|---:|---|---|---|
| `results/final_comm_300_eval.csv` | 36 | Raw final main evaluation rows. | 300 episodes per seed. | Main-result evidence. |
| `results/final_comm_300_summary.csv` | 12 | Aggregated final main evaluation summary. | 300 episodes per seed. | Main table and main figures. |
| `results/final_300_paired_statistics.csv` | 16 | Seed-paired descriptive confidence intervals. | Three paired seeds. | Statistical appendix table. |
| `results/comm_dropout_robustness_eval.csv` | 54 | Raw communication-dropout robustness diagnostic rows. | 50 episodes per seed. | Appendix robustness diagnostic. |
| `results/comm_dropout_robustness_summary.csv` | 18 | Aggregated communication-dropout robustness diagnostic. | 50 episodes per seed. | Appendix dropout table and figures. |
| `results/comm_dropout_paired_statistics.csv` | 24 | Seed-paired dropout descriptive statistics. | Three paired seeds. | Appendix dropout confidence-interval table. |
| `results/aggregate_robustness_summary.csv` | 6 | Cross-condition aggregate robustness summary. | Aggregates existing diagnostics. | Appendix robustness synthesis. |
| `results/claim_evidence_matrix.csv` | 9 | Paper claim-to-evidence matrix. | Generated evidence audit. | Binds manuscript claims to files, values, and wording boundaries. |
| `results/manuscript_evidence_reference_audit.csv` | 51 | Manuscript evidence-reference audit. | Generated manuscript audit. | Checks that Chinese and English LaTeX cite required evidence markers. |
| `results/bilingual_numeric_consistency_audit.csv` | 47 | Bilingual numeric consistency audit. | Generated manuscript audit. | Checks key values against Chinese and English LaTeX sources. |
| `results/latex_reference_integrity_audit.csv` | 86 | LaTeX label/reference integrity audit. | Generated manuscript audit. | Checks key table/figure labels and references in Chinese and English LaTeX. |
| `results/bilingual_manuscript_completeness_audit.csv` | 36 | Bilingual manuscript completeness audit. | Generated manuscript audit. | Checks structure, counts, markers, and submission action items. |
| `results/submission_action_register.csv` | 10 | Submission action register. | Generated submission planning artifact. | Tracks open, blocked, and deferred tasks before actual journal submission. |
| `results/experiment_extension_decision_plan.csv` | 7 | Experiment extension decision plan. | Generated planning artifact. | Prioritizes optional next experiments and future-system extensions. |
| `results/reproducibility_checksum_manifest.csv` | 184 | Stable artifact checksum manifest. | Generated reproducibility artifact. | Records SHA256 and file sizes for stable package files. |
| `results/reproducibility_checksum_verification.csv` | 184 | Checksum manifest verification rows. | Generated reproducibility artifact. | Verifies stable package files against recorded SHA256 and file sizes. |
| `results/radius_interpolation_eval.csv` | 27 | Raw held-out communication-radius interpolation rows. | 50 episodes per seed. | Appendix interpolation diagnostic. |
| `results/radius_interpolation_summary.csv` | 9 | Held-out communication-radius interpolation summary. | 50 episodes per seed. | Appendix interpolation table and figures. |
| `results/paper_comm_results.csv` | 20 | Legacy 100-episode communication-radius ablation summary. | 100 episodes per seed. | Appendix/training-time ablation context. |
| `results/per_seed_comm_appendix.csv` | 36 | Per-seed appendix rows for baseline comparison. | 100 episodes per seed. | Seed-variation scatter plots. |
| `results/speed_robustness_eval.csv` | 54 | Raw target-speed robustness rows. | 100 episodes per seed. | Appendix target-speed diagnostic. |
| `results/speed_robustness_summary.csv` | 18 | Target-speed robustness summary. | 100 episodes per seed. | Appendix robustness table and figures. |
| `results/edge_feature_ablation_eval.csv` | 42 | Raw evaluation-time edge-feature masking rows. | 30 episodes per seed. | Mechanism diagnostic only. |
| `results/edge_feature_ablation_summary.csv` | 14 | Edge-feature masking summary. | 30 episodes per seed. | Mechanism diagnostic table and figure. |
| `results/figure_asset_audit.csv` | 27 | Generated figure-asset quality checks. | Asset audit. | Technical reproducibility audit. |
| `results/evaluation_budget_audit.csv` | 6 | Episode-budget consistency checks. | Asset audit. | Prevents mixing main and appendix budgets. |
| `results/method_naming_audit.csv` | 28 | Method-name consistency checks. | Asset audit. | Prevents stale method names in publishable text. |
| `results/supplemental_csv_schema_audit.csv` | 32 | Supplemental CSV schema checks. | Asset audit. | Prevents schema, row-count, and key-domain drift. |
| `results/result_provenance_audit.csv` | 56 | Result artifact provenance checks. | Asset audit. | Maps tables/figures/reports to source data and scripts. |
| `results/lag_jsbsim_migration_probe.csv` | 29 | LAG/JSBSim migration-readiness probe. | Interface diagnostic. | Future extension evidence, not main validation. |
| `results/lag_role_graph_adapter_test.csv` | 26 | LAG-like role-graph adapter checks. | Interface diagnostic. | Future 6DOF migration evidence. |
| `results/lag_role_graph_wrapper_test.csv` | 11 | LAG-like reset/step graph wrapper checks. | Interface diagnostic. | Future 6DOF migration evidence. |
| `results/intercept_3d_smoke_test.csv` | 15 | 3DOF heterogeneous interception environment smoke test. | Environment interface diagnostic. | Next-stage 3DOF migration evidence, not a learning result. |
| `results/intercept_3d_policy_eval.csv` | 3 | 3DOF EA-RG-MAPPO-S checkpoint evaluation rows. | 3-episode smoke diagnostic. | Checkpoint-loading and metric-schema evidence, not a learning result. |

## Interpretation Boundary

```text
Use final_comm_300_summary.csv as the primary quantitative basis.
Use dropout, radius-interpolation, speed, and edge-feature files as appendix diagnostics.
Use LAG/JSBSim files only as migration-readiness evidence until real JSBSim data are restored and evaluated.
Do not use intent diagnostic files as primary contribution evidence.
```
