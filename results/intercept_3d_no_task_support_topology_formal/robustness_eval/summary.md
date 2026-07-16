# 3DOF Topology Robustness Evaluation

Generated: 2026-07-16T14:18:44

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
graph_encoders = ['multi_relation']
graph_relation_ablation = no_task_support
scenarios = ['relay_failure', 'scout_failure']
target_policy = straight
checkpoint_kind = actor_critic_best.pt
```

## Seed-Mean Summary

| Scenario | Graph | Train Method | Success | Chain | Tracking | Connectivity | Message Age | Timeout | Steps |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| relay_failure | multi_relation | bc_ppo | 0.889 +/- 0.096 | 0.889 +/- 0.096 | 0.398 +/- 0.032 | 0.874 +/- 0.036 | 43.889 +/- 1.889 | 0.111 +/- 0.096 | 69.167 +/- 20.553 |
| scout_failure | multi_relation | bc_ppo | 0.878 +/- 0.096 | 0.878 +/- 0.096 | 0.394 +/- 0.032 | 0.869 +/- 0.038 | 44.439 +/- 2.606 | 0.122 +/- 0.096 | 71.511 +/- 20.542 |

## Boundary

```text
A paper robustness claim requires matched training budgets, fixed evaluation seeds, and enough episodes per checkpoint-scenario.
Use small-episode runs for diagnostics only; reserve 30+ episode runs for formal tables.
```
