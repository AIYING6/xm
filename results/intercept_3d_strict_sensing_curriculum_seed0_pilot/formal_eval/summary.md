# 3DOF Topology Robustness Evaluation

Generated: 2026-07-16T20:54:39

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
target_policy = straight
strict_target_sensing = True
checkpoint_kind = actor_critic_best.pt
```

## Seed-Mean Summary

| Scenario | Graph | Train Method | Success | Chain | Tracking | Connectivity | Message Age | Timeout | Steps |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| relay_failure | multi_relation | bc_ppo | 0.967 +/- 0.027 | 0.967 +/- 0.027 | 0.434 +/- 0.009 | 0.894 +/- 0.012 | 50.801 +/- 5.695 | 0.033 +/- 0.027 | 53.567 +/- 5.886 |
| relay_failure | single | bc_ppo | 0.711 +/- 0.197 | 0.711 +/- 0.197 | 0.340 +/- 0.070 | 0.797 +/- 0.068 | 40.358 +/- 1.630 | 0.289 +/- 0.197 | 107.478 +/- 41.951 |
| scout_failure | multi_relation | bc_ppo | 0.856 +/- 0.204 | 0.856 +/- 0.204 | 0.393 +/- 0.073 | 0.832 +/- 0.111 | 52.655 +/- 6.051 | 0.144 +/- 0.204 | 77.033 +/- 43.464 |
| scout_failure | single | bc_ppo | 0.789 +/- 0.251 | 0.789 +/- 0.251 | 0.368 +/- 0.090 | 0.831 +/- 0.090 | 40.827 +/- 1.500 | 0.211 +/- 0.251 | 91.033 +/- 53.481 |

## Boundary

```text
A paper robustness claim requires matched training budgets, fixed evaluation seeds, and enough episodes per checkpoint-scenario.
Use small-episode runs for diagnostics only; reserve 30+ episode runs for formal tables.
```
