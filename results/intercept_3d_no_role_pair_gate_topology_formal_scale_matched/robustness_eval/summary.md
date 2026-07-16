# 3DOF Topology Robustness Evaluation

Generated: 2026-07-16T15:25:27

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
graph_message_ablation = no_role_pair_gate
scenarios = ['relay_failure', 'scout_failure']
target_policy = straight
checkpoint_kind = actor_critic_best.pt
```

## Seed-Mean Summary

| Scenario | Graph | Train Method | Success | Chain | Tracking | Connectivity | Message Age | Timeout | Steps |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| relay_failure | multi_relation | bc_ppo | 0.956 +/- 0.063 | 0.956 +/- 0.063 | 0.426 +/- 0.025 | 0.892 +/- 0.029 | 48.508 +/- 16.407 | 0.044 +/- 0.063 | 55.444 +/- 13.192 |
| scout_failure | multi_relation | bc_ppo | 0.933 +/- 0.054 | 0.933 +/- 0.054 | 0.418 +/- 0.018 | 0.880 +/- 0.032 | 50.319 +/- 17.978 | 0.067 +/- 0.054 | 60.167 +/- 11.839 |

## Boundary

```text
A paper robustness claim requires matched training budgets, fixed evaluation seeds, and enough episodes per checkpoint-scenario.
Use small-episode runs for diagnostics only; reserve 30+ episode runs for formal tables.
```
