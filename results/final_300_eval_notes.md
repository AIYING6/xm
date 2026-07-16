# Final 300-Episode Communication Evaluation

Date: 2026-07-13

## Setting

```text
target_policy = mixed
target_speed = 0.75
communication_radius = 4, 6, 8, 10
episodes = 300 per seed
seeds = 0, 1, 2
```

Compared methods:

```text
MAPPO
GAT-MAPPO
EA-RG-MAPPO-S
```

Generated files:

```text
results/final_comm_300_eval.csv
results/final_comm_300_summary.csv
results/latex_final_comm_300_table.tex
```

## Summary

| Method | Radius | Success | Collision | Timeout | Avg steps |
|---|---:|---:|---:|---:|---:|
| MAPPO | 4 | 0.707 ± 0.167 | 0.228 ± 0.099 | 0.072 ± 0.070 | 84.63 ± 31.75 |
| MAPPO | 6 | 0.770 ± 0.145 | 0.218 ± 0.130 | 0.017 ± 0.019 | 70.08 ± 29.73 |
| MAPPO | 8 | 0.810 ± 0.136 | 0.177 ± 0.126 | 0.017 ± 0.015 | 62.14 ± 25.16 |
| MAPPO | 10 | 0.836 ± 0.077 | 0.152 ± 0.067 | 0.014 ± 0.011 | 58.81 ± 16.62 |
| GAT-MAPPO | 4 | 0.811 ± 0.026 | 0.136 ± 0.020 | 0.060 ± 0.040 | 72.82 ± 14.04 |
| GAT-MAPPO | 6 | 0.838 ± 0.051 | 0.126 ± 0.034 | 0.039 ± 0.025 | 67.78 ± 18.91 |
| GAT-MAPPO | 8 | 0.784 ± 0.054 | 0.179 ± 0.042 | 0.038 ± 0.042 | 71.42 ± 18.20 |
| GAT-MAPPO | 10 | 0.802 ± 0.037 | 0.156 ± 0.024 | 0.043 ± 0.034 | 71.89 ± 12.11 |
| EA-RG-MAPPO-S | 4 | 0.926 ± 0.004 | 0.054 ± 0.007 | 0.022 ± 0.004 | 67.51 ± 0.63 |
| EA-RG-MAPPO-S | 6 | 0.919 ± 0.012 | 0.064 ± 0.006 | 0.018 ± 0.006 | 64.29 ± 1.61 |
| EA-RG-MAPPO-S | 8 | 0.890 ± 0.021 | 0.083 ± 0.012 | 0.027 ± 0.014 | 66.79 ± 4.71 |
| EA-RG-MAPPO-S | 10 | 0.879 ± 0.017 | 0.086 ± 0.020 | 0.039 ± 0.011 | 69.14 ± 1.74 |

## Interpretation

The 300-episode evaluation strengthens the main claim:

```text
EA-RG-MAPPO-S has consistently higher success and lower collision than MAPPO and GAT-MAPPO under limited communication.
```

Most important evidence:

```text
radius=4:
MAPPO collision = 0.228 ± 0.099
GAT collision   = 0.136 ± 0.020
EA-RG collision = 0.054 ± 0.007

radius=8:
MAPPO success = 0.810 ± 0.136
GAT success   = 0.784 ± 0.054
EA-RG success = 0.890 ± 0.021
```

The result also supports the stability claim:

```text
EA-RG-MAPPO-S has much smaller std in success, collision, and avg steps.
```

This 300-episode table should be used as the final main table. The older 100-episode table can be kept as an ablation table because it includes more method variants.
