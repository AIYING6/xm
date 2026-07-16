# Edge-Aware RI-GMAPPO Notes

Date: 2026-07-13

## Purpose

The previous RI-GMAPPO detach-intent result was promising under limited communication, but seed 2 was unstable, especially:

```text
radius 8, seed 2:
success = 0.72
collision = 0.24
```

This experiment adds relative edge features to the graph attention layer to improve stability.

## Implementation

Environment update:

```text
graph_obs["edge_feat"] shape = [num_nodes, num_nodes, 10]
```

Edge features:

```text
relative x / world_size
relative y / world_size
distance / world_size
distance / communication_radius
cos(relative bearing)
sin(relative bearing)
relative velocity x / 1.5
relative velocity y / 1.5
communication reachable flag
target-node flag
```

Model update:

```text
attention_score = node_pair_score + edge_score(edge_feat)
```

The final edge-score layer is initialized to zero, so warm-started old checkpoints initially behave like the old model. The edge branch then learns during training.

Updated files:

```text
envs/uav_pursuit_env.py
envs/__init__.py
algorithms/ri_gmappo/simple_ri_gmappo.py
scripts/evaluate_ri_gmappo.py
```

## Smoke Result

A 1-update smoke run passed:

```text
results/ri_gmappo_edge_smoke
```

Warm-start from GAT still works:

```text
loaded 18 matching tensors and 1 partial tensors; skipped 0
```

## Focused Test: Seed 2, Radius 8

Training:

```text
seed = 2
communication_radius = 8
updates = 30
detach_intent = True
intent_coef = 0.05
resume = results/gat_mappo_hybrid_slow_60_plus90/actor_critic_latest.pt
```

Old no-edge result:

```text
success = 0.72
collision = 0.24
```

Edge-aware result:

```text
best checkpoint:
success = 0.86
collision = 0.09

latest checkpoint:
success = 0.90
collision = 0.10
```

Interpretation:

```text
Relative edge features directly improve the previously weakest seed/radius case.
```

## 3-Seed Edge-Aware Communication Stress

All edge-aware models were trained at radius 8 for 30 updates, then evaluated at radii 4, 6, 8, and 10.

Per-seed best-checkpoint results:

| Seed | Radius | Success | Collision | Timeout | Avg steps | Intent acc |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 4 | 0.92 | 0.04 | 0.04 | 67.00 | 0.59 |
| 0 | 6 | 0.90 | 0.05 | 0.05 | 64.68 | 0.59 |
| 0 | 8 | 0.91 | 0.09 | 0.01 | 62.88 | 0.59 |
| 0 | 10 | 0.80 | 0.13 | 0.07 | 77.31 | 0.59 |
| 1 | 4 | 0.91 | 0.05 | 0.04 | 67.87 | 0.59 |
| 1 | 6 | 0.89 | 0.11 | 0.00 | 60.87 | 0.59 |
| 1 | 8 | 0.93 | 0.07 | 0.00 | 59.72 | 0.59 |
| 1 | 10 | 0.86 | 0.10 | 0.04 | 69.09 | 0.58 |
| 2 | 4 | 0.95 | 0.02 | 0.03 | 62.68 | 0.58 |
| 2 | 6 | 0.87 | 0.06 | 0.07 | 64.68 | 0.58 |
| 2 | 8 | 0.86 | 0.09 | 0.05 | 68.74 | 0.59 |
| 2 | 10 | 0.85 | 0.11 | 0.04 | 73.68 | 0.59 |

Mean ± std:

