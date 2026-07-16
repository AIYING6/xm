# Reproducibility Manifest

Date: 2026-07-13

## 1. Environment

Python environment used in this project:

```text
D:/Anaconda/envs/.conda/envs/cac/python.exe
```

Known runtime:

```text
torch 2.4.1+cu124
CUDA available: True
GPU: NVIDIA GeForce GTX 1650 Ti
```

Project root:

```text
C:/Users/96251/Documents/Codex/2026-07-12/ni/work/ri_gmappo_uav
```

Runtime environment report:

```bash
python scripts/write_runtime_environment_report.py
```

Generated:

```text
docs/runtime_environment_report.md
```

Checkpoint inventory:

```bash
python scripts/write_checkpoint_inventory.py
```

Generated:

```text
docs/checkpoint_inventory.md
```

Submission action register:

```bash
python scripts/write_submission_action_register.py
```

Generated:

```text
docs/submission_action_register.md
results/submission_action_register.csv
```

Current expected shape:

```text
items = 10
blocked = 2
deferred = 1
open = 7
```

Experiment extension decision plan:

```bash
python scripts/write_experiment_extension_decision_plan.py
```

Generated:

```text
docs/experiment_extension_decision_plan.md
results/experiment_extension_decision_plan.csv
```

Current expected shape:

```text
options = 7
blocked = 1
deferred = 3
ready = 3
```

Stable artifact checksum manifest:

```bash
python scripts/write_reproducibility_checksum_manifest.py
```

Checksum manifest verification:

```bash
python scripts/verify_reproducibility_checksum_manifest.py
```

Generated:

```text
docs/reproducibility_checksum_manifest.md
results/reproducibility_checksum_manifest.csv
docs/reproducibility_checksum_verification.md
results/reproducibility_checksum_verification.csv
```

Current expected shape:

```text
artifacts_hashed = 169
artifacts_verified = 169
failures = 0
```

Supplemental data README:

```bash
python scripts/write_supplemental_data_readme.py
```

Generated:

```text
docs/supplemental_data_readme.md
```

LAG/JSBSim migration readiness probe:

```bash
python scripts/probe_lag_jsbsim_migration.py
```

Generated:

```text
docs/lag_jsbsim_migration_probe.md
results/lag_jsbsim_migration_probe.csv
```

LAG state-to-role-graph adapter test:

```bash
python scripts/test_lag_role_graph_adapter.py
```

Generated:

```text
docs/lag_role_graph_adapter_test.md
results/lag_role_graph_adapter_test.csv
```

LAG reset/step role-graph wrapper test:

```bash
python scripts/test_lag_role_graph_wrapper.py
```

Generated:

```text
docs/lag_role_graph_wrapper_test.md
results/lag_role_graph_wrapper_test.csv
```

Submission readiness report:

```bash
python scripts/write_submission_readiness_report.py
```

Generated:

```text
docs/submission_readiness_report.md
```

Submission package manifest:

```bash
python scripts/write_submission_package_manifest.py
```

Generated:

```text
docs/submission_package_manifest.md
```

Claim-to-evidence matrix:

```bash
python scripts/write_claim_evidence_matrix.py
```

Generated:

```text
docs/claim_evidence_matrix.md
results/claim_evidence_matrix.csv
```

Current expected shape:

```text
claims_checked = 9
failures = 0
```

Manuscript evidence-reference audit:

```bash
python scripts/audit_manuscript_evidence_references.py
```

Generated:

```text
docs/manuscript_evidence_reference_audit.md
results/manuscript_evidence_reference_audit.csv
```

Current expected shape:

```text
references_checked = 51
failures = 0
```

Bilingual manuscript numeric consistency audit:

```bash
python scripts/audit_bilingual_numeric_consistency.py
```

Generated:

```text
docs/bilingual_numeric_consistency_audit.md
results/bilingual_numeric_consistency_audit.csv
```

Current expected shape:

```text
numeric_markers_checked = 47
failures = 0
```

LaTeX label/reference integrity audit:

```bash
python scripts/audit_latex_reference_integrity.py
```

Generated:

```text
docs/latex_reference_integrity_audit.md
results/latex_reference_integrity_audit.csv
```

Current expected shape:

```text
reference_checks = 86
failures = 0
```

Bilingual manuscript completeness audit:

```bash
python scripts/audit_bilingual_manuscript_completeness.py
```

Generated:

```text
docs/bilingual_manuscript_completeness_audit.md
results/bilingual_manuscript_completeness_audit.csv
```

Current expected shape:

```text
checks = 36
failures = 0
action_items = 8
```

English manuscript readiness audit:

```bash
python scripts/audit_english_manuscript_readiness.py
```

Generated:

```text
docs/english_manuscript_readiness_audit.md
```

