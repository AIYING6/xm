# Figure Asset Audit

Generated: 2026-07-16T21:04:38

Purpose:

```text
Check paper figure assets for missing, tiny, or near-blank PNG outputs.
This is a technical asset audit, not a visual-design or scientific-content review.
```

## Summary

| Item | Value |
|---|---:|
| PNG figures checked | 23 |
| Warnings | 0 |

## Audit Rows

| Figure | Size | File KB | Gray std | Unique colors | Status | Notes |
|---|---:|---:|---:|---:|---|---|
| `results/figures/comm_collision_rate.png` | 1120x672 | 57.8 | 35.6 | 1185 | ok | ok |
| `results/figures/comm_dropout_collision_rate.png` | 1406x826 | 81.4 | 36.6 | 963 | ok | ok |
| `results/figures/comm_dropout_success_rate.png` | 1406x826 | 85.0 | 36.8 | 1018 | ok | ok |
| `results/figures/comm_success_rate.png` | 1120x672 | 59.7 | 36.1 | 1174 | ok | ok |
| `results/figures/edge_feature_ablation_delta.png` | 2396x951 | 110.4 | 47.4 | 284 | ok | ok |
| `results/figures/final_300_collision_rate.png` | 1296x774 | 50.1 | 32.8 | 705 | ok | ok |
| `results/figures/final_300_success_rate.png` | 1296x774 | 53.9 | 33.3 | 643 | ok | ok |
| `results/figures/intent_confusion_ri_balanced_seed1_r8.png` | 1116x936 | 84.2 | 46.5 | 819 | ok | ok |
| `results/figures/intent_confusion_ri_staged_r8.png` | 1116x936 | 73.9 | 68.5 | 609 | ok | ok |
| `results/figures/intercept_3d_relay_failure_case_replay.png` | 1890x1224 | 199.7 | 36.0 | 777 | ok | ok |
| `results/figures/method_overview_ea_rg_mappo_s.png` | 2500x1440 | 233.6 | 38.6 | 825 | ok | ok |
| `results/figures/per_seed_collision_scatter.png` | 1296x827 | 76.8 | 32.8 | 776 | ok | ok |
| `results/figures/per_seed_success_scatter.png` | 1296x827 | 73.0 | 31.9 | 766 | ok | ok |
| `results/figures/radius_interpolation_collision_rate.png` | 1292x778 | 53.3 | 34.0 | 730 | ok | ok |
| `results/figures/radius_interpolation_success_rate.png` | 1292x778 | 54.5 | 34.0 | 689 | ok | ok |
| `results/figures/ri_attention_heatmap_r10.png` | 936x864 | 56.5 | 75.7 | 838 | ok | ok |
| `results/figures/ri_attention_heatmap_r4.png` | 936x864 | 56.8 | 88.6 | 807 | ok | ok |
| `results/figures/speed_robustness_collision_r4.png` | 1292x778 | 63.2 | 36.7 | 660 | ok | ok |
| `results/figures/speed_robustness_collision_r8.png` | 1292x778 | 66.5 | 36.6 | 774 | ok | ok |
| `results/figures/speed_robustness_success_r4.png` | 1292x778 | 71.0 | 37.0 | 775 | ok | ok |
| `results/figures/speed_robustness_success_r8.png` | 1292x778 | 74.2 | 36.5 | 784 | ok | ok |
| `results/figures/trajectory_ri_advantage_r10.png` | 2808x900 | 120.6 | 33.7 | 472 | ok | ok |
| `results/figures/trajectory_ri_advantage_r4.png` | 2808x900 | 115.3 | 33.5 | 479 | ok | ok |

## Thresholds

```text
warning if width < 900 or height < 500
warning if file size < 10 KB
warning if grayscale standard deviation < 8
warning if sampled unique RGB colors < 32
```