| Radius | Success | Collision | Timeout | Avg steps | Intent acc |
|---:|---:|---:|---:|---:|---:|
| 4 | 0.927 ± 0.021 | 0.037 ± 0.015 | 0.037 ± 0.006 | 65.85 ± 2.78 | 0.588 ± 0.004 |
| 6 | 0.887 ± 0.015 | 0.073 ± 0.032 | 0.040 ± 0.036 | 63.41 ± 2.20 | 0.586 ± 0.002 |
| 8 | 0.900 ± 0.036 | 0.083 ± 0.012 | 0.020 ± 0.026 | 63.78 ± 4.58 | 0.587 ± 0.001 |
| 10 | 0.837 ± 0.032 | 0.113 ± 0.015 | 0.050 ± 0.017 | 73.36 ± 4.12 | 0.587 ± 0.005 |

## Comparison to No-Edge RI-GMAPPO

No-edge 3-seed mean:

| Radius | Success | Collision |
|---:|---:|---:|
| 4 | 0.907 | 0.080 |
| 6 | 0.917 | 0.063 |
| 8 | 0.887 | 0.097 |
| 10 | 0.907 | 0.073 |

Edge-aware 3-seed mean:

| Radius | Success | Collision |
|---:|---:|---:|
| 4 | 0.927 | 0.037 |
| 6 | 0.887 | 0.073 |
| 8 | 0.900 | 0.083 |
| 10 | 0.837 | 0.113 |

## Current Judgment

Edge features are useful, but not yet a universally better final method.

What improved:

- radius 4 collision drops strongly;
- radius 8 seed-2 collapse is largely fixed;
- radius 8 standard deviation is much smaller than no-edge.

What got worse:

- radius 10 mean success drops from 0.907 to 0.837;
- training at a fixed radius 8 appears to overfit the communication condition.

Practical conclusion:

```text
Edge-aware attention is a valid module, but it should be trained with communication-radius randomization.
```

## Next Step

Implement communication-radius randomization during training:

```text
--comm-radius-random-min 4
--comm-radius-random-max 10
```

During training, each environment episode samples a communication radius from this range. Evaluation remains fixed at radius 4, 6, 8, or 10.

Expected benefit:

```text
Preserve the radius-4/radius-8 robustness of edge features
without hurting radius-10 performance.
```

## Random-Radius Training Update

A first random-radius training test was implemented.

New training arguments:

```text
--comm-radius-random-min
--comm-radius-random-max
```

During training, each environment samples a new communication radius when an episode resets. Evaluation still uses a fixed `--communication-radius`.

Test setting:

```text
seed = 2
comm_radius_random_min = 4
comm_radius_random_max = 10
updates = 30
detach_intent = True
intent_coef = 0.05
```

100-episode evaluation:

| Checkpoint | Radius | Success | Collision | Timeout | Avg steps | Intent acc |
|---|---:|---:|---:|---:|---:|---:|
| best | 4 | 0.81 | 0.12 | 0.07 | 84.80 | 0.59 |
| best | 6 | 0.90 | 0.09 | 0.01 | 78.45 | 0.59 |
| best | 8 | 0.90 | 0.06 | 0.04 | 78.79 | 0.58 |
| best | 10 | 0.85 | 0.10 | 0.05 | 75.27 | 0.58 |
| latest | 4 | 0.75 | 0.19 | 0.07 | 82.85 | 0.59 |
| latest | 6 | 0.87 | 0.08 | 0.06 | 77.10 | 0.59 |
| latest | 8 | 0.87 | 0.09 | 0.04 | 71.70 | 0.59 |
| latest | 10 | 0.80 | 0.12 | 0.09 | 77.27 | 0.59 |

Interpretation:

```text
Simple random-radius training did not improve the current edge-aware method.
It weakens radius-4 performance and does not recover radius-10 enough.
```

Current best practical direction:

1. Keep edge-aware attention as a useful module.
2. Do not rely on naive random-radius training yet.
3. Improve checkpoint selection with a larger validation set.
4. Consider staged training:

```text
stage 1: radius 8
stage 2: short conservative fine-tune on radius mix
```

The immediate next implementation should be a validation/evaluation helper that evaluates checkpoints using 100 episodes instead of relying on the 20-episode training-time best.

## Evaluation Helper

