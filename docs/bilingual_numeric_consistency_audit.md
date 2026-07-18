# Bilingual Numeric Consistency Audit

Generated: 2026-07-16T22:21:39

Purpose:

```text
Check that key numeric values derived from result CSVs appear in both Chinese and English LaTeX manuscript sources.
This audit catches manual manuscript edits that desynchronize reported numbers from result files.
```

## Summary

```text
numeric_markers_checked = 47
failures = 0
C1 = 9
C2 = 6
C3 = 6
C4 = 9
C5 = 9
C6 = 6
C9 = 2
```

## Rows

| Claim | Source | Value | Status | Notes |
|---|---|---:|---|---|
| C1 | `results/final_comm_300_summary.csv` | 0.926 | ok | EA-RG-MAPPO-S radius 4 success_mean. |
| C1 | `results/final_comm_300_summary.csv` | 0.054 | ok | EA-RG-MAPPO-S radius 4 collision_mean. |
| C1 | `results/final_comm_300_summary.csv` | 0.919 | ok | EA-RG-MAPPO-S radius 6 success_mean. |
| C1 | `results/final_comm_300_summary.csv` | 0.064 | ok | EA-RG-MAPPO-S radius 6 collision_mean. |
| C1 | `results/final_comm_300_summary.csv` | 0.890 | ok | EA-RG-MAPPO-S radius 8 success_mean. |
| C1 | `results/final_comm_300_summary.csv` | 0.083 | ok | EA-RG-MAPPO-S radius 8 collision_mean. |
| C1 | `results/final_comm_300_summary.csv` | 0.879 | ok | EA-RG-MAPPO-S radius 10 success_mean. |
| C1 | `results/final_comm_300_summary.csv` | 0.086 | ok | EA-RG-MAPPO-S radius 10 collision_mean. |
| C1 | `results/final_comm_300_summary.csv` | 0.228 | ok | MAPPO radius 4 collision comparison. |
| C2 | `results/final_300_paired_statistics.csv` | 0.039 | ok | GAT-MAPPO radius 4 collision_reduction CI lower. |
| C2 | `results/final_300_paired_statistics.csv` | 0.123 | ok | GAT-MAPPO radius 4 collision_reduction CI upper. |
| C2 | `results/final_300_paired_statistics.csv` | 0.005 | ok | GAT-MAPPO radius 8 success_gain CI lower. |
| C2 | `results/final_300_paired_statistics.csv` | 0.206 | ok | GAT-MAPPO radius 8 success_gain CI upper. |
| C2 | `results/final_300_paired_statistics.csv` | 0.005 | ok | GAT-MAPPO radius 8 collision_reduction CI lower. |
| C2 | `results/final_300_paired_statistics.csv` | 0.186 | ok | GAT-MAPPO radius 8 collision_reduction CI upper. |
| C3 | `results/comm_dropout_robustness_summary.csv` | 0.047 | ok | EA-RG-MAPPO-S radius 4 dropout 0.50 collision. |
| C3 | `results/comm_dropout_robustness_summary.csv` | 0.300 | ok | MAPPO radius 4 dropout 0.50 collision. |
| C3 | `results/comm_dropout_robustness_summary.csv` | 0.167 | ok | GAT-MAPPO radius 4 dropout 0.50 collision. |
| C3 | `results/comm_dropout_robustness_summary.csv` | 0.053 | ok | EA-RG-MAPPO-S radius 8 dropout 0.50 collision. |
| C3 | `results/comm_dropout_robustness_summary.csv` | 0.293 | ok | MAPPO radius 8 dropout 0.50 collision. |
| C3 | `results/comm_dropout_robustness_summary.csv` | 0.173 | ok | GAT-MAPPO radius 8 dropout 0.50 collision. |
| C4 | `results/aggregate_robustness_summary.csv` | 0.903 | ok | final_cross_radius EA-RG-MAPPO-S mean_success. |
| C4 | `results/aggregate_robustness_summary.csv` | 0.072 | ok | final_cross_radius EA-RG-MAPPO-S mean_collision. |
| C4 | `results/aggregate_robustness_summary.csv` | 0.793 | ok | final_cross_radius EA-RG-MAPPO-S conservative_margin. |
| C4 | `results/aggregate_robustness_summary.csv` | 0.892 | ok | dropout_diagnostic EA-RG-MAPPO-S mean_success. |
| C4 | `results/aggregate_robustness_summary.csv` | 0.070 | ok | dropout_diagnostic EA-RG-MAPPO-S mean_collision. |
| C4 | `results/aggregate_robustness_summary.csv` | 0.747 | ok | dropout_diagnostic EA-RG-MAPPO-S conservative_margin. |
| C4 | `results/aggregate_robustness_summary.csv` | 0.107 | ok | dropout_diagnostic EA-RG-MAPPO-S worst_collision. |
| C4 | `results/aggregate_robustness_summary.csv` | 0.320 | ok | dropout_diagnostic MAPPO worst_collision. |
| C4 | `results/aggregate_robustness_summary.csv` | 0.187 | ok | dropout_diagnostic GAT-MAPPO worst_collision. |
| C5 | `results/radius_interpolation_summary.csv` | 0.067 | ok | EA-RG-MAPPO-S unseen radius 5 collision. |
| C5 | `results/radius_interpolation_summary.csv` | 0.227 | ok | MAPPO unseen radius 5 collision. |
| C5 | `results/radius_interpolation_summary.csv` | 0.113 | ok | GAT-MAPPO unseen radius 5 collision. |
| C5 | `results/radius_interpolation_summary.csv` | 0.100 | ok | EA-RG-MAPPO-S unseen radius 7 collision. |
| C5 | `results/radius_interpolation_summary.csv` | 0.200 | ok | MAPPO unseen radius 7 collision. |
| C5 | `results/radius_interpolation_summary.csv` | 0.140 | ok | GAT-MAPPO unseen radius 7 collision. |
| C5 | `results/radius_interpolation_summary.csv` | 0.067 | ok | EA-RG-MAPPO-S unseen radius 9 collision. |
| C5 | `results/radius_interpolation_summary.csv` | 0.153 | ok | MAPPO unseen radius 9 collision. |
| C5 | `results/radius_interpolation_summary.csv` | 0.173 | ok | GAT-MAPPO unseen radius 9 collision. |
| C6 | `results/speed_robustness_summary.csv` | 0.097 | ok | EA-RG-MAPPO-S radius 4 target_speed 0.90 collision. |
| C6 | `results/speed_robustness_summary.csv` | 0.240 | ok | MAPPO radius 4 target_speed 0.90 collision. |
| C6 | `results/speed_robustness_summary.csv` | 0.237 | ok | GAT-MAPPO radius 4 target_speed 0.90 collision. |
| C6 | `results/speed_robustness_summary.csv` | 0.130 | ok | EA-RG-MAPPO-S radius 8 target_speed 0.90 collision. |
| C6 | `results/speed_robustness_summary.csv` | 0.300 | ok | MAPPO radius 8 target_speed 0.90 collision. |
| C6 | `results/speed_robustness_summary.csv` | 0.203 | ok | GAT-MAPPO radius 8 target_speed 0.90 collision. |
| C9 | `docs/english_experiments_draft.md` | 0.587 | ok | Intent plain accuracy. |
| C9 | `docs/english_experiments_draft.md` | 0.200 | ok | Intent balanced accuracy. |

## Use Boundary

```text
Passing this audit means the selected key numbers are present in both manuscript languages.
It does not replace full proofreading, PDF layout inspection, or journal-specific formatting checks.
```
