# Delayed-Recovery MAPPO Seed-1 Candidate Sweep

Last updated: 2026-07-29

## Purpose

Check whether delayed-recovery checkpoint selection changes the interpretation
of the anomalously strong MAPPO/no-graph seed-1 run.

## Protocol

```text
method = MAPPO/no-graph
train_seed = 1
candidate_updates = 2000, 2060, 2100, 2200, 2300
scenario = dropout030_delay2_relay_failure
max_target_message_age_steps = 20
selection_metric = delayed_recovery
delayed_recovery_min_step = 80
episodes = 10
base_seed = 260000
```

Outputs:

- `results/paper_config_runs/dev_1m/delayed_recovery_sweep_mappo_seed1_u2000_2400/`
- `results/paper_config_runs/dev_1m/delayed_recovery_sweep_mappo_seed1_u2000_2400_success0/`

## Results

| Update | Legacy recovery | Delayed recovery >= 80 | Success | Score, success weight 100 | Score, success weight 0 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 2000 | 0.0000 | 0.0000 | 0.0000 | -1000 | -1000 |
| 2060 | 0.0000 | 0.0000 | 0.0000 | -1000 | -1000 |
| 2100 | 0.0000 | 0.0000 | 0.0000 | -1000 | -1000 |
| 2200 | 0.0000 | 0.0000 | 0.0000 | -1000 | -1000 |
| 2300 | 0.8000 | 0.0000 | 0.8000 | -920 | -1000 |

## Interpretation

- The update-2300 checkpoint has strong legacy recovery and success, but zero
  delayed recovery at threshold `80`.
- With `selection_success_weight=100`, early success still improves the delayed
  selection score from `-1000` to `-920`.
- With `selection_success_weight=0`, all candidates have the same score
  (`-1000`) because none shows delayed recovery.
- Therefore this MAPPO/no-graph seed-1 sweep confirms that the anomaly is not a
  useful delayed-recovery policy.

## Decision

For future strict delayed-recovery checkpoint selection:

```text
--selection-metric delayed_recovery
--delayed-recovery-min-step 80
--selection-success-weight 0
```

If all candidate checkpoints have zero delayed recovery, do not treat the
selected checkpoint as meaningful. Treat the run as a failed delayed-recovery
training seed.

