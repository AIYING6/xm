# 3DOF Topology Robustness Evaluation

Generated: 2026-07-16T12:13:31

Purpose:

```text
Evaluate saved 3DOF checkpoints under communication range compression, dropout, delay, radar dropout, and temporary communication-node failure.
When the checkpoints are nominally trained, use this as scenario screening; when they are topology-curriculum trained, use it as a matched robustness diagnostic.
```

## Configuration

```text
episodes_per_checkpoint_scenario = 1
training_seeds = [0]
train_methods = ['bc_ppo']
graph_encoders = ['multi_relation']
scenarios = ['relay_failure', 'scout_failure']
target_policy = straight
checkpoint_kind = actor_critic_best.pt
```

## Seed-Mean Summary

| Scenario | Graph | Train Method | Success | Chain | Tracking | Connectivity | Message Age | Timeout | Steps |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| relay_failure | multi_relation | bc_ppo | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 0.417 +/- 0.000 | 0.939 +/- 0.000 | 47.424 +/- 0.000 | 0.000 +/- 0.000 | 44.000 +/- 0.000 |
| scout_failure | multi_relation | bc_ppo | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 0.417 +/- 0.000 | 0.939 +/- 0.000 | 47.424 +/- 0.000 | 0.000 +/- 0.000 | 44.000 +/- 0.000 |

## Boundary

```text
A paper robustness claim requires matched training budgets, fixed evaluation seeds, and enough episodes per checkpoint-scenario.
Use small-episode runs for diagnostics only; reserve 30+ episode runs for formal tables.
```
