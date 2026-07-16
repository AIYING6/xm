# Supplemental CSV Schema Audit

Generated: 2026-07-16T21:05:12

Purpose:

```text
Check that supplementary CSV files keep the expected columns, row counts, key value domains, and rate ranges.
This audit complements the quantitative claim checks; it does not rerun experiments.
```

## Summary

```text
csv_files_checked = 32
failures = 0
```

## Rows

| Name | Rows | Columns | Status | Notes |
|---|---:|---:|---|---|
| `final_main_raw` | 36 / 36 | 14 / 14 | ok | Raw final 300-episode rows. |
| `final_main_summary` | 12 / 12 | 12 / 12 | ok | Aggregated final 300-episode rows. |
| `final_main_paired_statistics` | 16 / 16 | 11 / 11 | ok | Seed-paired final descriptive statistics. |
| `comm_dropout_raw` | 54 / 54 | 15 / 15 | ok | Raw communication-dropout diagnostic rows. |
| `comm_dropout_summary` | 18 / 18 | 13 / 13 | ok | Aggregated communication-dropout diagnostic rows. |
| `comm_dropout_paired_statistics` | 24 / 24 | 12 / 12 | ok | Seed-paired dropout descriptive statistics. |
| `aggregate_robustness` | 6 / 6 | 11 / 11 | ok | Cross-condition aggregate robustness summary. |
| `claim_evidence_matrix` | 9 / 9 | 8 / 8 | ok | Generated paper claim-to-evidence matrix. |
| `manuscript_evidence_reference_audit` | 51 / 51 | 7 / 7 | ok | Generated manuscript evidence-reference audit. |
| `bilingual_numeric_consistency_audit` | 47 / 47 | 7 / 7 | ok | Generated bilingual manuscript numeric consistency audit. |
| `latex_reference_integrity_audit` | 86 / 86 | 5 / 5 | ok | Generated bilingual LaTeX label/reference integrity audit. |
| `bilingual_manuscript_completeness_audit` | 36 / 36 | 5 / 5 | ok | Generated bilingual manuscript completeness audit. |
| `submission_action_register` | 10 / 10 | 7 / 7 | ok | Generated submission-facing action item register. |
| `experiment_extension_decision_plan` | 7 / 7 | 10 / 10 | ok | Generated optional next-experiment decision plan. |
| `reproducibility_checksum_manifest` | 184 / 184 | 4 / 4 | ok | Generated stable artifact SHA256/size manifest. |
| `reproducibility_checksum_verification` | 184 / 184 | 8 / 8 | ok | Generated checksum manifest verification rows. |
| `radius_interpolation_raw` | 27 / 27 | 14 / 14 | ok | Raw held-out communication-radius interpolation rows. |
| `radius_interpolation_summary` | 9 / 9 | 12 / 12 | ok | Aggregated held-out communication-radius interpolation rows. |
| `legacy_comm_ablation` | 20 / 20 | 11 / 11 | ok | Legacy 100-episode communication ablation context. |
| `per_seed_appendix` | 36 / 36 | 7 / 7 | ok | Per-seed appendix scatter data. |
| `speed_robustness_raw` | 54 / 54 | 14 / 14 | ok | Raw target-speed robustness rows. |
| `speed_robustness_summary` | 18 / 18 | 13 / 13 | ok | Aggregated target-speed robustness rows. |
| `edge_feature_ablation_raw` | 42 / 42 | 16 / 16 | ok | Raw evaluation-time edge-feature masking rows. |
| `edge_feature_ablation_summary` | 14 / 14 | 14 / 14 | ok | Aggregated evaluation-time edge-feature masking rows. |
| `figure_asset_audit` | 23 / 23 | 8 / 8 | ok | Generated figure technical audit. |
| `evaluation_budget_audit` | 6 / 6 | 10 / 10 | ok | Generated evaluation-budget audit. |
| `method_naming_audit` | 28 / 28 | 6 / 6 | ok | Generated method-name consistency audit. |
| `lag_jsbsim_migration_probe` | 29 / 29 | 4 / 4 | ok | LAG/JSBSim migration-readiness probe. |
| `lag_role_graph_adapter_test` | 26 / 26 | 3 / 3 | ok | LAG-like state-to-role-graph adapter test. |
| `lag_role_graph_wrapper_test` | 11 / 11 | 3 / 3 | ok | LAG-like reset/step graph wrapper test. |
| `intercept_3d_smoke_test` | 15 / 15 | 13 / 13 | ok | 3DOF heterogeneous interception environment smoke test. |
| `intercept_3d_policy_eval` | 3 / 3 | 39 / 39 | ok | 3DOF checkpoint evaluation smoke diagnostic; not a paper learning result. |

## Use Boundary

```text
Passing this audit means the CSV files are structurally consistent with the current paper package.
It does not prove that a diagnostic has the same evidentiary weight as the 300-episode final main evaluation.
```
