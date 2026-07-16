# 3DOF Topology Robustness Evaluation

Generated: 2026-07-16T19:19:31

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
graph_encoders = ['single', 'multi_relation']
graph_relation_ablation = none
graph_message_ablation = none
graph_input_ablation = none
scenarios = ['relay_failure', 'scout_failure']
target_policy = break_turn
checkpoint_kind = actor_critic_best.pt
```

## Seed-Mean Summary

| Scenario | Graph | Train Method | Success | Chain | Tracking | Connectivity | Message Age | Timeout | Steps |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| relay_failure | multi_relation | bc_ppo | 0.267 +/- 0.000 | 0.267 +/- 0.000 | 0.264 +/- 0.000 | 0.287 +/- 0.000 | 70.449 +/- 0.000 | 0.733 +/- 0.000 | 219.667 +/- 0.000 |
| relay_failure | single | bc_ppo | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 0.114 +/- 0.000 | 0.180 +/- 0.000 | 92.853 +/- 0.000 | 1.000 +/- 0.000 | 260.000 +/- 0.000 |
| scout_failure | multi_relation | bc_ppo | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 0.184 +/- 0.000 | 0.242 +/- 0.000 | 82.879 +/- 0.000 | 1.000 +/- 0.000 | 260.000 +/- 0.000 |
| scout_failure | single | bc_ppo | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 0.123 +/- 0.000 | 0.217 +/- 0.000 | 87.687 +/- 0.000 | 1.000 +/- 0.000 | 260.000 +/- 0.000 |

## Boundary

```text
A paper robustness claim requires matched training budgets, fixed evaluation seeds, and enough episodes per checkpoint-scenario.
Use small-episode runs for diagnostics only; reserve 30+ episode runs for formal tables.
```
