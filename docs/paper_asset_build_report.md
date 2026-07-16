# Paper Asset Build Report

Generated: 2026-07-16T21:05:14

Purpose:

```text
Regenerate paper tables/figures from existing result files and run non-training validation gates.
This script does not retrain policies or rerun long evaluation jobs.
```

## Summary

| Step | Status |
|---|---|
| Runtime environment report | OK |
| Checkpoint inventory | OK |
| Submission action register | OK |
| Experiment extension decision plan | OK |
| Supplemental data README | OK |
| Submission readiness report | OK |
| Submission package manifest | OK |
| English manuscript readiness audit | OK |
| Bilingual manuscript completeness audit | OK |
| Final 300 paired statistics | OK |
| Communication dropout paired statistics | OK |
| Aggregate robustness summary | OK |
| Claim evidence matrix | OK |
| Manuscript evidence reference audit | OK |
| Bilingual numeric consistency audit | OK |
| LaTeX reference integrity audit | OK |
| LaTeX tables | OK |
| Final 300 figures | OK |
| Communication ablation figures | OK |
| Per-seed appendix | OK |
| Edge feature ablation figure | OK |
| Speed robustness figures | OK |
| Communication dropout figures | OK |
| Radius interpolation figures | OK |
| Figure asset audit | OK |
| Evaluation budget audit | OK |
| Method naming audit | OK |
| LAG graph synthetic smoke | OK |
| LAG JSBSim migration probe | OK |
| LAG role graph adapter test | OK |
| LAG role graph wrapper test | OK |
| 3DOF interception environment smoke | OK |
| 3DOF RI-GMAPPO checkpoint evaluation | OK |
| 3DOF paper-facing main table | OK |
| 3DOF relay-failure case candidates | OK |
| 3DOF relay-failure case replay | OK |
| 3DOF task-support ablation pilot summary | OK |
| 3DOF formal task-support ablation summary | OK |
| 3DOF formal role-pair gate ablation summary | OK |
| Reproducibility checksum manifest | OK |
| Reproducibility checksum verification | OK |
| Supplemental CSV schema audit | OK |
| Result provenance audit | OK |
| Submission package manifest refresh | OK |
| Supplemental data README refresh | OK |
| LaTeX static check | OK |
| Quantitative claim consistency | OK |
| English LaTeX consistency | OK |
| Paper text risk audit | OK |
| Reproducibility artifact gate | OK |

## Step Details

### Runtime environment report

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/write_runtime_environment_report.py
```

stdout:

```text
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\docs\runtime_environment_report.md
```

### Checkpoint inventory

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/write_checkpoint_inventory.py
```

stdout:

```text
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\docs\checkpoint_inventory.md
```

### Submission action register

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/write_submission_action_register.py
```

stdout:

```text
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\submission_action_register.csv
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\docs\submission_action_register.md
items: 10
blocked: 2
deferred: 1
open: 7
```

### Experiment extension decision plan

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/write_experiment_extension_decision_plan.py
```

stdout:

```text
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\experiment_extension_decision_plan.csv
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\docs\experiment_extension_decision_plan.md
options: 7
blocked: 1
deferred: 3
ready: 3
```

### Supplemental data README

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/write_supplemental_data_readme.py
```

stdout:

```text
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\docs\supplemental_data_readme.md
```

### Submission readiness report

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/write_submission_readiness_report.py
```

stdout:

```text
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\docs\submission_readiness_report.md
```

### Submission package manifest

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/write_submission_package_manifest.py
```

stdout:

```text
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\docs\submission_package_manifest.md
```

### English manuscript readiness audit

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/audit_english_manuscript_readiness.py
```

stdout:

```text
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\docs\english_manuscript_readiness_audit.md
```

### Bilingual manuscript completeness audit

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/audit_bilingual_manuscript_completeness.py
```

stdout:

```text
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\bilingual_manuscript_completeness_audit.csv
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\docs\bilingual_manuscript_completeness_audit.md
checks: 36
failures: 0
action items: 8
```

### Final 300 paired statistics

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/analyze_final_300_statistics.py
```

stdout:

```text
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\final_300_paired_statistics.csv
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\final_300_paired_statistics.md
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\latex_final_300_paired_ci_table.tex
```

### Communication dropout paired statistics

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/analyze_comm_dropout_statistics.py
```

stdout:

```text
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\comm_dropout_paired_statistics.csv
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\comm_dropout_paired_statistics.md
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\latex_comm_dropout_paired_ci_table.tex
```

### Aggregate robustness summary

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/analyze_aggregate_robustness.py
```

stdout:

