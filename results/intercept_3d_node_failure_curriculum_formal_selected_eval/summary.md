# 3DOF Topology Robustness Evaluation

Generated: 2026-07-16T12:33:38

Purpose:

```text
Evaluate saved 3DOF checkpoints under communication range compression, dropout, delay, radar dropout, and temporary communication-node failure.
When the checkpoints are nominally trained, use this as scenario screening; when they are topology-curriculum trained, use it as a matched robustness diagnostic.
```

## Configuration

```text
episodes_per_checkpoint_scenario = 30
training_seeds = [0, 1, 2]
train_methods = ['bc_ppo']
graph_encoders = ['single', 'multi_relation']
scenarios = ['dropout_030', 'radar_025', 'range_075', 'delay_2']
target_policy = straight
checkpoint_kind = actor_critic_best.pt
```

## Seed-Mean Summary

| Scenario | Graph | Train Method | Success | Chain | Tracking | Connectivity | Message Age | Timeout | Steps |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| delay_2 | multi_relation | bc_ppo | 0.967 +/- 0.047 | 0.967 +/- 0.047 | 0.427 +/- 0.016 | 0.988 +/- 0.017 | 53.029 +/- 3.647 | 0.033 +/- 0.047 | 52.644 +/- 10.080 |
| delay_2 | single | bc_ppo | 0.944 +/- 0.016 | 0.944 +/- 0.016 | 0.418 +/- 0.007 | 0.982 +/- 0.003 | 42.344 +/- 2.338 | 0.056 +/- 0.016 | 57.156 +/- 3.268 |
| dropout_030 | multi_relation | bc_ppo | 0.967 +/- 0.027 | 0.967 +/- 0.027 | 0.427 +/- 0.013 | 0.715 +/- 0.017 | 50.023 +/- 6.451 | 0.033 +/- 0.027 | 52.667 +/- 5.579 |
| dropout_030 | single | bc_ppo | 0.933 +/- 0.027 | 0.933 +/- 0.027 | 0.414 +/- 0.009 | 0.728 +/- 0.014 | 41.832 +/- 2.242 | 0.067 +/- 0.027 | 59.544 +/- 5.824 |
| radar_025 | multi_relation | bc_ppo | 0.944 +/- 0.079 | 0.944 +/- 0.079 | 0.317 +/- 0.018 | 0.983 +/- 0.025 | 50.939 +/- 4.163 | 0.056 +/- 0.079 | 57.444 +/- 16.727 |
| radar_025 | single | bc_ppo | 0.922 +/- 0.031 | 0.922 +/- 0.031 | 0.305 +/- 0.010 | 0.974 +/- 0.012 | 40.377 +/- 2.054 | 0.078 +/- 0.031 | 61.967 +/- 6.694 |
| range_075 | multi_relation | bc_ppo | 0.944 +/- 0.079 | 0.944 +/- 0.079 | 0.420 +/- 0.028 | 0.974 +/- 0.037 | 83.781 +/- 2.352 | 0.056 +/- 0.079 | 57.456 +/- 16.696 |
| range_075 | single | bc_ppo | 0.967 +/- 0.027 | 0.967 +/- 0.027 | 0.425 +/- 0.010 | 0.984 +/- 0.012 | 73.034 +/- 4.480 | 0.033 +/- 0.027 | 52.411 +/- 5.743 |

## Boundary

```text
A paper robustness claim requires matched training budgets, fixed evaluation seeds, and enough episodes per checkpoint-scenario.
Use small-episode runs for diagnostics only; reserve 30+ episode runs for formal tables.
```
