# RI-GMAPPO Detach-Intent 3-Seed Summary

Date: 2026-07-13

## Setting

Method:

```text
RI-GMAPPO
detach_intent = True
intent_coef   = 0.05
```

Training:

```text
target_policy = mixed
target_speed  = 0.75
updates       = 30
num_envs      = 8
rollout_steps = 64
lr            = 1e-4
resume        = results/gat_mappo_hybrid_slow_60_plus90/actor_critic_latest.pt
```

Evaluation:

```text
100 deterministic episodes
target_policy = mixed
target_speed  = 0.75
checkpoint    = actor_critic_best.pt
```

## Per-Seed Results

| Seed | Success | Collision | Timeout | Avg steps | Intent acc |
|---:|---:|---:|---:|---:|---:|
| 0 | 0.90 | 0.07 | 0.04 | 51.18 | 0.58 |
| 1 | 0.94 | 0.05 | 0.01 | 56.16 | 0.59 |
| 2 | 0.84 | 0.11 | 0.05 | 55.81 | 0.38 |

## Mean and Standard Deviation

| Metric | Mean | Std |
|---|---:|---:|
| Success | 0.893 | 0.050 |
| Collision | 0.077 | 0.031 |
| Timeout | 0.033 | 0.021 |
| Avg steps | 54.38 | 2.78 |
| Intent acc | 0.516 | 0.115 |

## Baseline Comparison

Current reference baselines use 100 mixed/0.75 evaluation episodes:

| Method | Success | Collision | Timeout | Avg steps |
|---|---:|---:|---:|---:|
| MAPPO curriculum checkpoint | 0.87 | 0.12 | 0.01 | 51.99 |
| Hybrid GAT-MAPPO curriculum checkpoint | 0.82 | 0.14 | 0.05 | 54.94 |
| RI-GMAPPO detach-intent, 3-seed mean | 0.893 | 0.077 | 0.033 | 54.38 |

## Interpretation

The 3-seed result is promising:

```text
success:   0.87 -> 0.893
collision: 0.12 -> 0.077
```

However, the result is not fully stable:

- seed 0 and seed 1 outperform MAPPO clearly;
- seed 2 drops to 0.84 success and 0.11 collision;
- intent accuracy also varies from 0.38 to 0.59.

Current conclusion:

```text
detach_intent + intent_coef=0.05 is the current best RI-GMAPPO variant,
but the method still needs stability improvement before it can support a strong paper claim.
```

## Next Step

The next most useful experiment is communication-stress evaluation, not immediate LAG migration.

Required change:

```text
Add --communication-radius to training/evaluation scripts.
```

Then evaluate:

```text
communication_radius = 4, 6, 8, 10
```

Compare:

```text
MAPPO
Hybrid GAT-MAPPO
RI-GMAPPO detach-intent
```

If RI-GMAPPO degrades more slowly under communication limits, the paper contribution becomes much stronger.

Communication-stress evaluation has been started and the representative checkpoint result is strong:

```text
results/communication_stress_eval.md
```