```text
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\aggregate_robustness_summary.csv
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\aggregate_robustness_summary.md
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\latex_aggregate_robustness_table.tex
```

### Claim evidence matrix

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/write_claim_evidence_matrix.py
```

stdout:

```text
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\claim_evidence_matrix.csv
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\docs\claim_evidence_matrix.md
claims checked: 9
failures: 0
```

### Manuscript evidence reference audit

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/audit_manuscript_evidence_references.py
```

stdout:

```text
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\manuscript_evidence_reference_audit.csv
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\docs\manuscript_evidence_reference_audit.md
references checked: 51
failures: 0
```

### Bilingual numeric consistency audit

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/audit_bilingual_numeric_consistency.py
```

stdout:

```text
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\bilingual_numeric_consistency_audit.csv
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\docs\bilingual_numeric_consistency_audit.md
numeric markers checked: 47
failures: 0
```

### LaTeX reference integrity audit

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/audit_latex_reference_integrity.py
```

stdout:

```text
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\latex_reference_integrity_audit.csv
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\docs\latex_reference_integrity_audit.md
reference checks: 86
failures: 0
```

### LaTeX tables

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/make_latex_tables.py
```

stdout:

```text
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\latex_main_comm_table.tex
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\latex_ablation_comm_table.tex
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\latex_final_comm_300_table.tex
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\latex_speed_robustness_table.tex
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\latex_edge_feature_ablation_table.tex
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\latex_training_settings_table.tex
```

### Final 300 figures

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/plot_final_300_results.py
```

stdout:

```text
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\figures\final_300_success_rate.png
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\figures\final_300_collision_rate.png
```

### Communication ablation figures

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/plot_comm_results.py
```

stdout:

```text
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\figures\comm_success_rate.png
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\figures\comm_collision_rate.png
```

### Per-seed appendix

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/build_paper_appendix.py
```

stdout:

```text
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\per_seed_comm_appendix.csv
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\per_seed_comm_appendix.md
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\figures\per_seed_success_scatter.png
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\figures\per_seed_collision_scatter.png
```

### Edge feature ablation figure

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/plot_edge_feature_ablation.py
```

stdout:

```text
saved: results\figures\edge_feature_ablation_delta.png
```

### Speed robustness figures

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/plot_speed_robustness.py
```

stdout:

```text
results\figures\speed_robustness_success_r4.png
results\figures\speed_robustness_collision_r4.png
results\figures\speed_robustness_success_r8.png
results\figures\speed_robustness_collision_r8.png
```

### Communication dropout figures

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/plot_comm_dropout_robustness.py
```

stdout:

```text
results\figures\comm_dropout_success_rate.png
results\figures\comm_dropout_collision_rate.png
```

### Radius interpolation figures

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/plot_radius_interpolation.py
```

stdout:

```text
results\figures\radius_interpolation_success_rate.png
results\figures\radius_interpolation_collision_rate.png
```

### Figure asset audit

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/audit_figure_assets.py
```

stdout:

```text
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\figure_asset_audit.csv
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\docs\figure_asset_audit.md
figures checked: 23
warnings: 0
```

### Evaluation budget audit

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/audit_evaluation_budget_consistency.py
```

stdout:

```text
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\evaluation_budget_audit.csv
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\docs\evaluation_budget_audit.md
budget groups checked: 6
failures: 0
```

### Method naming audit

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/audit_method_naming_consistency.py
```

stdout:

```text
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\method_naming_audit.csv
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\docs\method_naming_audit.md
naming rows checked: 28
failures: 0
```

### LAG graph synthetic smoke

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/lag_graph_smoke_test.py --mode synthetic --steps 100
```

stdout:

```text
wrote 400 rows to C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\lag_graph_smoke_stats.csv
nan_count=0, inf_count=0
```

### LAG JSBSim migration probe

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/probe_lag_jsbsim_migration.py
```

stdout:

```text
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\docs\lag_jsbsim_migration_probe.md
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\lag_jsbsim_migration_probe.csv
```

### LAG role graph adapter test

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/test_lag_role_graph_adapter.py
```

stdout:

```text
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\docs\lag_role_graph_adapter_test.md
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\lag_role_graph_adapter_test.csv
```

### LAG role graph wrapper test

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/test_lag_role_graph_wrapper.py
```

stdout:

```text
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\docs\lag_role_graph_wrapper_test.md
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\lag_role_graph_wrapper_test.csv
```

### 3DOF interception environment smoke

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/smoke_test_intercept_3d_env.py
```

stdout:

```text
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\intercept_3d_smoke_test.csv
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\docs\intercept_3d_smoke_test.md
episodes: 15
```

