# 3DOF Topology Curriculum Formal Summary

Generated: 2026-07-16T12:51:13

Inputs:

```text
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\intercept_3d_node_failure_curriculum_formal_node_failure_eval\episode_metrics.csv
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\intercept_3d_node_failure_curriculum_formal_selected_eval\episode_metrics.csv
```

## Multi-Relation Minus Single-Graph

| Scenario | Seeds | Pairs | Success Delta | Success 95% CI | p_boot | Timeout Delta | Steps Delta | Tracking Delta |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| delay_2 | 3 | 90 | +0.022 | [-0.033, +0.078] | 0.542 | -0.022 | -4.5 | +0.009 |
| dropout_030 | 3 | 90 | +0.033 | [-0.022, +0.089] | 0.342 | -0.033 | -6.9 | +0.013 |
| radar_025 | 3 | 90 | +0.022 | [-0.044, +0.089] | 0.639 | -0.022 | -4.5 | +0.011 |
| range_075 | 3 | 90 | -0.022 | [-0.089, +0.033] | 0.588 | +0.022 | +5.0 | -0.005 |
| relay_failure | 3 | 90 | +0.078 | [+0.022, +0.133] | 0.001 | -0.078 | -16.2 | +0.031 |
| scout_failure | 3 | 90 | +0.022 | [-0.033, +0.078] | 0.547 | -0.022 | -4.4 | +0.011 |

## Step-Time Diagnostics

| Scenario | Steps Delta | Steps 95% CI | Timeout Delta | Timeout 95% CI |
|---|---:|---:|---:|---:|
| delay_2 | -4.5 | [-16.3, +7.2] | -0.022 | [-0.078, +0.033] |
| dropout_030 | -6.9 | [-18.8, +5.0] | -0.033 | [-0.089, +0.022] |
| radar_025 | -4.5 | [-18.8, +9.7] | -0.022 | [-0.089, +0.044] |
| range_075 | +5.0 | [-6.8, +19.1] | +0.022 | [-0.044, +0.089] |
| relay_failure | -16.2 | [-28.0, -6.7] | -0.078 | [-0.133, -0.022] |
| scout_failure | -4.4 | [-16.2, +7.3] | -0.022 | [-0.078, +0.033] |

## Use Boundary

```text
Positive success delta and negative timeout/steps delta favor the multi-relation graph.
Bootstrap intervals resample paired evaluation episodes with replacement; they are useful diagnostics but do not replace a larger seed-level significance study.
```
