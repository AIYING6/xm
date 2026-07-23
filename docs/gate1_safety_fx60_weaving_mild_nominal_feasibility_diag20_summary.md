# Weaving-Mild Nominal Feasibility Diagnostic

Date: 2026-07-22

## Purpose

The strict failure fine-tuning run produced zero recovery for both `single` and `multi_relation`. This follow-up isolated whether the issue comes from the `weaving_mild` target itself or from combining weaving with strict sensing and relay failure.

## Protocol

- Methods: `single`, `multi_relation`
- Seeds: `0, 1, 2`
- Checkpoints: existing straight-target fixed-update-60 checkpoints
- Target policy: `weaving_mild`
- Strict sensing: disabled
- Agent target-information bottleneck: disabled
- Node failure: disabled
- Evaluation budget: 20 episodes per seed

Outputs:

- `results/gate1_safety_fx60_weaving_mild_nominal_feasibility_diag20/`

## Result

| Method | Success | Chain closed | Attack window | Timeout | Collision | Tracking rate | Communication connectivity |
|---|---:|---:|---:|---:|---:|---:|---:|
| `single` | 0.0% | 0.0% | 0.0% | 98.3% | 0.0% | 10.5% | 32.1% |
| `multi_relation` | 21.7% | 21.7% | 21.7% | 78.3% | 0.0% | 24.4% | 45.5% |

Seed-level `multi_relation` success was uneven: seed 0 reached 45.0%, seed 2 reached 20.0%, and seed 1 remained at 0.0%.

## Interpretation

The mild weaving target is not impossible, but current straight-target checkpoints transfer weakly. The multi-relation policy retains some capability under nominal weaving, while the single-graph policy fails on all three seeds.

The strict relay-failure variant fails because it stacks several difficulty sources at once:

- maneuvering target;
- intermittent sensing;
- target-information bottleneck;
- relay failure;
- no staged target-policy adaptation.

## Decision

Do not promote `weaving_mild` into the main paper table yet.

The next experiment should be a staged weaving curriculum. The first acceptance gate is nominal weaving success for `multi_relation`, not strict relay-failure recovery. If nominal weaving cannot reach a useful range after staged training, reduce target maneuver amplitude or redesign the target-policy curriculum before spending five-seed formal budget.
