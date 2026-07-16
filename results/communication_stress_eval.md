# Communication Stress Evaluation

Date: 2026-07-13

## Purpose

This experiment evaluates whether RI-GMAPPO is more robust when UAV-to-UAV communication is restricted.

Important implementation update:

```text
Local teammate observations are now masked by communication_radius.
If a teammate is outside communication range, its local-observation slot is zero.
```

This makes the stress test stricter and fairer for MAPPO, GAT-MAPPO, and RI-GMAPPO. Because of this environment change, these numbers should not be mixed directly with earlier default-radius results.

## Code Changes

Updated:

```text
envs/uav_pursuit_env.py
algorithms/mappo/simple_mappo.py
algorithms/gat_mappo/simple_gat_mappo.py
algorithms/ri_gmappo/simple_ri_gmappo.py
scripts/train_mappo.py
scripts/train_gat_mappo.py
scripts/train_ri_gmappo.py
scripts/evaluate_model.py
scripts/evaluate_gat_model.py
scripts/evaluate_ri_gmappo.py
```

New CLI argument:

```text
--communication-radius
```

## Setting

Evaluation:

```text
target_policy = mixed
target_speed  = 0.75
episodes      = 100
deterministic = True
```

Checkpoints:

```text
MAPPO: results/mappo_curriculum_slow_150/actor_critic_latest.pt
GAT:   results/gat_mappo_hybrid_slow_60_plus90/actor_critic_latest.pt
RI:    results/ri_gmappo_detach_intent005_30/actor_critic_best.pt
```

RI-GMAPPO uses:

```text
detach_intent = True
intent_coef   = 0.05
```

## Results

| Method | Radius | Success | Collision | Timeout | Avg steps | Intent acc |
|---|---:|---:|---:|---:|---:|---:|
| MAPPO | 4 | 0.39 | 0.43 | 0.19 | 124.50 | n/a |
| GAT-MAPPO | 4 | 0.85 | 0.14 | 0.01 | 82.88 | n/a |
| RI-GMAPPO | 4 | 0.94 | 0.05 | 0.02 | 65.50 | 0.59 |
| MAPPO | 6 | 0.56 | 0.41 | 0.04 | 107.44 | n/a |
| GAT-MAPPO | 6 | 0.82 | 0.14 | 0.04 | 87.79 | n/a |
| RI-GMAPPO | 6 | 0.95 | 0.04 | 0.01 | 62.84 | 0.59 |
| MAPPO | 8 | 0.57 | 0.39 | 0.05 | 92.96 | n/a |
| GAT-MAPPO | 8 | 0.74 | 0.24 | 0.02 | 85.35 | n/a |
| RI-GMAPPO | 8 | 0.95 | 0.04 | 0.01 | 62.87 | 0.59 |
| MAPPO | 10 | 0.79 | 0.19 | 0.02 | 79.38 | n/a |
| GAT-MAPPO | 10 | 0.76 | 0.21 | 0.03 | 80.18 | n/a |
| RI-GMAPPO | 10 | 0.92 | 0.05 | 0.03 | 71.07 | 0.59 |

## Interpretation

This is the strongest result so far for the RI-GMAPPO direction.

Key observations:

1. MAPPO degrades heavily under tight communication because teammate observations are masked.
2. GAT-MAPPO is more robust than MAPPO at radius 4 and 6, but collision remains higher than RI-GMAPPO.
3. RI-GMAPPO keeps high success across all tested radii:

```text
radius 4:  success 0.94, collision 0.05
radius 6:  success 0.95, collision 0.04
radius 8:  success 0.95, collision 0.04
radius 10: success 0.92, collision 0.05
```

4. RI-GMAPPO also keeps intent accuracy near 0.59 across radii, suggesting the intent branch remains stable under communication stress.

## Current Judgment

The communication-stress result gives a much stronger paper angle than the plain mixed/0.75 evaluation:

```text
Target-intent-aware graph policy improves robustness under limited communication.
```

This is more defensible than claiming a generic GAT improvement.

However, this is still a representative-checkpoint evaluation. For paper-grade evidence, repeat the communication-stress test for 3 seeds.

## Next Step

Run 3-seed communication-stress evaluation for RI-GMAPPO detach-intent and compare against MAPPO/GAT where possible.

Recommended minimum:

```text
RI-GMAPPO seed 0/1/2
communication_radius = 4, 6, 8, 10
100 episodes each
```

If the 3-seed stress result remains strong, proceed to:

1. Add relative edge features.
2. Generate communication-stress plots.
3. Prepare the first paper result table.

## 3-Seed RI-GMAPPO Update

RI-GMAPPO detach-intent was evaluated with seeds 0, 1, and 2 under the same communication radii.

Per-seed results:

| Seed | Radius | Success | Collision | Timeout | Avg steps | Intent acc |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 4 | 0.94 | 0.05 | 0.02 | 65.50 | 0.59 |
| 0 | 6 | 0.95 | 0.04 | 0.01 | 62.84 | 0.59 |
| 0 | 8 | 0.95 | 0.04 | 0.01 | 62.87 | 0.59 |
| 0 | 10 | 0.92 | 0.05 | 0.03 | 71.07 | 0.59 |
| 1 | 4 | 0.92 | 0.06 | 0.02 | 73.42 | 0.59 |
| 1 | 6 | 0.97 | 0.02 | 0.01 | 70.24 | 0.59 |
| 1 | 8 | 0.99 | 0.01 | 0.00 | 65.69 | 0.59 |
| 1 | 10 | 0.97 | 0.03 | 0.00 | 62.38 | 0.58 |
| 2 | 4 | 0.86 | 0.13 | 0.01 | 80.69 | 0.43 |
| 2 | 6 | 0.83 | 0.13 | 0.05 | 85.24 | 0.48 |
| 2 | 8 | 0.72 | 0.24 | 0.04 | 87.44 | 0.44 |
| 2 | 10 | 0.83 | 0.14 | 0.03 | 82.68 | 0.42 |

Mean ± std:

| Radius | Success | Collision | Timeout | Avg steps | Intent acc |
|---:|---:|---:|---:|---:|---:|
| 4 | 0.907 ± 0.042 | 0.080 ± 0.044 | 0.017 ± 0.006 | 73.20 ± 7.60 | 0.537 ± 0.089 |
| 6 | 0.917 ± 0.076 | 0.063 ± 0.059 | 0.023 ± 0.023 | 72.77 ± 11.41 | 0.550 ± 0.064 |
| 8 | 0.887 ± 0.146 | 0.097 ± 0.125 | 0.017 ± 0.021 | 72.00 ± 13.45 | 0.538 ± 0.089 |
| 10 | 0.907 ± 0.071 | 0.073 ± 0.059 | 0.020 ± 0.017 | 72.04 ± 10.18 | 0.532 ± 0.094 |

Updated interpretation:

The 3-seed result still supports the limited-communication direction:

```text
RI-GMAPPO keeps mean success near or above 0.89 across all radii.
Mean collision stays below 0.10 across all radii.
```

But the method is not yet stable enough:

```text
seed 2 drops sharply at radius 8:
success = 0.72, collision = 0.24
```

This means the paper claim should be:

```text
RI-GMAPPO shows promising robustness under limited communication,
but training stability must be improved before final experiments.
```

The next implementation target should be relative edge features or a more stable checkpoint-selection/evaluation protocol.
