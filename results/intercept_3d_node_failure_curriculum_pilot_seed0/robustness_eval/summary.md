# 3DOF Topology Robustness Evaluation

Generated: 2026-07-16T12:25:00

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
| delay_2 | multi_relation | bc_ppo | 0.933 +/- 0.094 | 0.933 +/- 0.094 | 0.418 +/- 0.033 | 0.977 +/- 0.032 | 50.789 +/- 2.798 | 0.067 +/- 0.094 | 60.067 +/- 20.035 |
| delay_2 | single | bc_ppo | 0.867 +/- 0.094 | 0.867 +/- 0.094 | 0.396 +/- 0.034 | 0.951 +/- 0.035 | 41.499 +/- 2.412 | 0.133 +/- 0.094 | 74.267 +/- 19.988 |
| delay_5 | multi_relation | bc_ppo | 0.933 +/- 0.094 | 0.933 +/- 0.094 | 0.417 +/- 0.033 | 0.977 +/- 0.032 | 52.799 +/- 1.813 | 0.067 +/- 0.094 | 60.000 +/- 20.082 |
| delay_5 | single | bc_ppo | 0.933 +/- 0.094 | 0.933 +/- 0.094 | 0.420 +/- 0.034 | 0.973 +/- 0.038 | 44.176 +/- 1.222 | 0.067 +/- 0.094 | 60.067 +/- 20.035 |
| dropout_015 | multi_relation | bc_ppo | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 0.443 +/- 0.002 | 0.872 +/- 0.011 | 50.523 +/- 4.868 | 0.000 +/- 0.000 | 46.000 +/- 0.163 |
| dropout_015 | single | bc_ppo | 0.867 +/- 0.094 | 0.867 +/- 0.094 | 0.396 +/- 0.036 | 0.856 +/- 0.033 | 40.891 +/- 1.941 | 0.133 +/- 0.094 | 74.267 +/- 19.846 |
| dropout_030 | multi_relation | bc_ppo | 0.933 +/- 0.094 | 0.933 +/- 0.094 | 0.419 +/- 0.037 | 0.712 +/- 0.020 | 49.909 +/- 5.623 | 0.067 +/- 0.094 | 60.267 +/- 19.893 |
| dropout_030 | single | bc_ppo | 0.800 +/- 0.000 | 0.800 +/- 0.000 | 0.371 +/- 0.001 | 0.699 +/- 0.009 | 40.286 +/- 0.346 | 0.200 +/- 0.000 | 88.333 +/- 0.094 |
| nominal | multi_relation | bc_ppo | 0.933 +/- 0.094 | 0.933 +/- 0.094 | 0.418 +/- 0.033 | 0.972 +/- 0.039 | 49.269 +/- 2.727 | 0.067 +/- 0.094 | 60.067 +/- 20.035 |
| nominal | single | bc_ppo | 0.867 +/- 0.094 | 0.867 +/- 0.094 | 0.396 +/- 0.034 | 0.952 +/- 0.035 | 39.751 +/- 2.317 | 0.133 +/- 0.094 | 74.267 +/- 19.988 |
| radar_010 | multi_relation | bc_ppo | 0.933 +/- 0.094 | 0.933 +/- 0.094 | 0.373 +/- 0.027 | 0.977 +/- 0.032 | 49.154 +/- 2.832 | 0.067 +/- 0.094 | 60.067 +/- 20.035 |
| radar_010 | single | bc_ppo | 0.867 +/- 0.094 | 0.867 +/- 0.094 | 0.354 +/- 0.026 | 0.947 +/- 0.039 | 40.380 +/- 2.843 | 0.133 +/- 0.094 | 74.267 +/- 19.988 |
| radar_025 | multi_relation | bc_ppo | 0.933 +/- 0.094 | 0.933 +/- 0.094 | 0.309 +/- 0.027 | 0.982 +/- 0.026 | 48.603 +/- 3.130 | 0.067 +/- 0.094 | 60.200 +/- 19.941 |
| radar_025 | single | bc_ppo | 0.867 +/- 0.094 | 0.867 +/- 0.094 | 0.286 +/- 0.026 | 0.947 +/- 0.039 | 40.416 +/- 2.746 | 0.133 +/- 0.094 | 74.200 +/- 19.941 |
| range_050 | multi_relation | bc_ppo | 0.400 +/- 0.327 | 0.400 +/- 0.327 | 0.235 +/- 0.115 | 0.166 +/- 0.081 | 184.757 +/- 40.224 | 0.600 +/- 0.327 | 174.400 +/- 69.811 |
| range_050 | single | bc_ppo | 0.733 +/- 0.249 | 0.733 +/- 0.249 | 0.348 +/- 0.086 | 0.211 +/- 0.081 | 193.881 +/- 2.393 | 0.267 +/- 0.249 | 102.667 +/- 53.381 |
| range_075 | multi_relation | bc_ppo | 0.933 +/- 0.094 | 0.933 +/- 0.094 | 0.419 +/- 0.035 | 0.973 +/- 0.038 | 82.257 +/- 2.900 | 0.067 +/- 0.094 | 60.200 +/- 19.941 |
| range_075 | single | bc_ppo | 0.867 +/- 0.094 | 0.867 +/- 0.094 | 0.395 +/- 0.035 | 0.928 +/- 0.051 | 71.142 +/- 4.641 | 0.133 +/- 0.094 | 74.133 +/- 19.894 |
| relay_failure | multi_relation | bc_ppo | 0.933 +/- 0.094 | 0.933 +/- 0.094 | 0.418 +/- 0.034 | 0.889 +/- 0.037 | 49.620 +/- 2.681 | 0.067 +/- 0.094 | 60.067 +/- 20.035 |
| relay_failure | single | bc_ppo | 0.867 +/- 0.094 | 0.867 +/- 0.094 | 0.396 +/- 0.034 | 0.845 +/- 0.049 | 41.605 +/- 1.908 | 0.133 +/- 0.094 | 74.267 +/- 19.988 |
| scout_failure | multi_relation | bc_ppo | 0.933 +/- 0.094 | 0.933 +/- 0.094 | 0.418 +/- 0.033 | 0.876 +/- 0.055 | 51.368 +/- 2.268 | 0.067 +/- 0.094 | 60.067 +/- 20.035 |
| scout_failure | single | bc_ppo | 0.867 +/- 0.094 | 0.867 +/- 0.094 | 0.403 +/- 0.030 | 0.831 +/- 0.059 | 45.897 +/- 2.890 | 0.133 +/- 0.094 | 74.267 +/- 19.988 |

## Boundary

```text
A paper robustness claim requires matched training budgets, fixed evaluation seeds, and enough episodes per checkpoint-scenario.
Use small-episode runs for diagnostics only; reserve 30+ episode runs for formal tables.
```