Supplemental CSV schema audit:

```bash
python scripts/audit_supplemental_csv_schema.py
```

Generated:

```text
docs/supplemental_csv_schema_audit.md
results/supplemental_csv_schema_audit.csv
```

Current expected shape:

```text
csv_files_checked = 31
failures = 0
```

Result provenance audit:

```bash
python scripts/audit_result_provenance.py
```

Generated:

```text
docs/result_provenance_audit.md
results/result_provenance_audit.csv
```

Current expected shape:

```text
artifacts_checked = 54
failures = 0
```

## 2. Final Method Naming

Paper name:

```text
EA-RG-MAPPO-S
```

Code/result directory name:

```text
ri_gmappo_edge_stage2_rand_seed*_20
```

Mapping:

| Paper name | Result directory |
|---|---|
| MAPPO | `results/mappo_curriculum_slow_150`, `results/mappo_curriculum_slow_seed1_150`, `results/mappo_curriculum_slow_seed2_150` |
| GAT-MAPPO | `results/gat_mappo_hybrid_slow_60_plus90`, `results/gat_mappo_hybrid_slow_seed1_60_plus90`, `results/gat_mappo_hybrid_slow_seed2_60_plus90` |
| EA-RG-MAPPO-S | `results/ri_gmappo_edge_stage2_rand_seed0_20`, `results/ri_gmappo_edge_stage2_rand_seed1_20`, `results/ri_gmappo_edge_stage2_rand_seed2_20` |

## 3. Final 300-Episode Evaluation

Command:

```bash
python scripts/evaluate_final_comm_300.py --episodes 300 --target-policy mixed --target-speed 0.75 --radii 4 6 8 10 --out-csv results/final_comm_300_eval.csv --summary-csv results/final_comm_300_summary.csv
```

Generated files:

```text
results/final_comm_300_eval.csv
results/final_comm_300_summary.csv
results/final_300_eval_notes.md
```

Final LaTeX table:

```text
results/latex_final_comm_300_table.tex
```

Seed-paired descriptive confidence intervals:

```bash
python scripts/analyze_final_300_statistics.py
```

Generated files:

```text
results/final_300_paired_statistics.csv
results/final_300_paired_statistics.md
results/latex_final_300_paired_ci_table.tex
```

Communication-dropout robustness diagnostic:

```bash
python scripts/evaluate_comm_dropout_robustness.py --episodes 50 --target-policy mixed --target-speed 0.75 --radii 4 8 --dropout-probs 0 0.25 0.5
```

Generated files:

```text
results/comm_dropout_robustness_eval.csv
results/comm_dropout_robustness_summary.csv
results/comm_dropout_robustness_notes.md
results/latex_comm_dropout_robustness_table.tex
```

Communication-dropout paired descriptive statistics:

```bash
python scripts/analyze_comm_dropout_statistics.py
```

Generated files:

```text
results/comm_dropout_paired_statistics.csv
results/comm_dropout_paired_statistics.md
results/latex_comm_dropout_paired_ci_table.tex
```

Aggregate robustness summary:

```bash
python scripts/analyze_aggregate_robustness.py
```

Generated files:

```text
results/aggregate_robustness_summary.csv
results/aggregate_robustness_summary.md
results/latex_aggregate_robustness_table.tex
```

Communication-radius interpolation diagnostic:

```bash
python scripts/evaluate_radius_interpolation.py --episodes 50 --radii 5 7 9 --resume
```

Generated files:

```text
results/radius_interpolation_eval.csv
results/radius_interpolation_summary.csv
results/radius_interpolation_notes.md
results/latex_radius_interpolation_table.tex
```

Figure asset audit:

```bash
python scripts/audit_figure_assets.py
```

Generated files:

```text
results/figure_asset_audit.csv
docs/figure_asset_audit.md
```

Evaluation budget consistency audit:

```bash
python scripts/audit_evaluation_budget_consistency.py
```

Generated files:

```text
results/evaluation_budget_audit.csv
docs/evaluation_budget_audit.md
```

Method naming consistency audit:

```bash
python scripts/audit_method_naming_consistency.py
```

Generated files:

```text
results/method_naming_audit.csv
docs/method_naming_audit.md
```

Communication-dropout diagnostic figures:

```bash
python scripts/plot_comm_dropout_robustness.py
```

Generated files:

```text
results/figures/comm_dropout_success_rate.png
results/figures/comm_dropout_collision_rate.png
```

## 4. Ablation Evaluation

Ablation source table:

```text
results/paper_comm_results.csv
```

Generated LaTeX ablation table:

```text
results/latex_ablation_comm_table.tex
```

Interpretation:

```text
The ablation table is 100 episodes per seed.
The final main table is 300 episodes per seed.
Do not merge them into one table without clearly marking evaluation episodes.
```

