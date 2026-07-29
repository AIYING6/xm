# Dev-1M Fresh-Message Stress Diagnostic

Last updated: 2026-07-29

## Purpose

Test whether making target information less persistent increases dependence on
communication-mediated target updates.

This diagnostic evaluates frozen dev-1M validation-selected checkpoints. It is
not used for checkpoint selection or hyperparameter tuning.

## Protocol

```text
target_policy = straight
strict_target_sensing = true
agent_target_info_bottleneck = true
target_prior_position = (10000, 0, 5000)
max_target_message_age_steps = 20
communication_dropout_prob = 0.30
message_delay_steps = 2
failed_blue_agent = 1
node_failure_start_step = 40
node_failure_duration_steps = 80
episodes_per_seed = 30
base_seed = 240000
```

Methods:

- EA-RG-MAPPO
- Single-Graph MAPPO
- MAPPO/no-graph

## Seed-Level Results

| Seed | Method | Selected update | Success | Recovery | Censored recovery steps | Tracking during failure | Connectivity during failure | Timeout | Collision |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | EA-RG-MAPPO | 1600 | 0.2000 | 0.2000 | 180.0667 | 0.2284 | 0.1978 | 0.8000 | 0.0000 |
| 1 | EA-RG-MAPPO | 2200 | 0.4333 | 0.4333 | 148.7333 | 0.4740 | 0.1999 | 0.5667 | 0.0000 |
| 2 | EA-RG-MAPPO | 3800 | 0.0333 | 0.0333 | 213.5000 | 0.1662 | 0.1638 | 0.9667 | 0.0000 |
| 0 | Single-Graph | 3907 | 0.2333 | 0.2333 | 165.5667 | 0.4177 | 0.1733 | 0.7000 | 0.0667 |
| 1 | Single-Graph | 40 | 0.0000 | 0.0000 | 220.0000 | 0.0260 | 0.1110 | 1.0000 | 0.0000 |
| 2 | Single-Graph | 40 | 0.0000 | 0.0000 | 220.0000 | 0.1843 | 0.1565 | 1.0000 | 0.0000 |
| 0 | MAPPO/no-graph | 3800 | 0.0000 | 0.0000 | 220.0000 | 0.1742 | 0.1691 | 1.0000 | 0.0000 |
| 1 | MAPPO/no-graph | 2400 | 0.9667 | 0.9667 | 26.6333 | 0.4544 | 0.1485 | 0.0333 | 0.0000 |
| 2 | MAPPO/no-graph | 3907 | 0.0000 | 0.0000 | 220.0000 | 0.1333 | 0.0000 | 1.0000 | 0.0000 |

## Aggregate Results

| Method | Success mean | Success std | Recovery mean | Censored recovery mean | Tracking during failure | Connectivity during failure | Timeout | Collision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| EA-RG-MAPPO | 0.2222 | 0.2009 | 0.2222 | 180.7667 | 0.2895 | 0.1872 | 0.7778 | 0.0000 |
| Single-Graph | 0.0778 | 0.1347 | 0.0778 | 201.8556 | 0.2093 | 0.1469 | 0.9000 | 0.0222 |
| MAPPO/no-graph | 0.3222 | 0.5581 | 0.3222 | 155.5444 | 0.2540 | 0.1059 | 0.6778 | 0.0000 |

Machine-readable outputs:

- `results/paper_config_runs/dev_1m/fresh_message_stress/fresh20_dropout030_delay2_seed0_2/episode_summary.csv`
- `results/paper_config_runs/dev_1m/fresh_message_stress/fresh20_dropout030_delay2_seed0_2/aggregate_summary.csv`

## Interpretation

- This stress condition is too unstable to promote as a main scenario.
- EA-RG-MAPPO improves over Single-Graph on mean recovery, but not over
  MAPPO/no-graph because MAPPO seed 1 remains extremely strong (`0.9667`).
- Shortening message age plus dropout/delay suppresses some no-graph checkpoints
  but does not remove the no-graph seed-1 anomaly.
- The result reinforces the existing scientific warning: the current task still
  contains exploitable geometric regularities, and no-graph can sometimes solve
  the task without explicit graph communication.

## Decision

Do not use `fresh20_dropout030_delay2` as the final main scenario in its current
form.

Recommended next step:

1. Diagnose MAPPO/no-graph seed 1 trajectory behavior and observation/action
   pattern under the stress condition.
2. Compare successful MAPPO seed 1 episodes against failed MAPPO seed 0/2 and
   EA seed 1 to determine whether the no-graph success comes from geometric
   interception, target-cache use, or an environment shortcut.
3. Only after this diagnosis decide whether to modify the task, retrain under a
   stronger protocol, or narrow the paper claim.

