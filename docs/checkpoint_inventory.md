# Checkpoint Inventory

Generated: 2026-07-16T22:21:37

Purpose:

```text
Map paper methods and seeds to concrete checkpoint directories and training logs.
This report is generated from existing files only; it does not train or evaluate policies.
```

| Method | Seed | Directory | Checkpoint | Log rows | Last eval success | Last eval collision | Last eval steps |
|---|---:|---|---:|---:|---:|---:|---:|
| MAPPO | 0 | `results/mappo_curriculum_slow_150` | yes | 150 | 1.000 | 0.000 | 37.5 |
| MAPPO | 1 | `results/mappo_curriculum_slow_seed1_150` | yes | 150 | 1.000 | 0.000 | 24.9 |
| MAPPO | 2 | `results/mappo_curriculum_slow_seed2_150` | yes | 150 | 0.967 | 0.033 | 35.4 |
| GAT-MAPPO | 0 | `results/gat_mappo_hybrid_slow_60_plus90` | yes | 90 | 0.900 | 0.100 | 36.1 |
| GAT-MAPPO | 1 | `results/gat_mappo_hybrid_slow_seed1_60_plus90` | yes | 90 | 1.000 | 0.000 | 36.6 |
| GAT-MAPPO | 2 | `results/gat_mappo_hybrid_slow_seed2_60_plus90` | yes | 90 | 1.000 | 0.000 | 30.3 |
| EA-RG-MAPPO-S | 0 | `results/ri_gmappo_edge_stage2_rand_seed0_20` | yes | 20 | 0.900 | 0.050 | 75.2 |
| EA-RG-MAPPO-S | 1 | `results/ri_gmappo_edge_stage2_rand_seed1_20` | yes | 20 | 1.000 | 0.000 | 73.3 |
| EA-RG-MAPPO-S | 2 | `results/ri_gmappo_edge_stage2_rand_seed2_20` | yes | 20 | 0.850 | 0.000 | 76.2 |

Interpretation:

```text
The final paper evaluation uses these checkpoints and re-evaluates them with 300 episodes per seed.
Training-log last evaluation rows are provided only as a run sanity check, not as final paper results.
```
