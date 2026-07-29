# Dev-1M MAPPO/No-Graph Seed-1 Anomaly Diagnostic

Last updated: 2026-07-29

## Purpose

Diagnose why MAPPO/no-graph seed 1 remains highly successful under the
`fresh20_dropout030_delay2` stress condition, while MAPPO/no-graph seeds 0 and 2
fail.

This uses the frozen fresh-message stress evaluation outputs. It does not
change checkpoints or tune protocols.

## Source

Stress condition:

```text
max_target_message_age_steps = 20
communication_dropout_prob = 0.30
message_delay_steps = 2
failed_blue_agent = 1
node_failure_start_step = 40
node_failure_duration_steps = 80
base_seed = 240000
episodes = 30
```

Machine-readable diagnostic:

`results/paper_config_runs/dev_1m/fresh_message_stress/fresh20_dropout030_delay2_seed0_2/no_graph_seed1_anomaly_metrics.json`

## Key Comparison

| Policy | Success | Mean steps | Successful mean steps | Successful first attack-window step | Successful tracking during failure | Successful connectivity during failure |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| EA-RG-MAPPO seed 1 | 0.4333 | 188.7333 | 95.5385 | 64.6923 | 0.7804 | 0.2307 |
| MAPPO/no-graph seed 1 | 0.9667 | 66.6333 | 59.9655 | 56.9655 | 0.4660 | 0.1455 |
| MAPPO/no-graph seed 0 | 0.0000 | 260.0000 | n/a | n/a | n/a | n/a |
| MAPPO/no-graph seed 2 | 0.0000 | 260.0000 | n/a | n/a | n/a | n/a |

## Interpretation

MAPPO/no-graph seed 1 does not look like a communication-recovery policy.

Evidence:

- Successful episodes end very early: mean successful episode length is about
  `60` steps.
- The attack window appears around step `57`, only shortly after relay failure
  begins at step `40`.
- Successful connectivity during failure is low (`0.1455`), lower than
  EA-RG-MAPPO seed 1 (`0.2307`).
- Successful tracking during failure is moderate (`0.4660`), much lower than
  EA-RG-MAPPO seed 1 (`0.7804`).

The most likely explanation is that MAPPO/no-graph seed 1 learned a fast
geometric interception mode that can form the attack window before the
communication-recovery problem fully matters. This is not evidence that
no-graph solves the intended kill-chain recovery problem.

## Consequence

The current relay-failure setup still allows some policies to win by early
geometric closure. This weakens the graph-centric paper claim unless the final
scenario explicitly separates:

1. early geometric interception;
2. true post-failure target-information recovery;
3. sustained attack-window formation after communication disruption.

## Recommended Fix

Do not simply increase dropout or delay again. Instead, introduce a controlled
evaluation condition that makes early geometric closure insufficient, such as:

- score recovery only if attack-window formation occurs after a minimum
  post-failure delay;
- randomize target initial lateral/range position enough that memorized fast
  intercept geometry is unreliable;
- require sustained post-failure chain closure for several consecutive steps;
- evaluate recovery only after the system has first lost the chain.

These changes should be framed as task definition and evaluation hardening, not
as a new algorithm contribution.

