# Staged Random-Radius Fine-Tuning Summary

Date: 2026-07-13

## Purpose

The edge-aware RI-GMAPPO model improved low-radius robustness and fixed the seed-2/radius-8 collapse, but it lost performance at radius 10. Naive random-radius training from the GAT checkpoint did not solve this.

This experiment tests staged fine-tuning:

```text
stage 1: train edge-aware RI-GMAPPO at communication radius 8
stage 2: resume from stage-1 best checkpoint and do short low-lr random-radius fine-tuning
```

## Setting

Stage 2:

```text
updates = 20
num_envs = 8
rollout_steps = 64
lr = 3e-5
comm_radius_random_min = 4
comm_radius_random_max = 10
detach_intent = True
intent_coef = 0.05
```

Evaluation:

```text
script = scripts/evaluate_ri_run.py
episodes = 100
radii = 4, 6, 8, 10
checkpoints = best, latest
```

Run directories:

```text
results/ri_gmappo_edge_stage2_rand_seed0_20
results/ri_gmappo_edge_stage2_rand_seed1_20
results/ri_gmappo_edge_stage2_rand_seed2_20
```

Each run contains:

```text
ri_run_eval.csv
```

## 3-Seed Mean and Std

### Best Checkpoint

| Radius | Success | Collision | Timeout | Avg steps | Intent acc |
|---:|---:|---:|---:|---:|---:|
| 4 | 0.933 ± 0.006 | 0.037 ± 0.006 | 0.030 ± 0.010 | 64.67 ± 3.06 | 0.588 ± 0.004 |
| 6 | 0.923 ± 0.025 | 0.053 ± 0.006 | 0.030 ± 0.017 | 62.47 ± 2.88 | 0.586 ± 0.003 |
| 8 | 0.877 ± 0.015 | 0.110 ± 0.010 | 0.020 ± 0.010 | 66.18 ± 6.85 | 0.587 ± 0.002 |
| 10 | 0.853 ± 0.067 | 0.100 ± 0.036 | 0.050 ± 0.035 | 75.09 ± 4.36 | 0.586 ± 0.004 |

### Latest Checkpoint

| Radius | Success | Collision | Timeout | Avg steps | Intent acc |
|---:|---:|---:|---:|---:|---:|
| 4 | 0.907 ± 0.012 | 0.067 ± 0.012 | 0.027 ± 0.012 | 69.47 ± 2.30 | 0.589 ± 0.003 |
| 6 | 0.907 ± 0.015 | 0.073 ± 0.021 | 0.020 ± 0.010 | 62.68 ± 6.51 | 0.587 ± 0.002 |
| 8 | 0.883 ± 0.051 | 0.083 ± 0.031 | 0.033 ± 0.032 | 65.21 ± 7.70 | 0.588 ± 0.003 |
| 10 | 0.880 ± 0.020 | 0.090 ± 0.026 | 0.033 ± 0.021 | 70.35 ± 3.54 | 0.588 ± 0.002 |

## Comparison With Edge Fixed-Radius Training

Edge fixed-r8 3-seed mean:

| Radius | Success | Collision |
|---:|---:|---:|
| 4 | 0.927 | 0.037 |
| 6 | 0.887 | 0.073 |
| 8 | 0.900 | 0.083 |
| 10 | 0.837 | 0.113 |

Staged latest 3-seed mean:

| Radius | Success | Collision |
|---:|---:|---:|
| 4 | 0.907 | 0.067 |
| 6 | 0.907 | 0.073 |
| 8 | 0.883 | 0.083 |
| 10 | 0.880 | 0.090 |

## Interpretation

Staged random-radius fine-tuning is more balanced than fixed-radius edge-aware training:

- radius 10 improves from `0.837 / 0.113` to `0.880 / 0.090`;
- radius 6 improves from `0.887` to `0.907`;
- radius 4 gets slightly worse but remains above 0.90 success;
- radius 8 gets slightly worse but remains near 0.88-0.90.

The latest checkpoint is more balanced than the training-time best checkpoint.

Current main-method candidate:

```text
RI-GMAPPO + edge-aware attention + detach intent + staged random-radius fine-tuning
```

Use `latest` checkpoint for staged fine-tune evaluation unless a larger validation protocol is added.

## Next Step

The next useful step is to generate figures and clean paper-style tables:

1. communication radius vs success rate;
2. communication radius vs collision rate;
3. method comparison table:
   - MAPPO,
   - GAT-MAPPO,
   - RI-GMAPPO no-edge,
   - RI-GMAPPO edge fixed-r8,
   - RI-GMAPPO staged random-radius.

This will clarify whether the current evidence is strong enough for a first paper-result draft.
