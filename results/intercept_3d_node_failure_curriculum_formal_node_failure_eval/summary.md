# 3DOF Topology Robustness Evaluation

Generated: 2026-07-16T12:49:27

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
scenarios = ['relay_failure', 'scout_failure']
target_policy = straight
checkpoint_kind = actor_critic_best.pt
```

## Seed-Mean Summary

| Scenario | Graph | Train Method | Success | Chain | Tracking | Connectivity | Message Age | Timeout | Steps |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| relay_failure | multi_relation | bc_ppo | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 0.439 +/- 0.002 | 0.918 +/- 0.002 | 51.969 +/- 3.465 | 0.000 +/- 0.000 | 45.644 +/- 0.206 |
| relay_failure | single | bc_ppo | 0.922 +/- 0.016 | 0.922 +/- 0.016 | 0.408 +/- 0.005 | 0.886 +/- 0.001 | 41.913 +/- 1.592 | 0.078 +/- 0.016 | 61.822 +/- 3.378 |
| scout_failure | multi_relation | bc_ppo | 0.967 +/- 0.047 | 0.967 +/- 0.047 | 0.427 +/- 0.016 | 0.901 +/- 0.027 | 51.927 +/- 3.487 | 0.033 +/- 0.047 | 52.689 +/- 10.143 |
| scout_failure | single | bc_ppo | 0.944 +/- 0.016 | 0.944 +/- 0.016 | 0.416 +/- 0.006 | 0.893 +/- 0.007 | 42.567 +/- 1.953 | 0.056 +/- 0.016 | 57.133 +/- 3.347 |

## Boundary

```text
A paper robustness claim requires matched training budgets, fixed evaluation seeds, and enough episodes per checkpoint-scenario.
Use small-episode runs for diagnostics only; reserve 30+ episode runs for formal tables.
```
