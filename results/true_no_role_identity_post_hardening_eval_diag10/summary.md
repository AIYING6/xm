# 3DOF Topology Robustness Evaluation

Generated: 2026-07-22T02:50:24

Purpose:

```text
Evaluate saved 3DOF checkpoints under communication range compression, dropout, delay, radar dropout, and temporary communication-node failure.
When the checkpoints are nominally trained, use this as scenario screening; when they are topology-curriculum trained, use it as a matched robustness diagnostic.
```

## Configuration

```text
episodes_per_checkpoint_scenario = 10
training_seeds = [0, 1, 2]
train_methods = ['bc_ppo']
graph_encoders = ['multi_relation']
graph_relation_ablation = none
graph_message_ablation = none
graph_input_ablation = no_role_identity
scenarios = ['dropout030_relay_failure', 'scout_failure']
target_policy = straight
strict_target_sensing = True
agent_target_info_bottleneck = True
max_target_message_age_steps = 80
min_target_confidence = 0.2
checkpoint_kind = actor_critic_best.pt
```

## Seed-Mean Summary

| Scenario | Graph | Train Method | Success | Chain | Tracking | Connectivity | Message Age | Timeout | Steps |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| dropout030_relay_failure | multi_relation | bc_ppo | 0.500 +/- 0.374 | 0.500 +/- 0.374 | 0.270 +/- 0.136 | 0.467 +/- 0.112 | 56.664 +/- 1.616 | 0.500 +/- 0.374 | 153.233 +/- 79.680 |
| scout_failure | multi_relation | bc_ppo | 0.500 +/- 0.374 | 0.500 +/- 0.374 | 0.270 +/- 0.136 | 0.768 +/- 0.120 | 61.963 +/- 3.116 | 0.500 +/- 0.374 | 153.267 +/- 79.742 |

## Boundary

```text
A paper robustness claim requires matched training budgets, fixed evaluation seeds, and enough episodes per checkpoint-scenario.
Use small-episode runs for diagnostics only; reserve 30+ episode runs for formal tables.
```