## 5. Table Generation

Command:

```bash
python scripts/make_latex_tables.py
```

Generated files:

```text
results/latex_main_comm_table.tex
results/latex_ablation_comm_table.tex
results/latex_final_comm_300_table.tex
results/latex_speed_robustness_table.tex
results/latex_edge_feature_ablation_table.tex
results/latex_training_settings_table.tex
```

Training settings summarized in the LaTeX table:

```text
num_envs=8
rollout_steps=128
hidden_dim=128
lr=3e-4
gamma=0.99
gae_lambda=0.95
clip_coef=0.2
entropy_coef=0.01
value_coef=0.5
max_grad_norm=0.5
ppo_epochs=4
MAPPO minibatch_size=512
GAT/EA-RG graph minibatch=256
fixed training radius=8
staged fine-tuning radius=U(4,10)
final evaluation=300 episodes per seed, 3 seeds
```

## 6. Figure Generation

Final 300-episode main figures:

```bash
python scripts/plot_final_300_results.py
```

Generated:

```text
results/figures/final_300_success_rate.png
results/figures/final_300_collision_rate.png
```

Full 100-episode ablation figures:

```bash
python scripts/plot_comm_results.py
```

Generated:

```text
results/figures/comm_success_rate.png
results/figures/comm_collision_rate.png
```

Per-seed appendix and scatter:

```bash
python scripts/build_paper_appendix.py
```

Generated:

```text
results/per_seed_comm_appendix.csv
results/per_seed_comm_appendix.md
results/figures/per_seed_success_scatter.png
results/figures/per_seed_collision_scatter.png
```

Qualitative figures:

```bash
python scripts/plot_trajectory_cases.py --radius 4 --search-episodes 120 --out-png results/figures/trajectory_ri_advantage_r4.png
python scripts/plot_trajectory_cases.py --radius 10 --search-episodes 120 --out-png results/figures/trajectory_ri_advantage_r10.png
python scripts/plot_ri_attention_heatmap.py --radius 4 --out-png results/figures/ri_attention_heatmap_r4.png --out-csv results/ri_attention_heatmap_r4.csv
python scripts/plot_ri_attention_heatmap.py --radius 10 --out-png results/figures/ri_attention_heatmap_r10.png --out-csv results/ri_attention_heatmap_r10.csv
```

Intent diagnostic:

```bash
python scripts/plot_intent_confusion.py --episodes 100 --communication-radius 8 --out-png results/figures/intent_confusion_ri_staged_r8.png --out-csv results/intent_confusion_ri_staged_r8.csv
```

## 6.1 Lightweight Paper Asset Build

One-command non-training rebuild and validation:

```bash
python scripts/build_paper_assets.py
```

Generated report:

```text
docs/paper_asset_build_report.md
```

Current result:

```text
LaTeX tables: OK
Final 300 figures: OK
Communication ablation figures: OK
Per-seed appendix: OK
Edge feature ablation figure: OK
Speed robustness figures: OK
LAG graph synthetic smoke: OK
LaTeX static check: OK
Quantitative claim consistency: OK
Paper text risk audit: OK
Reproducibility artifact gate: OK
```

## 7. Paper Draft

Markdown manuscript:

```text
docs/paper_manuscript_zh_v1.md
docs/english_abstract_and_contributions.md
docs/english_introduction_draft.md
docs/english_related_work_draft.md
docs/english_problem_method_draft.md
docs/english_experiments_draft.md
docs/english_discussion_conclusion_draft.md
docs/english_manuscript_draft.md
```

LaTeX project:

```text
paper_latex/main.tex
paper_latex/sections/
paper_latex/references.bib
paper_latex/sections/08_appendix_experiments.tex
paper_latex_en/main.tex
paper_latex_en/sections/
```

Static check:

```bash
python scripts/check_latex_project.py
```

Current result:

```text
checked tex files: 28
bib keys: 14
OK
```

Quantitative claim consistency:

```bash
python scripts/check_paper_claim_consistency.py
```

Current result:

```text
claim groups checked: final_main, speed_robustness, edge_masking
OK
```

English LaTeX consistency:

```bash
python scripts/check_english_latex_consistency.py
```

Current result:

```text
english latex files checked: 9
required markers checked: 16
OK
```

Paper text risk audit:

```bash
python scripts/check_paper_text_risk.py
```

Current result:

```text
text risk files checked: 30
OK
```

PDF rendering:

```text
Not verified in current Codex runtime because xelatex is not on PATH.
```

## 8. Final Main Result

Use this as the main claim table:

```text
results/latex_final_comm_300_table.tex
```

Key values:

