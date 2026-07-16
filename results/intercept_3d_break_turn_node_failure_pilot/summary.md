# 3DOF Topology Robustness Evaluation

Generated: 2026-07-16T18:59:12

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
| relay_failure | multi_relation | bc_ppo | 0.244 +/- 0.220 | 0.244 +/- 0.220 | 0.254 +/- 0.055 | 0.294 +/- 0.049 | 73.296 +/- 9.138 | 0.722 +/- 0.185 | 215.000 +/- 28.839 |
| relay_failure | single | bc_ppo | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 0.115 +/- 0.015 | 0.223 +/- 0.032 | 92.042 +/- 11.098 | 1.000 +/- 0.000 | 260.000 +/- 0.000 |
| scout_failure | multi_relation | bc_ppo | 0.144 +/- 0.204 | 0.144 +/- 0.204 | 0.224 +/- 0.052 | 0.288 +/- 0.066 | 78.253 +/- 9.263 | 0.844 +/- 0.197 | 233.511 +/- 32.770 |
| scout_failure | single | bc_ppo | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 0.116 +/- 0.024 | 0.246 +/- 0.014 | 90.060 +/- 12.624 | 1.000 +/- 0.000 | 260.000 +/- 0.000 |

## Boundary

```text
A paper robustness claim requires matched training budgets, fixed evaluation seeds, and enough episodes per checkpoint-scenario.
Use small-episode runs for diagnostics only; reserve 30+ episode runs for formal tables.
```