### 3DOF RI-GMAPPO checkpoint evaluation

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/evaluate_ri_gmappo_3d.py
```

stdout:

```text
loaded 30 matching tensors and 0 partial tensors from C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\ri_gmappo_3d_smoke\actor_critic_latest.pt; skipped 0
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\intercept_3d_policy_eval.csv
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\docs\intercept_3d_policy_eval.md
episodes: 3
```

### 3DOF paper-facing main table

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/build_3d_paper_tables.py
```

stdout:

```text
Wrote C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\intercept_3d_paper_main_table.csv
Wrote C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\docs\intercept_3d_paper_main_table.md
Wrote C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\docs\intercept_3d_paper_main_table.tex
```

### 3DOF relay-failure case candidates

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/find_3d_relay_failure_case_candidates.py
```

stdout:

```text
Wrote C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\intercept_3d_relay_failure_case_candidates.csv
Wrote C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\docs\intercept_3d_relay_failure_case_candidates.md
```

### 3DOF relay-failure case replay

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/replay_3d_relay_failure_case.py
```

stdout:

```text
loaded 30 matching tensors and 0 partial tensors from C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\intercept_3d_node_failure_curriculum_pilot_seed0\runs\single\bc_ppo_seed0\actor_critic_best.pt; skipped 0
loaded 70 matching tensors and 0 partial tensors from C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\intercept_3d_node_failure_curriculum_pilot_seed0\runs\multi_relation\bc_ppo_seed0\actor_critic_best.pt; skipped 0
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\intercept_3d_relay_failure_case_replay.csv
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\docs\intercept_3d_relay_failure_case_replay.md
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\figures\intercept_3d_relay_failure_case_replay.png
```

### 3DOF task-support ablation pilot summary

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/analyze_3d_task_support_ablation_pilot.py
```

stdout:

```text
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\intercept_3d_task_support_ablation_seed0_pilot_summary.csv
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\docs\intercept_3d_task_support_ablation_seed0_pilot_summary.md
```

### 3DOF formal task-support ablation summary

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/analyze_3d_task_support_ablation_formal.py
```

stdout:

```text
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\intercept_3d_task_support_ablation_formal_summary.csv
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\docs\intercept_3d_task_support_ablation_formal_summary.md
```

### 3DOF formal role-pair gate ablation summary

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/analyze_3d_role_pair_gate_ablation_formal.py
```

stdout:

```text
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\intercept_3d_role_pair_gate_ablation_formal_scale_matched_summary.csv
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\docs\intercept_3d_role_pair_gate_ablation_formal_scale_matched_summary.md
```

### Reproducibility checksum manifest

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/write_reproducibility_checksum_manifest.py
```

stdout:

```text
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\reproducibility_checksum_manifest.csv
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\docs\reproducibility_checksum_manifest.md
artifacts hashed: 184
```

### Reproducibility checksum verification

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/verify_reproducibility_checksum_manifest.py
```

stdout:

```text
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\reproducibility_checksum_verification.csv
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\docs\reproducibility_checksum_verification.md
artifacts verified: 184
failures: 0
```

### Supplemental CSV schema audit

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/audit_supplemental_csv_schema.py
```

stdout:

```text
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\supplemental_csv_schema_audit.csv
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\docs\supplemental_csv_schema_audit.md
csv files checked: 32
failures: 0
```

### Result provenance audit

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/audit_result_provenance.py
```

stdout:

```text
artifacts checked: 56
failures: 0
OK
```

### Submission package manifest refresh

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/write_submission_package_manifest.py
```

stdout:

```text
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\docs\submission_package_manifest.md
```

### Supplemental data README refresh

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/write_supplemental_data_readme.py
```

stdout:

```text
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\docs\supplemental_data_readme.md
```

### LaTeX static check

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/check_latex_project.py
```

stdout:

```text
checked tex files: 38
bib keys: 14, 14
OK
```

### Quantitative claim consistency

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/check_paper_claim_consistency.py
```

stdout:

```text
claim groups checked: final_main, speed_robustness, edge_masking, paired_ci, comm_dropout, aggregate_robustness, radius_interpolation
OK
```

### English LaTeX consistency

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/check_english_latex_consistency.py
```

stdout:

```text
english latex files checked: 9
required markers checked: 17
OK
```

### Paper text risk audit

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/check_paper_text_risk.py
```

stdout:

```text
text risk files checked: 30
OK
```

### Reproducibility artifact gate

Status: `OK`

Command:

```text
D:\Anaconda\envs\.conda\envs\cac\python.exe scripts/check_reproducibility_artifacts.py
```

stdout:

```text
required files checked: 144
required scripts checked: 50
OK
```