| Radius | EA-RG-MAPPO-S Success | EA-RG-MAPPO-S Collision |
|---:|---:|---:|
| 4 | 0.926 ± 0.004 | 0.054 ± 0.007 |
| 6 | 0.919 ± 0.012 | 0.064 ± 0.006 |
| 8 | 0.890 ± 0.021 | 0.083 ± 0.012 |
| 10 | 0.879 ± 0.017 | 0.086 ± 0.020 |

## 9. Do Not Overclaim

Supported:

```text
EA-RG-MAPPO-S improves limited-communication stability and reduces collision in the simplified 2D UAV pursuit environment.
```

Not supported yet:

```text
High-accuracy target intent recognition.
Full 6DOF air combat with missile/radar/human-UAV teaming.
```

## 10. LAG/JSBSim Migration Smoke Test

Synthetic graph-construction smoke test:

```bash
python scripts/lag_graph_smoke_test.py --mode synthetic --steps 100
```

Generated:

```text
results/lag_graph_smoke_stats.csv
```

Current result:

```text
wrote 400 rows to results/lag_graph_smoke_stats.csv
nan_count=0, inf_count=0
```

Real LAG mode:

```bash
python scripts/lag_graph_smoke_test.py --mode lag --steps 1 --out-csv results/lag_graph_smoke_stats_real.csv
```

Current blocker:

```text
The cac environment can import jsbsim 1.1.6, but the copied LAG tree is missing work/LAG/envs/JSBSim/data.
Complete the JSBSim data/submodule before running real LAG smoke tests.
```

## 11. Edge Feature Evaluation-Time Ablation

Command:

```bash
python scripts/evaluate_edge_feature_ablation.py --episodes 30 --radii 4 8 --out-csv results/edge_feature_ablation_eval.csv --summary-csv results/edge_feature_ablation_summary.csv --notes-md results/edge_feature_ablation_notes.md
```

Generated:

```text
results/edge_feature_ablation_eval.csv
results/edge_feature_ablation_summary.csv
results/edge_feature_ablation_notes.md
results/figures/edge_feature_ablation_delta.png
```

Plot command:

```bash
python scripts/plot_edge_feature_ablation.py
```

Expected rows:

```text
results/edge_feature_ablation_eval.csv: 42 rows
results/edge_feature_ablation_summary.csv: 14 rows
```

Interpretation boundary:

```text
This is an evaluation-time masking diagnostic, not a retrained structural ablation.
Use it only as mechanism-analysis evidence; keep the training-time ablation table as the primary ablation result.
```

## 12. Target Speed Robustness Evaluation

Command:

```bash
python scripts/evaluate_speed_robustness.py --episodes 100 --radii 4 8 --target-speeds 0.60 0.75 0.90 --out-csv results/speed_robustness_eval.csv --summary-csv results/speed_robustness_summary.csv --notes-md results/speed_robustness_notes.md
```

Generated:

```text
results/speed_robustness_eval.csv
results/speed_robustness_summary.csv
results/speed_robustness_notes.md
```

Expected rows:

```text
results/speed_robustness_eval.csv: 54 rows
results/speed_robustness_summary.csv: 18 rows
```

Plot command:

```bash
python scripts/plot_speed_robustness.py
```

Generated figures:

```text
results/figures/speed_robustness_success_r4.png
results/figures/speed_robustness_collision_r4.png
results/figures/speed_robustness_success_r8.png
results/figures/speed_robustness_collision_r8.png
```

Interpretation boundary:

```text
This is a 100-episode robustness appendix, not the 300-episode main table.
Use it to support target-speed robustness and low-collision behavior under stronger target motion.
```

## 13. Claim Consistency Gate

The reproducibility gate now calls:

```text
scripts/check_paper_claim_consistency.py
```

It verifies:

```text
1. Final main table: EA-RG-MAPPO-S keeps collision below 0.10 and below MAPPO/GAT-MAPPO at radii 4/6/8/10.
2. Speed robustness appendix: EA-RG-MAPPO-S keeps lower collision than MAPPO/GAT-MAPPO at target_speed=0.90 for radii 4 and 8.
3. Edge masking diagnostic: comm/target feature masking consistently reduces success and increases collision, while full edge masking remains weak-sensitivity rather than catastrophic degradation.
```

The reproducibility gate also calls:

```text
scripts/check_paper_text_risk.py
```

It verifies that publishable LaTeX/Markdown text does not contain stale RI-GMAPPO-route claims or positive overclaims such as verified full 6DOF combat, high-accuracy intent recognition, or comprehensive superiority without a negation/limitation context.

The lightweight build also regenerates and checks:

```text
scripts/audit_result_provenance.py
scripts/audit_supplemental_csv_schema.py
```

These verify that publishable tables, figures, reports, and audits have traceable source-data/generator-script records, and that supplementary CSV files keep expected columns, row counts, key value domains, and rate ranges.
