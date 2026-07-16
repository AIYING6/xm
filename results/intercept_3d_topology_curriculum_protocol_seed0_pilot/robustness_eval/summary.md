# 3DOF Topology Robustness Evaluation

Generated: 2026-07-16T12:16:13

Purpose:

```text
Evaluate saved 3DOF checkpoints under communication range compression, dropout, delay, radar dropout, and temporary communication-node failure.
When the checkpoints are nominally trained, use this as scenario screening; when they are topology-curriculum trained, use it as a matched robustness diagnostic.
```

## Configuration

```text
episodes_per_checkpoint_scenario = 5
training_seeds = [0, 1, 2]
train_methods = ['bc_ppo']
graph_encoders = ['single', 'multi_relation']
scenarios = ['nominal', 'range_075', 'range_050', 'dropout_015', 'dropout_030', 'delay_2', 'delay_5', 'radar_010', 'radar_025', 'relay_failure', 'scout_failure']
target_policy = straight
checkpoint_kind = actor_critic_best.pt
```

## Seed-Mean Summary

| Scenario | Graph | Train Method | Success | Chain | Tracking | Connectivity | Message Age | Timeout | Steps |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| delay_2 | multi_relation | bc_ppo | 0.933 +/- 0.094 | 0.933 +/- 0.094 | 0.418 +/- 0.033 | 0.970 +/- 0.042 | 50.025 +/- 3.860 | 0.067 +/- 0.094 | 60.000 +/- 20.082 |
| delay_2 | single | bc_ppo | 0.933 +/- 0.094 | 0.933 +/- 0.094 | 0.418 +/- 0.032 | 0.981 +/- 0.027 | 41.374 +/- 1.564 | 0.067 +/- 0.094 | 59.933 +/- 20.129 |
| delay_5 | multi_relation | bc_ppo | 0.933 +/- 0.094 | 0.933 +/- 0.094 | 0.417 +/- 0.033 | 0.973 +/- 0.038 | 52.078 +/- 3.848 | 0.067 +/- 0.094 | 59.933 +/- 20.129 |
| delay_5 | single | bc_ppo | 0.933 +/- 0.094 | 0.933 +/- 0.094 | 0.418 +/- 0.032 | 0.981 +/- 0.027 | 43.573 +/- 1.825 | 0.067 +/- 0.094 | 59.933 +/- 20.129 |
| dropout_015 | multi_relation | bc_ppo | 0.933 +/- 0.094 | 0.933 +/- 0.094 | 0.419 +/- 0.031 | 0.852 +/- 0.027 | 48.572 +/- 5.915 | 0.067 +/- 0.094 | 60.200 +/- 20.365 |
| dropout_015 | single | bc_ppo | 0.933 +/- 0.094 | 0.933 +/- 0.094 | 0.419 +/- 0.033 | 0.881 +/- 0.018 | 39.831 +/- 1.685 | 0.067 +/- 0.094 | 60.000 +/- 20.082 |
| dropout_030 | multi_relation | bc_ppo | 0.933 +/- 0.094 | 0.933 +/- 0.094 | 0.419 +/- 0.034 | 0.707 +/- 0.019 | 49.628 +/- 7.245 | 0.067 +/- 0.094 | 60.267 +/- 20.036 |
| dropout_030 | single | bc_ppo | 0.933 +/- 0.094 | 0.933 +/- 0.094 | 0.419 +/- 0.033 | 0.740 +/- 0.022 | 39.274 +/- 2.281 | 0.067 +/- 0.094 | 60.000 +/- 20.082 |
| nominal | multi_relation | bc_ppo | 0.933 +/- 0.094 | 0.933 +/- 0.094 | 0.418 +/- 0.033 | 0.970 +/- 0.043 | 48.444 +/- 3.838 | 0.067 +/- 0.094 | 60.000 +/- 20.082 |
| nominal | single | bc_ppo | 0.933 +/- 0.094 | 0.933 +/- 0.094 | 0.418 +/- 0.032 | 0.983 +/- 0.023 | 39.847 +/- 1.673 | 0.067 +/- 0.094 | 59.933 +/- 20.129 |
| radar_010 | multi_relation | bc_ppo | 0.933 +/- 0.094 | 0.933 +/- 0.094 | 0.368 +/- 0.027 | 0.977 +/- 0.032 | 48.076 +/- 4.264 | 0.067 +/- 0.094 | 60.000 +/- 20.082 |
| radar_010 | single | bc_ppo | 0.933 +/- 0.094 | 0.933 +/- 0.094 | 0.371 +/- 0.026 | 0.983 +/- 0.023 | 39.847 +/- 1.673 | 0.067 +/- 0.094 | 59.933 +/- 20.129 |
| radar_025 | multi_relation | bc_ppo | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 0.319 +/- 0.007 | 1.000 +/- 0.000 | 48.581 +/- 3.525 | 0.000 +/- 0.000 | 46.000 +/- 0.163 |
| radar_025 | single | bc_ppo | 0.933 +/- 0.094 | 0.933 +/- 0.094 | 0.306 +/- 0.026 | 0.985 +/- 0.021 | 39.776 +/- 1.628 | 0.067 +/- 0.094 | 59.933 +/- 20.129 |
| range_050 | multi_relation | bc_ppo | 0.400 +/- 0.327 | 0.400 +/- 0.327 | 0.233 +/- 0.114 | 0.181 +/- 0.026 | 178.339 +/- 27.190 | 0.600 +/- 0.327 | 174.200 +/- 70.055 |
| range_050 | single | bc_ppo | 0.733 +/- 0.249 | 0.733 +/- 0.249 | 0.372 +/- 0.099 | 0.228 +/- 0.112 | 191.176 +/- 14.258 | 0.200 +/- 0.283 | 89.600 +/- 59.694 |
| range_075 | multi_relation | bc_ppo | 0.933 +/- 0.094 | 0.933 +/- 0.094 | 0.419 +/- 0.034 | 0.967 +/- 0.046 | 80.982 +/- 3.879 | 0.067 +/- 0.094 | 60.133 +/- 19.988 |
| range_075 | single | bc_ppo | 0.933 +/- 0.094 | 0.933 +/- 0.094 | 0.417 +/- 0.032 | 0.979 +/- 0.029 | 70.825 +/- 4.094 | 0.067 +/- 0.094 | 59.867 +/- 20.176 |
| relay_failure | multi_relation | bc_ppo | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 0.443 +/- 0.002 | 0.914 +/- 0.002 | 48.957 +/- 3.598 | 0.000 +/- 0.000 | 45.933 +/- 0.189 |
| relay_failure | single | bc_ppo | 0.933 +/- 0.094 | 0.933 +/- 0.094 | 0.418 +/- 0.032 | 0.885 +/- 0.046 | 40.995 +/- 2.479 | 0.067 +/- 0.094 | 59.933 +/- 20.129 |
| scout_failure | multi_relation | bc_ppo | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 0.442 +/- 0.001 | 0.914 +/- 0.002 | 48.957 +/- 3.598 | 0.000 +/- 0.000 | 45.933 +/- 0.189 |
| scout_failure | single | bc_ppo | 0.933 +/- 0.094 | 0.933 +/- 0.094 | 0.418 +/- 0.032 | 0.885 +/- 0.046 | 40.995 +/- 2.479 | 0.067 +/- 0.094 | 59.933 +/- 20.129 |

## Boundary

```text
A paper robustness claim requires matched training budgets, fixed evaluation seeds, and enough episodes per checkpoint-scenario.
Use small-episode runs for diagnostics only; reserve 30+ episode runs for formal tables.
```
