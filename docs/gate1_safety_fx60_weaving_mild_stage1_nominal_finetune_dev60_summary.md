# Weaving-Mild Stage 1 Nominal Fine-Tuning Dev60 Summary

Date: 2026-07-22

## Purpose

This run extended the checkpoint-compatible Stage 1 nominal `weaving_mild` fine-tuning budget from 20 to 60 updates.

The goal was to determine whether longer nominal target-policy adaptation is enough to make the maneuvering-target scenario ready for Stage 2 strict sensing.

## Protocol

- Method: `multi_relation`
- Seeds: `0, 1, 2`
- Source checkpoints: mature straight-target safety fixed-update-60 checkpoints
- Target policy: `weaving_mild`
- Strict sensing: disabled
- Agent target-information bottleneck: disabled
- Node failure: disabled
- Hidden dimension: `64`
- Learning rate: `1e-5`
- Fine-tuning budget: 60 updates
- Snapshots: every 10 updates
- Validation: 30 episodes per seed
- Test: 50 episodes per seed

Outputs:

- `results/gate1_safety_fx60_weaving_mild_nominal_finetune_from_straight_h64_lr1e5_dev60/`

## Validation Selection

Validation selected:

| Seed | Selected update | Validation success | Validation collision |
|---:|---:|---:|---:|
| 0 | 60 | 63.3% | 0.0% |
| 1 | 60 | 0.0% | 0.0% |
| 2 | 30 | 26.7% | 0.0% |

## Test Result

| Seed | Selected update | Success | Timeout | Collision | Mean steps |
|---:|---:|---:|---:|---:|---:|
| 0 | 60 | 58.0% | 42.0% | 0.0% | 184.2 |
| 1 | 60 | 0.0% | 100.0% | 0.0% | 260.0 |
| 2 | 30 | 16.0% | 84.0% | 0.0% | 247.1 |

Aggregate:

| Method | Success | Timeout | Collision |
|---|---:|---:|---:|
| `multi_relation` | 24.7% | 75.3% | 0.0% |

## Interpretation

Longer Stage 1 fine-tuning did not solve the nominal `weaving_mild` adaptation problem.

Compared with the 20-update diagnostic, seed 0 remains usable, seed 2 remains weak, and seed 1 remains completely stuck. The mean success rate stays around 25%, far below the 60%-80% gate needed before adding strict sensing or relay failure.

The result argues against simply scaling updates for the current `weaving_mild` setup.

## Decision

Do not proceed to Stage 2 strict-sensing weaving.

Before any formal maneuvering-target experiment, the project needs a gentler target-policy curriculum or a reward/curriculum redesign that specifically handles target maneuver adaptation. Blindly increasing the training budget is not justified by this diagnostic.
