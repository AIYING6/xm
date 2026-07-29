# Dropout030 Delay2 Early Relay-Failure Validation Summary

Last updated: 2026-07-28

## Protocol

Validation checkpoint selection was completed for regular MAPPO-family methods:

```text
scenario = dropout030_delay2_relay_failure_early
split = validation
seeds = 0, 1, 2
episodes = 50 per checkpoint
target_policy = straight
strict_target_sensing = true
agent_target_info_bottleneck = true
communication dropout = 0.30
message delay = 2 steps
max target message age = 80
min target confidence = 0.2
zero-collision selection constraint = true
```

Output directory:

```text
results/paper_config_runs/dev_1m/checkpoint_sweeps/dropout030_delay2_relay_failure_early_seed0_2_validation/
```

## Selected Checkpoints

| Method | Seed | Selected Update | Success/Recovery | Recovery Steps | Collision |
| --- | ---: | ---: | ---: | ---: | ---: |
| MAPPO/no-graph | 0 | 3400 | 0.62 | 34.2258 | 0.00 |
| MAPPO/no-graph | 1 | 3060 | 0.48 | 70.0417 | 0.00 |
| MAPPO/no-graph | 2 | 3907 | 0.00 | inf | 0.00 |
| Single-Graph MAPPO | 0 | 1800 | 0.60 | 25.2333 | 0.00 |
| Single-Graph MAPPO | 1 | 200 | 0.32 | 35.8125 | 0.00 |
| Single-Graph MAPPO | 2 | 2560 | 0.66 | 38.3030 | 0.00 |
| EA-RG-MAPPO | 0 | 100 | 0.28 | 26.0000 | 0.00 |
| EA-RG-MAPPO | 1 | 1200 | 0.72 | 38.2222 | 0.00 |
| EA-RG-MAPPO | 2 | 2900 | 0.42 | 39.0476 | 0.00 |

## Aggregate

| Method | Mean Success/Recovery | Min | Max | Collision Mean |
| --- | ---: | ---: | ---: | ---: |
| MAPPO/no-graph | 0.3667 | 0.00 | 0.62 | 0.00 |
| Single-Graph MAPPO | 0.5267 | 0.32 | 0.66 | 0.00 |
| EA-RG-MAPPO | 0.4733 | 0.28 | 0.72 | 0.00 |

## Interpretation

The early relay-failure stress scenario is more diagnostic than the original
nominal relay-failure setting, but it does not support promoting EA-RG-MAPPO as
the final main result.

Useful findings:

- EA-RG-MAPPO improves over MAPPO/no-graph by `+0.1066` mean
  success/recovery.
- EA-RG-MAPPO avoids the zero-success seed seen in no-graph.
- EA seed1 is strong (`0.72`) and clearly beats Single seed1 (`0.32`).

Blocking finding:

- Single-Graph MAPPO remains stronger overall: `0.5267` vs EA-RG-MAPPO
  `0.4733`.
- EA seed0 is weak (`0.28`) compared with both no-graph seed0 (`0.62`) and
  Single seed0 (`0.60`).

## Decision

Do not promote `dropout030_delay2_relay_failure_early` to held-out testing as
the final main scenario.

The result should be kept as development evidence:

- early relay failure increases difficulty;
- graph-based methods are useful relative to no-graph;
- current EA-RG-MAPPO is not consistently stronger than Single-Graph.

## Next Step

Stop searching for another hand-picked stress scenario.

Next priority is to diagnose and improve why EA-RG-MAPPO underperforms
Single-Graph in some seeds while outperforming it in others. Recommended order:

1. compare EA seed0 and seed1 trajectories/metrics under the early scenario;
2. inspect relation attention, task-support usage, tracking, connectivity, and
   message age for the selected checkpoints;
3. check whether EA has higher variance because multi-relation attention
   overfits early checkpoints;
4. if supported by diagnostics, tune the existing training protocol rather than
   adding another architectural module.

