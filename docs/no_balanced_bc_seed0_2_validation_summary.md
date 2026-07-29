# No-Balanced BC Seed 0-2 PPO Validation Summary

Last updated: 2026-07-29

## Purpose

This document summarizes the three-seed development repeat of the no-balanced
BC protocol under strict early-stress conditions:

```text
target_policy = straight
strict_target_sensing = true
agent_target_info_bottleneck = true
communication_dropout_prob = 0.30
message_delay_steps = 2
failed_blue_agent = 1
node_failure_start_step = 25
node_failure_duration_steps = 80
BC demonstrations = 200 direct geometric-oracle episodes
BC loss = unbalanced cross entropy
PPO updates = 100
candidate checkpoints = update 30, update 40, update 70
validation episodes = 50 matched episodes
validation base_seed = 140000
```

This is development evidence only. It is used to decide whether the
no-balanced BC protocol should replace the earlier balanced BC starting point
before any 1M/2M-scale paper run.

## Artifacts

Machine-readable summaries:

- `results/paper_config_runs/no_balanced_bc_dev/validation_eval50_seed0_2_common_candidates_summary.csv`
- `results/paper_config_runs/no_balanced_bc_dev/validation_eval50_seed0_2_selected_summary.csv`
- `results/paper_config_runs/no_balanced_bc_dev/validation_eval50_seed0_2_selected_aggregate.csv`

Per-seed evaluation folders:

- `results/paper_config_runs/no_balanced_bc_dev/validation_eval50_seed0/`
- `results/paper_config_runs/no_balanced_bc_dev/validation_eval50_seed1/`
- `results/paper_config_runs/no_balanced_bc_dev/validation_eval50_seed2/`

## Selected Checkpoints

Selection rule: maximize validation success/recovery, then prefer lower
censored recovery time, lower timeout, and earlier update.

| Seed | Method | Selected update | Success | Recovery | Censored recovery steps | Tracking during failure | Connectivity during failure | Timeout | Collision |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | EA-RG-MAPPO | 40 | 0.4400 | 0.4400 | 140.3000 | 0.5001 | 0.1211 | 0.5600 | 0.0000 |
| 0 | Single-Graph | 70 | 0.3800 | 0.3800 | 153.2200 | 0.4423 | 0.1809 | 0.6200 | 0.0000 |
| 0 | MAPPO/no-graph | 70 | 0.3400 | 0.3400 | 161.8800 | 0.4469 | 0.0988 | 0.6600 | 0.0000 |
| 1 | EA-RG-MAPPO | 30 | 0.3400 | 0.3400 | 157.8600 | 0.4548 | 0.0983 | 0.6400 | 0.0200 |
| 1 | Single-Graph | 70 | 0.3400 | 0.3400 | 161.8600 | 0.4259 | 0.1003 | 0.6600 | 0.0000 |
| 1 | MAPPO/no-graph | 70 | 0.3400 | 0.3400 | 161.8600 | 0.4482 | 0.1000 | 0.6600 | 0.0000 |
| 2 | EA-RG-MAPPO | 40 | 0.3400 | 0.3400 | 161.8400 | 0.4477 | 0.1003 | 0.6600 | 0.0000 |
| 2 | Single-Graph | 40 | 0.3400 | 0.3400 | 161.8600 | 0.4453 | 0.1597 | 0.6600 | 0.0000 |
| 2 | MAPPO/no-graph | 30 | 0.3400 | 0.3400 | 161.8800 | 0.4485 | 0.1000 | 0.6600 | 0.0000 |

## Aggregate

| Method | Selected updates | Success mean | Success std | Recovery mean | Censored recovery mean | Tracking during failure | Connectivity during failure | Timeout mean |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| EA-RG-MAPPO | 40/30/40 | 0.3733 | 0.0577 | 0.3733 | 153.3333 | 0.4675 | 0.1066 | 0.6200 |
| Single-Graph | 70/70/40 | 0.3533 | 0.0231 | 0.3533 | 158.9800 | 0.4378 | 0.1470 | 0.6467 |
| MAPPO/no-graph | 70/70/30 | 0.3400 | 0.0000 | 0.3400 | 161.8733 | 0.4478 | 0.0996 | 0.6600 |

## Interpretation

- No-balanced BC is a better development protocol than balanced BC because it
  gives all methods usable starting policies under strict sensing and early
  relay failure.
- The protocol does not by itself prove the proposed method. MAPPO/no-graph is
  strong at the BC-only stage, and after 100 PPO updates the three methods are
  still close.
- EA-RG-MAPPO has the best three-seed mean validation success/recovery
  (`0.3733`), but the margin over Single-Graph (`+0.0200`) and MAPPO/no-graph
  (`+0.0333`) is too small for a paper-level method claim.
- The seed-1 EA selected checkpoint has a small collision rate (`0.0200`), so
  collision/safety must remain part of checkpoint selection and final testing.
- Online 5-episode training monitors are too noisy: several update-70 online
  peaks at `0.8` collapsed to about `0.34` on the fixed 50-episode validation
  split.

## Decision

Do not promote this 100-update no-balanced BC protocol directly to formal paper
evidence.

Use it as a development lesson:

1. Keep no-balanced BC as the preferred initialization option when running
   short strict-stress diagnostics.
2. Do not claim task-support or role-pair gate as a strong mechanism unless a
   controlled ablation produces clear degradation.
3. Before any 1M/2M launch from this branch, strengthen the mechanism or task
   dependence on role-conditioned communication, then repeat the same
   seed-aware validation procedure.

