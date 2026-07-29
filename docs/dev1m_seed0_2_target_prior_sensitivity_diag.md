# Dev-1M Seed 0-2 Target-Prior Sensitivity Diagnostic

Last updated: 2026-07-29

## Purpose

Evaluate whether validation-selected dev-1M policies rely on an overly accurate
fixed target prior under strict intermittent sensing.

This is a frozen-checkpoint diagnostic. It is not used for checkpoint
selection, reward tuning, or method selection.

## Protocol

Methods:

| Method | Seeds | Selected checkpoint source |
| --- | --- | --- |
| EA-RG-MAPPO | 0/1/2 | validation-selected dev-1M checkpoints |
| Single-Graph MAPPO | 0/1/2 | validation-selected dev-1M checkpoints |
| MAPPO/no-graph | 0/1/2 | validation-selected dev-1M checkpoints |

Evaluation settings:

```text
episodes_per_seed = 30
base_seed = 230000
target_policy = straight
strict_target_sensing = true
agent_target_info_bottleneck = true
failed_blue_agent = 1
node_failure_start_step = 40
node_failure_duration_steps = 80
communication_dropout_prob = 0.0
message_delay_steps = 0
```

Target-prior settings:

| Name | Target prior position |
| --- | --- |
| fixed_default | `(10000, 0, 5000)` |
| lateral_offset | `(10000, 8000, 5000)` |
| far_prior | `(0, -20000, 5000)` |

## Aggregate Results

| Method | Prior | Success mean | Success std | Recovery mean | Censored recovery steps | Tracking during failure | Connectivity during failure | Timeout | Collision |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| EA-RG-MAPPO | fixed_default | 0.5222 | 0.3564 | 0.5222 | 114.5667 | 0.4555 | 0.2568 | 0.4778 | 0.0000 |
| EA-RG-MAPPO | lateral_offset | 0.4333 | 0.4583 | 0.4333 | 133.8556 | 0.4067 | 0.2500 | 0.5667 | 0.0000 |
| EA-RG-MAPPO | far_prior | 0.6333 | 0.3180 | 0.6333 | 92.5111 | 0.4579 | 0.2329 | 0.3667 | 0.0000 |
| Single-Graph | fixed_default | 0.4778 | 0.4194 | 0.4778 | 125.7111 | 0.3963 | 0.2508 | 0.5222 | 0.0000 |
| Single-Graph | lateral_offset | 0.3000 | 0.4910 | 0.3000 | 160.5333 | 0.3731 | 0.1587 | 0.7000 | 0.0000 |
| Single-Graph | far_prior | 0.3000 | 0.4910 | 0.3000 | 160.5333 | 0.3362 | 0.1721 | 0.7000 | 0.0000 |
| MAPPO/no-graph | fixed_default | 0.5000 | 0.4702 | 0.5000 | 119.4556 | 0.3804 | 0.1464 | 0.5000 | 0.0000 |
| MAPPO/no-graph | lateral_offset | 0.5000 | 0.4702 | 0.5000 | 119.4556 | 0.3891 | 0.1501 | 0.5000 | 0.0000 |
| MAPPO/no-graph | far_prior | 0.4889 | 0.4683 | 0.4889 | 121.7111 | 0.3363 | 0.1338 | 0.5111 | 0.0000 |

## Delta from Default Prior

| Method | Perturbation | Success delta | Recovery delta |
| --- | --- | ---: | ---: |
| EA-RG-MAPPO | lateral_offset | -0.0889 | -0.0889 |
| EA-RG-MAPPO | far_prior | +0.1111 | +0.1111 |
| Single-Graph | lateral_offset | -0.1778 | -0.1778 |
| Single-Graph | far_prior | -0.1778 | -0.1778 |
| MAPPO/no-graph | lateral_offset | +0.0000 | +0.0000 |
| MAPPO/no-graph | far_prior | -0.0111 | -0.0111 |

Machine-readable outputs:

- `results/paper_config_runs/dev_1m/target_prior_diag/seed0_2_prior_sensitivity_episode_summary.csv`
- `results/paper_config_runs/dev_1m/target_prior_diag/seed0_2_prior_sensitivity_aggregate.csv`
- `results/paper_config_runs/dev_1m/target_prior_diag/seed0_2_prior_sensitivity_deltas.csv`

## Interpretation

- The fixed target prior is not a simple leakage path explaining the dev-1M
  results. A strong far-prior mismatch does not collapse EA-RG-MAPPO and has
  almost no effect on MAPPO/no-graph.
- EA-RG-MAPPO is not consistently hurt by prior perturbation. It drops under
  lateral offset but improves under far prior on the 30-episode diagnostic
  split. This suggests high seed/split variance rather than direct dependence
  on a specific prior point.
- Single-Graph is more sensitive to prior perturbation in this diagnostic,
  especially seed 2.
- MAPPO/no-graph remains surprisingly insensitive to target-prior perturbation.
  This reinforces the existing concern that the relay-failure task may still be
  solvable through learned geometric behavior and environment regularities, not
  only through graph-based communication recovery.

## Decision

Use this result as a credibility audit:

- It weakens the objection that the main result is caused by an overly accurate
  fixed target prior.
- It does not solve the main scientific warning: MAPPO/no-graph remains too
  competitive in some seeds.
- The next method-quality step should therefore focus on a task condition that
  requires fresher communication-mediated target information, or on a mechanism
  audit that demonstrates why multi-relation routing is causally necessary.

