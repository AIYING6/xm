# Weaving-Mild Strict Failure Fine-Tuning Diagnostic

Date: 2026-07-22

## Purpose

This diagnostic tested whether the completed straight-target fixed-update-60 policies can be adapted directly to a mild weaving target under the same strict relay-failure bottleneck used by the main Gate 1 evidence.

The question was not manuscript-level performance. The question was whether `weaving_mild` is ready to become a formal scenario-depth table.

## Protocol

- Methods: `single`, `multi_relation`
- Seeds: `0, 1, 2`
- Source checkpoints: straight-target safety fixed-update-60 checkpoints
- Target policy: `weaving_mild`
- Strict sensing: enabled
- Agent target-information bottleneck: enabled
- Failure scenario: `dropout030_relay_failure`
- Fine-tuning budget: 20 updates
- Checkpoint interval: 5 updates
- Validation/test budget: 10 episodes per seed

Outputs:

- `results/gate1_safety_fx60_weaving_mild_finetune_3seed_dev20/`

## Result

Validation selected update 20 for every method/seed, but validation recovery stayed at zero for all selected checkpoints.

Disjoint test recovery also stayed at zero for both methods:

| Method | Recovery | Timeout | Collision | Mean steps | Tracking during failure | Connectivity during failure |
|---|---:|---:|---:|---:|---:|---:|
| `single` | 0.0% | 100.0% | 0.0% | 260.0 | 9.6% | 11.3% |
| `multi_relation` | 0.0% | 100.0% | 0.0% | 260.0 | 7.2% | 7.1% |

Neither method formed a valid kill-chain recovery under the strict relay-failure weaving setting within the 20-update adaptation budget.

## Interpretation

Directly combining target weaving, strict intermittent sensing, target-information bottleneck, and relay failure is currently too hard for a short fine-tuning run.

This result should not be used as a negative claim about the proposed method. It is a scenario-readiness diagnostic showing that the difficulty jump is too large for immediate formal reporting.

The correct next move is staged scenario-depth training:

1. Nominal `weaving_mild` adaptation without strict sensing or node failure.
2. Add strict sensing and the target-information bottleneck after nominal weaving becomes learnable.
3. Add relay failure only after the policy can solve nominal strict weaving.

## Decision

`weaving_mild` is not ready for five-seed formal scenario-depth reporting.

Use it as a planned Q1-quality enhancement only after staged curriculum diagnostics produce a useful recovery range. A useful range means full `multi_relation` recovery is clearly above zero and below saturation, preferably around 60%-90%, while `single` remains meaningfully lower.
