# 3DOF Topology Robustness Evaluation

Generated: 2026-07-16T18:20:30

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
graph_relation_ablation = none
graph_message_ablation = none
graph_input_ablation = no_role_identity
scenarios = ['relay_failure', 'scout_failure']
target_policy = straight
checkpoint_kind = actor_critic_best.pt
```

## Seed-Mean Summary

| Scenario | Graph | Train Method | Success | Chain | Tracking | Connectivity | Message Age | Timeout | Steps |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| relay_failure | multi_relation | bc_ppo | 0.978 +/- 0.016 | 0.978 +/- 0.016 | 0.433 +/- 0.010 | 0.905 +/- 0.004 | 47.450 +/- 2.096 | 0.022 +/- 0.016 | 50.500 +/- 2.925 |
| scout_failure | multi_relation | bc_ppo | 0.978 +/- 0.016 | 0.978 +/- 0.016 | 0.433 +/- 0.010 | 0.903 +/- 0.006 | 48.254 +/- 2.649 | 0.022 +/- 0.016 | 50.467 +/- 2.949 |

## Boundary

```text
A paper robustness claim requires matched training budgets, fixed evaluation seeds, and enough episodes per checkpoint-scenario.
Use small-episode runs for diagnostics only; reserve 30+ episode runs for formal tables.
```
