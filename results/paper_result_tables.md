# Paper-Style Result Tables

Date: 2026-07-13

## Limited-Communication Evaluation

Task:

```text
target_policy = mixed
target_speed = 0.75
evaluation episodes = 100
communication_radius = 4, 6, 8, 10
```

## Baselines

All rows below are 3-seed mean ± std results from the latest checkpoints of seed 0/1/2.

| Method | Radius | Success | Collision | Timeout | Avg steps |
|---|---:|---:|---:|---:|---:|
| MAPPO | 4 | 0.690 ± 0.212 | 0.240 ± 0.135 | 0.073 ± 0.083 | 85.40 ± 30.28 |
| MAPPO | 6 | 0.777 ± 0.158 | 0.217 ± 0.141 | 0.013 ± 0.019 | 68.69 ± 29.24 |
| MAPPO | 8 | 0.800 ± 0.167 | 0.180 ± 0.151 | 0.023 ± 0.021 | 62.21 ± 24.59 |
| MAPPO | 10 | 0.850 ± 0.054 | 0.143 ± 0.046 | 0.007 ± 0.009 | 58.90 ± 17.53 |
| GAT-MAPPO | 4 | 0.840 ± 0.037 | 0.127 ± 0.012 | 0.040 ± 0.042 | 70.21 ± 14.32 |
| GAT-MAPPO | 6 | 0.873 ± 0.045 | 0.097 ± 0.031 | 0.030 ± 0.022 | 64.53 ± 17.87 |
| GAT-MAPPO | 8 | 0.777 ± 0.052 | 0.183 ± 0.040 | 0.043 ± 0.048 | 67.52 ± 15.51 |
| GAT-MAPPO | 10 | 0.797 ± 0.029 | 0.170 ± 0.033 | 0.033 ± 0.029 | 69.51 ± 11.50 |

## RI-GMAPPO Variants

These rows are 3-seed mean ± std.

| Method | Radius | Success | Collision | Timeout | Avg steps |
|---|---:|---:|---:|---:|---:|
| RI no-edge | 4 | 0.907 ± 0.042 | 0.080 ± 0.044 | 0.017 ± 0.006 | 73.20 ± 7.60 |
| RI no-edge | 6 | 0.917 ± 0.076 | 0.063 ± 0.059 | 0.023 ± 0.023 | 72.77 ± 11.41 |
| RI no-edge | 8 | 0.887 ± 0.146 | 0.097 ± 0.125 | 0.017 ± 0.021 | 72.00 ± 13.45 |
| RI no-edge | 10 | 0.907 ± 0.071 | 0.073 ± 0.059 | 0.020 ± 0.017 | 72.04 ± 10.18 |
| RI edge fixed-r8 | 4 | 0.927 ± 0.021 | 0.037 ± 0.015 | 0.037 ± 0.006 | 65.85 ± 2.78 |
| RI edge fixed-r8 | 6 | 0.887 ± 0.015 | 0.073 ± 0.032 | 0.040 ± 0.036 | 63.41 ± 2.20 |
| RI edge fixed-r8 | 8 | 0.900 ± 0.036 | 0.083 ± 0.012 | 0.020 ± 0.026 | 63.78 ± 4.58 |
| RI edge fixed-r8 | 10 | 0.837 ± 0.032 | 0.113 ± 0.015 | 0.050 ± 0.017 | 73.36 ± 4.12 |
| RI edge staged | 4 | 0.907 ± 0.012 | 0.067 ± 0.012 | 0.027 ± 0.012 | 69.47 ± 2.30 |
| RI edge staged | 6 | 0.907 ± 0.015 | 0.073 ± 0.021 | 0.020 ± 0.010 | 62.68 ± 6.51 |
| RI edge staged | 8 | 0.883 ± 0.051 | 0.083 ± 0.031 | 0.033 ± 0.032 | 65.21 ± 7.70 |
| RI edge staged | 10 | 0.880 ± 0.020 | 0.090 ± 0.026 | 0.033 ± 0.021 | 70.35 ± 3.54 |

## Current Paper Claim Candidate

Strongest defensible claim:

```text
Edge-aware role graph coordination improves robustness under limited communication,
especially by reducing collision rate and variance compared with MAPPO and GAT-MAPPO.
```

More cautious wording:

```text
The proposed RI-GMAPPO variants maintain around 0.88-0.91 success under communication stress,
while showing lower collision rates than MAPPO and better radius-8/10 robustness than standard GAT-MAPPO.
```

Intent caveat:

```text
The current intent head has weak balanced accuracy and should not be claimed as accurate intent recognition.
Until fixed, intent should be reported as an auxiliary branch or ablation rather than the strongest contribution.
```

Important caveat:

```text
All main rows are now 3-seed results, but 3 seeds is still a minimum.
For final submission, consider 5 seeds or 300-500 evaluation episodes if time permits.
```

## Next Required Work

To make the table more paper-grade:

1. Add paired visual case studies for MAPPO/GAT/RI under radius 4 and radius 10.
2. Add intent prediction confusion matrix for RI variants.
3. Add statistical comparison or at least per-seed tables in the appendix.
4. Decide whether to report RI edge staged or RI edge fixed-r8 as the main method.

## Generated Artifacts

Machine-readable table:

```text
results/paper_comm_results.csv
results/mappo_comm_multi_seed_eval.csv
results/mappo_comm_multi_seed_summary.csv
results/gat_comm_multi_seed_eval.csv
results/gat_comm_multi_seed_summary.csv
```

Figure script:

```text
scripts/plot_comm_results.py
```

Generated figures:

```text
results/figures/method_overview_ea_rg_mappo_s.png
results/figures/comm_success_rate.png
results/figures/comm_collision_rate.png
results/figures/per_seed_success_scatter.png
results/figures/per_seed_collision_scatter.png
results/figures/trajectory_ri_advantage_r4.png
results/figures/trajectory_ri_advantage_r10.png
results/figures/ri_attention_heatmap_r4.png
results/figures/ri_attention_heatmap_r10.png
```

Appendix materials:

```text
results/per_seed_comm_appendix.csv
results/per_seed_comm_appendix.md
```
