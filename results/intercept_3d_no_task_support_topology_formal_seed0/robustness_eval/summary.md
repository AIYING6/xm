# 3DOF Topology Robustness Evaluation

Generated: 2026-07-16T13:59:01

Purpose:

```text
Evaluate saved 3DOF checkpoints under communication range compression, dropout, delay, radar dropout, and temporary communication-node failure.
When the checkpoints are nominally trained, use this as scenario screening; when they are topology-curriculum trained, use it as a matched robustness diagnostic.
```

## Configuration

```text
episodes_per_checkpoint_scenario = 30
training_seeds = [0]
train_methods = ['bc_ppo']
graph_encoders = ['multi_relation']
graph_relation_ablation = no_task_support
scenarios = ['relay_failure', 'scout_failure']
target_policy = straight
checkpoint_kind = actor_critic_best.pt
```

## Seed-Mean Summary

| Scenario | Graph | Train Method | Success | Chain | Tracking | Connectivity | Message Age | Timeout | Steps |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| relay_failure | multi_relation | bc_ppo | 0.900 +/- 0.000 | 0.900 +/- 0.000 | 0.402 +/- 0.000 | 0.862 +/- 0.000 | 45.737 +/- 0.000 | 0.100 +/- 0.000 | 66.733 +/- 0.000 |
| scout_failure | multi_relation | bc_ppo | 0.867 +/- 0.000 | 0.867 +/- 0.000 | 0.389 +/- 0.000 | 0.840 +/- 0.000 | 47.675 +/- 0.000 | 0.133 +/- 0.000 | 73.767 +/- 0.000 |

## Boundary

```text
A paper robustness claim requires matched training budgets, fixed evaluation seeds, and enough episodes per checkpoint-scenario.
Use small-episode runs for diagnostics only; reserve 30+ episode runs for formal tables.
```
