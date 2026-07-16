# 3DOF Topology Robustness Evaluation

Generated: 2026-07-16T11:36:13

Purpose:

```text
Zero-shot evaluation of existing 3DOF checkpoints under communication range compression, dropout, delay, radar dropout, and temporary communication-node failure.
This identifies the topology disruptions worth using for staged retraining; it is not yet a topology-curriculum training result.
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
| delay_2 | multi_relation | bc_ppo | 0.867 +/- 0.189 | 0.867 +/- 0.189 | 0.400 +/- 0.067 | 0.955 +/- 0.064 | 48.721 +/- 2.974 | 0.133 +/- 0.189 | 74.467 +/- 40.117 |
| delay_2 | single | bc_ppo | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 0.446 +/- 0.001 | 1.000 +/- 0.000 | 43.952 +/- 2.085 | 0.000 +/- 0.000 | 45.933 +/- 0.094 |
| delay_5 | multi_relation | bc_ppo | 0.867 +/- 0.189 | 0.867 +/- 0.189 | 0.399 +/- 0.068 | 0.955 +/- 0.064 | 50.907 +/- 2.603 | 0.133 +/- 0.189 | 74.400 +/- 40.164 |
| delay_5 | single | bc_ppo | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 0.446 +/- 0.001 | 1.000 +/- 0.000 | 46.464 +/- 2.060 | 0.000 +/- 0.000 | 45.933 +/- 0.094 |
| dropout_015 | multi_relation | bc_ppo | 0.933 +/- 0.094 | 0.933 +/- 0.094 | 0.426 +/- 0.035 | 0.843 +/- 0.033 | 48.027 +/- 3.031 | 0.067 +/- 0.094 | 60.467 +/- 19.894 |
| dropout_015 | single | bc_ppo | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 0.448 +/- 0.002 | 0.879 +/- 0.002 | 42.218 +/- 3.977 | 0.000 +/- 0.000 | 46.067 +/- 0.189 |
| dropout_030 | multi_relation | bc_ppo | 0.933 +/- 0.094 | 0.933 +/- 0.094 | 0.426 +/- 0.033 | 0.714 +/- 0.029 | 47.667 +/- 2.876 | 0.067 +/- 0.094 | 60.533 +/- 20.129 |
| dropout_030 | single | bc_ppo | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 0.449 +/- 0.002 | 0.741 +/- 0.008 | 42.769 +/- 4.648 | 0.000 +/- 0.000 | 46.133 +/- 0.249 |
| nominal | multi_relation | bc_ppo | 0.867 +/- 0.189 | 0.867 +/- 0.189 | 0.400 +/- 0.068 | 0.961 +/- 0.055 | 46.804 +/- 3.606 | 0.133 +/- 0.189 | 74.467 +/- 40.117 |
| nominal | single | bc_ppo | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 0.446 +/- 0.001 | 1.000 +/- 0.000 | 42.403 +/- 2.215 | 0.000 +/- 0.000 | 45.933 +/- 0.094 |
| radar_010 | multi_relation | bc_ppo | 0.933 +/- 0.094 | 0.933 +/- 0.094 | 0.388 +/- 0.031 | 0.984 +/- 0.022 | 48.506 +/- 1.406 | 0.067 +/- 0.094 | 60.200 +/- 20.084 |
| radar_010 | single | bc_ppo | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 0.399 +/- 0.003 | 1.000 +/- 0.000 | 42.403 +/- 2.215 | 0.000 +/- 0.000 | 45.933 +/- 0.094 |
| radar_025 | multi_relation | bc_ppo | 0.733 +/- 0.249 | 0.733 +/- 0.249 | 0.269 +/- 0.063 | 0.901 +/- 0.080 | 44.769 +/- 4.945 | 0.267 +/- 0.249 | 103.467 +/- 52.955 |
| radar_025 | single | bc_ppo | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 0.336 +/- 0.001 | 1.000 +/- 0.000 | 41.801 +/- 2.315 | 0.000 +/- 0.000 | 46.333 +/- 0.377 |
| range_050 | multi_relation | bc_ppo | 0.533 +/- 0.340 | 0.533 +/- 0.340 | 0.283 +/- 0.117 | 0.182 +/- 0.023 | 185.249 +/- 31.344 | 0.467 +/- 0.340 | 145.667 +/- 72.746 |
| range_050 | single | bc_ppo | 0.733 +/- 0.377 | 0.733 +/- 0.377 | 0.351 +/- 0.129 | 0.182 +/- 0.064 | 198.637 +/- 16.783 | 0.267 +/- 0.377 | 102.733 +/- 80.799 |
| range_075 | multi_relation | bc_ppo | 0.800 +/- 0.283 | 0.800 +/- 0.283 | 0.378 +/- 0.103 | 0.923 +/- 0.108 | 76.628 +/- 10.057 | 0.200 +/- 0.283 | 88.800 +/- 60.105 |
| range_075 | single | bc_ppo | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 0.446 +/- 0.001 | 1.000 +/- 0.000 | 77.007 +/- 4.232 | 0.000 +/- 0.000 | 45.933 +/- 0.094 |
| relay_failure | multi_relation | bc_ppo | 0.933 +/- 0.094 | 0.933 +/- 0.094 | 0.425 +/- 0.032 | 0.874 +/- 0.055 | 50.341 +/- 1.442 | 0.067 +/- 0.094 | 60.400 +/- 20.225 |
| relay_failure | single | bc_ppo | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 0.446 +/- 0.000 | 0.914 +/- 0.001 | 42.711 +/- 2.224 | 0.000 +/- 0.000 | 45.933 +/- 0.094 |
| scout_failure | multi_relation | bc_ppo | 0.800 +/- 0.283 | 0.800 +/- 0.283 | 0.377 +/- 0.101 | 0.819 +/- 0.132 | 49.291 +/- 0.836 | 0.200 +/- 0.283 | 88.667 +/- 60.199 |
| scout_failure | single | bc_ppo | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 0.446 +/- 0.001 | 0.914 +/- 0.001 | 42.711 +/- 2.224 | 0.000 +/- 0.000 | 45.933 +/- 0.094 |

## Boundary

```text
These rows reuse nominally trained checkpoints. A paper robustness claim still requires matched topology-curriculum retraining and a final fixed evaluation suite.
Use this table to select disruption levels that are neither saturated nor trivial.
```
