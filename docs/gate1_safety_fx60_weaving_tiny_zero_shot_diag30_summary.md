# Weaving-Tiny Zero-Shot Diagnostic

Date: 2026-07-22

## Purpose

The `weaving_mild` Stage 1 adaptation remained too difficult. This diagnostic added and evaluated a smaller target-maneuver policy, `weaving_tiny`, as a potential curriculum entry point.

`weaving_tiny` is opt-in and does not change any existing default environment behavior.

## Implementation

`weaving_tiny` uses the same target-motion structure as `weaving_mild`, but with smaller lateral and altitude oscillations:

- lateral heading amplitude: `0.06`
- altitude amplitude: `120 m`

A regression test verifies that, under the same deterministic initial state, `weaving_tiny` induces a smaller heading perturbation than `weaving_mild`.

## Protocol

- Methods: `single`, `multi_relation`
- Seeds: `0, 1, 2`
- Checkpoints: mature straight-target safety fixed-update-60 checkpoints
- Target policy: `weaving_tiny`
- Strict sensing: disabled
- Node failure: disabled
- Evaluation budget: 30 episodes per seed

Outputs:

- `results/gate1_safety_fx60_weaving_tiny_nominal_zero_shot_diag30/`

## Result

| Method | Success | Timeout | Collision |
|---|---:|---:|---:|
| `multi_relation` | 28.9% | 70.0% | 1.1% |
| `single` | 0.0% | 97.8% | 2.2% |

Seed-level `multi_relation` success:

| Seed | Success |
|---:|---:|
| 0 | 66.7% |
| 1 | 0.0% |
| 2 | 20.0% |

## Seed-1 Source Snapshot Check

To test whether seed 1 failed because update 60 was a poor transfer checkpoint, source updates `10, 20, 30, 40, 50, 60` were evaluated on `weaving_tiny`.

All six source snapshots had `0.0%` success for seed 1. This suggests the failure is not just checkpoint selection.

## Interpretation

`weaving_tiny` is a better curriculum entry point than `weaving_mild`, but it still does not solve the maneuvering-target route. The main blocker is seed-level transfer brittleness: some source policies adapt or transfer to maneuvering targets, while seed 1 does not.

The next improvement should not be another simple update-budget increase. Better options are:

1. Add a staged target-policy curriculum during training: `straight -> weaving_tiny -> weaving_mild`.
2. Add a target-maneuver-aware shaping term that rewards maintaining approach geometry under lateral target drift.
3. Use validation selection over target-policy stages, not only over PPO update number.

## Decision

Keep maneuvering target experiments as scenario-depth development evidence for now. Do not promote them into the main paper table until seed-level robustness improves.
