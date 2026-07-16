# 3DOF Topology Robustness Evaluation

Generated: 2026-07-16T20:42:07

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
graph_relation_ablation = none
graph_message_ablation = none
graph_input_ablation = none
scenarios = ['relay_failure', 'scout_failure']
target_policy = straight
strict_target_sensing = True
checkpoint_kind = actor_critic_best.pt
```

## Seed-Mean Summary

| Scenario | Graph | Train Method | Success | Chain | Tracking | Connectivity | Message Age | Timeout | Steps |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| relay_failure | multi_relation | bc_ppo | 0.867 +/- 0.094 | 0.867 +/- 0.094 | 0.396 +/- 0.032 | 0.846 +/- 0.051 | 50.200 +/- 2.167 | 0.133 +/- 0.094 | 74.133 +/- 20.177 |
| relay_failure | single | bc_ppo | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 0.442 +/- 0.001 | 0.918 +/- 0.000 | 41.465 +/- 2.371 | 0.000 +/- 0.000 | 45.600 +/- 0.000 |
| scout_failure | multi_relation | bc_ppo | 0.867 +/- 0.189 | 0.867 +/- 0.189 | 0.396 +/- 0.064 | 0.835 +/- 0.118 | 53.751 +/- 2.878 | 0.133 +/- 0.189 | 74.133 +/- 40.352 |
| scout_failure | single | bc_ppo | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 0.442 +/- 0.001 | 0.918 +/- 0.000 | 41.465 +/- 2.371 | 0.000 +/- 0.000 | 45.600 +/- 0.000 |

## Boundary

```text
A paper robustness claim requires matched training budgets, fixed evaluation seeds, and enough episodes per checkpoint-scenario.
Use small-episode runs for diagnostics only; reserve 30+ episode runs for formal tables.
```
