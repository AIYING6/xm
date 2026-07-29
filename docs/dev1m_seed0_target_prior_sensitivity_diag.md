# Dev-1M Seed-0 Target-Prior Sensitivity Diagnostic

Last updated: 2026-07-29

## Purpose

Check whether the validation-selected dev-1M seed-0 policies rely on an overly
accurate fixed target prior under strict intermittent sensing.

This is a frozen-checkpoint diagnostic, not a tuning result.

## Protocol

Selected seed-0 checkpoints:

| Method | Graph encoder | Checkpoint update |
| --- | --- | ---: |
| EA-RG-MAPPO | multi_relation | 1600 |
| Single-Graph MAPPO | single | 3907 |
| MAPPO/no-graph | no_graph | 3800 |

Evaluation:

```text
episodes = 30
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

## Results

| Prior | Method | Success | Recovery | Censored recovery steps | Tracking during failure | Connectivity during failure | Timeout | Collision |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| fixed_default | EA-RG-MAPPO | 0.9333 | 0.9333 | 32.0000 | 0.5713 | 0.3333 | 0.0667 | 0.0000 |
| fixed_default | Single-Graph | 0.8667 | 0.8667 | 46.3000 | 0.8744 | 0.3111 | 0.1333 | 0.0000 |
| fixed_default | MAPPO/no-graph | 0.5667 | 0.5667 | 105.3333 | 0.4044 | 0.3064 | 0.4333 | 0.0000 |
| lateral_offset | EA-RG-MAPPO | 0.9333 | 0.9333 | 32.0000 | 0.5713 | 0.3333 | 0.0667 | 0.0000 |
| lateral_offset | Single-Graph | 0.8667 | 0.8667 | 46.3000 | 0.8744 | 0.3111 | 0.1333 | 0.0000 |
| lateral_offset | MAPPO/no-graph | 0.5667 | 0.5667 | 105.3333 | 0.4305 | 0.3175 | 0.4333 | 0.0000 |
| far_prior | EA-RG-MAPPO | 0.9333 | 0.9333 | 32.0000 | 0.5713 | 0.3333 | 0.0667 | 0.0000 |
| far_prior | Single-Graph | 0.8667 | 0.8667 | 46.3000 | 0.8744 | 0.3111 | 0.1333 | 0.0000 |
| far_prior | MAPPO/no-graph | 0.5333 | 0.5333 | 112.1000 | 0.2881 | 0.2688 | 0.4667 | 0.0000 |

Machine-readable summary:

`results/paper_config_runs/dev_1m/target_prior_diag/seed0_prior_sensitivity_summary.csv`

## Interpretation

- EA-RG-MAPPO and Single-Graph are insensitive to these prior perturbations on
  the seed-0 diagnostic split.
- MAPPO/no-graph is mildly affected by the far prior, but it does not collapse.
- The seed-0 dev-1M result is therefore unlikely to be explained only by an
  overly accurate fixed target prior.
- This does not prove full robustness. A paper-facing robustness check should
  repeat the same perturbations on seeds 1/2 selected checkpoints or run a
  formal randomized-prior evaluation after the final scenario is frozen.

## Decision

Keep target-prior perturbation as a credibility diagnostic. It is not a main
contribution and should not be used to tune checkpoints.