A unified RI run evaluator was added:

```text
scripts/evaluate_ri_run.py
```

Usage:

```bash
python scripts/evaluate_ri_run.py \
  --run-dir results/ri_gmappo_edge_rand_radius_seed2_30 \
  --episodes 100 \
  --radii 4 6 8 10 \
  --detach-intent
```

It evaluates:

```text
actor_critic_best.pt
actor_critic_latest.pt
```

and saves:

```text
ri_run_eval.csv
```

This should be used for future checkpoint selection instead of manually comparing scattered command outputs.

## Staged Random-Radius Fine-Tuning

The naive random-radius run was weak because it started from the GAT checkpoint and had to learn edge-aware control and radius robustness at the same time.

A staged test was run:

```text
stage 1: edge-aware training at radius 8
stage 2: low-lr random-radius fine-tune from stage-1 best checkpoint
```

Setting:

```text
seed = 2
resume = results/ri_gmappo_edge_seed2_r8_30/actor_critic_best.pt
updates = 20
lr = 3e-5
comm_radius_random_min = 4
comm_radius_random_max = 10
detach_intent = True
intent_coef = 0.05
```

Evaluation was generated with:

```bash
python scripts/evaluate_ri_run.py \
  --run-dir results/ri_gmappo_edge_stage2_rand_seed2_20 \
  --episodes 100 \
  --radii 4 6 8 10 \
  --detach-intent
```

Best checkpoint:

| Radius | Success | Collision | Timeout | Avg steps | Intent acc |
|---:|---:|---:|---:|---:|---:|
| 4 | 0.93 | 0.03 | 0.04 | 67.46 | 0.58 |
| 6 | 0.92 | 0.06 | 0.02 | 65.65 | 0.59 |
| 8 | 0.86 | 0.12 | 0.03 | 73.99 | 0.59 |
| 10 | 0.91 | 0.06 | 0.03 | 77.55 | 0.58 |

Latest checkpoint:

| Radius | Success | Collision | Timeout | Avg steps | Intent acc |
|---:|---:|---:|---:|---:|---:|
| 4 | 0.90 | 0.06 | 0.04 | 67.46 | 0.59 |
| 6 | 0.92 | 0.05 | 0.03 | 63.04 | 0.59 |
| 8 | 0.84 | 0.09 | 0.07 | 74.01 | 0.59 |
| 10 | 0.90 | 0.06 | 0.04 | 74.43 | 0.59 |

Comparison for seed 2:

| Variant | R4 success/collision | R8 success/collision | R10 success/collision |
|---|---:|---:|---:|
| edge fixed-r8 best | 0.95 / 0.02 | 0.86 / 0.09 | 0.85 / 0.11 |
| naive random-radius best | 0.81 / 0.12 | 0.90 / 0.06 | 0.85 / 0.10 |
| staged random-radius best | 0.93 / 0.03 | 0.86 / 0.12 | 0.91 / 0.06 |

Interpretation:

```text
Staged random-radius fine-tuning improves radius-10 generalization
without destroying radius-4 performance, but it does not improve radius-8.
```

This is better than naive random-radius training and worth testing on seeds 0 and 1.

Next decision:

```text
Run staged fine-tuning for seed 0 and seed 1.
If the 3-seed staged result improves radius-10 without hurting radius-4/radius-8 too much,
use staged edge-aware RI-GMAPPO as the main method candidate.
```

Staged fine-tuning has been repeated for seeds 0, 1, and 2.

Detailed summary:

```text
results/staged_random_radius_summary.md
```

Current candidate:

```text
RI-GMAPPO + edge-aware attention + detach intent + staged random-radius fine-tuning
```

The staged latest checkpoint is the most balanced current policy:

```text
radius 4:  success 0.907, collision 0.067
radius 6:  success 0.907, collision 0.073
radius 8:  success 0.883, collision 0.083
radius 10: success 0.880, collision 0.090
```
