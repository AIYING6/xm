# Communication-Dropout Robustness Diagnostic

Purpose:

```text
Evaluate trained policies under stochastic pursuer-pursuer communication-link dropout without retraining.
The diagnostic masks both teammate local-observation slots and graph adjacency/edge reachability.
The target observation node is retained; this experiment only degrades pursuer-pursuer communication links.
```

## Summary

| Method | Radius | Dropout | Success mean | Collision mean |
|---|---:|---:|---:|---:|
| MAPPO | 4 | 0.00 | 0.673 | 0.267 |
| MAPPO | 4 | 0.25 | 0.593 | 0.320 |
| MAPPO | 4 | 0.50 | 0.613 | 0.300 |
| MAPPO | 8 | 0.00 | 0.833 | 0.167 |
| MAPPO | 8 | 0.25 | 0.780 | 0.207 |
| MAPPO | 8 | 0.50 | 0.700 | 0.293 |
| GAT-MAPPO | 4 | 0.00 | 0.767 | 0.187 |
| GAT-MAPPO | 4 | 0.25 | 0.813 | 0.140 |
| GAT-MAPPO | 4 | 0.50 | 0.807 | 0.167 |
| GAT-MAPPO | 8 | 0.00 | 0.840 | 0.120 |
| GAT-MAPPO | 8 | 0.25 | 0.813 | 0.153 |
| GAT-MAPPO | 8 | 0.50 | 0.800 | 0.173 |
| EA-RG-MAPPO-S | 4 | 0.00 | 0.873 | 0.067 |
| EA-RG-MAPPO-S | 4 | 0.25 | 0.887 | 0.073 |
| EA-RG-MAPPO-S | 4 | 0.50 | 0.920 | 0.047 |
| EA-RG-MAPPO-S | 8 | 0.00 | 0.853 | 0.107 |
| EA-RG-MAPPO-S | 8 | 0.25 | 0.900 | 0.073 |
| EA-RG-MAPPO-S | 8 | 0.50 | 0.920 | 0.053 |

## Delta from No-Dropout Diagnostic Baseline

| Method | Radius | Dropout | Delta success | Delta collision |
|---|---:|---:|---:|---:|
| MAPPO | 4 | 0.25 | -0.080 | +0.053 |
| MAPPO | 4 | 0.50 | -0.060 | +0.033 |
| MAPPO | 8 | 0.25 | -0.053 | +0.040 |
| MAPPO | 8 | 0.50 | -0.133 | +0.127 |
| GAT-MAPPO | 4 | 0.25 | +0.047 | -0.047 |
| GAT-MAPPO | 4 | 0.50 | +0.040 | -0.020 |
| GAT-MAPPO | 8 | 0.25 | -0.027 | +0.033 |
| GAT-MAPPO | 8 | 0.50 | -0.040 | +0.053 |
| EA-RG-MAPPO-S | 4 | 0.25 | +0.013 | +0.007 |
| EA-RG-MAPPO-S | 4 | 0.50 | +0.047 | -0.020 |
| EA-RG-MAPPO-S | 8 | 0.25 | +0.047 | -0.033 |
| EA-RG-MAPPO-S | 8 | 0.50 | +0.067 | -0.053 |

## Use in Paper

```text
Use this as an appendix-level robustness diagnostic only.
Do not merge it with the final 300-episode main table, because it uses a different evaluation budget and an additional communication-dropout perturbation.
```
