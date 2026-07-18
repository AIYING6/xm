# Aggregate Robustness Summary

Purpose:

```text
Summarize robustness across evaluation conditions without introducing a new training run.
Mean margin is mean_success - mean_collision.
Conservative margin is worst_success - worst_collision, where worst_success is the minimum success across conditions and worst_collision is the maximum collision across conditions.
These are descriptive diagnostics for paper organization, not a new optimization objective.
```

## Scope Definitions

| Scope | Definition |
|---|---|
| `final_cross_radius` | 300-episode final evaluation across communication radii 4, 6, 8, and 10 |
| `dropout_diagnostic` | 50-episode communication-dropout diagnostic across radii 4 and 8 and dropout probabilities 0, 0.25, and 0.5 |

## Aggregate Metrics

| Scope | Method | Conditions | Mean success | Worst success | Success range | Mean collision | Worst collision | Collision range | Mean margin | Conservative margin |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Final cross-radius | MAPPO | 4 | 0.781 | 0.707 | 0.129 | 0.194 | 0.228 | 0.076 | 0.587 | 0.479 |
| Final cross-radius | GAT-MAPPO | 4 | 0.809 | 0.784 | 0.053 | 0.149 | 0.179 | 0.053 | 0.660 | 0.606 |
| Final cross-radius | EA-RG-MAPPO-S | 4 | 0.903 | 0.879 | 0.047 | 0.072 | 0.086 | 0.031 | 0.831 | 0.793 |
| Dropout diagnostic | MAPPO | 6 | 0.699 | 0.593 | 0.240 | 0.259 | 0.320 | 0.153 | 0.440 | 0.273 |
| Dropout diagnostic | GAT-MAPPO | 6 | 0.807 | 0.767 | 0.073 | 0.157 | 0.187 | 0.067 | 0.650 | 0.580 |
| Dropout diagnostic | EA-RG-MAPPO-S | 6 | 0.892 | 0.853 | 0.067 | 0.070 | 0.107 | 0.060 | 0.822 | 0.747 |

## Reading Notes

```text
Final cross-radius: EA-RG-MAPPO-S mean_margin=0.831, conservative_margin=0.793, worst_collision=0.086.
Dropout diagnostic: EA-RG-MAPPO-S mean_margin=0.822, conservative_margin=0.747, worst_collision=0.107.
Use these values as compact descriptive evidence for finite-communication robustness.
Do not replace the main per-radius tables with this aggregate summary.
```
