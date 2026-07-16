# 3DOF Topology Robustness Evaluation

Generated: 2026-07-16T20:50:37

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
| relay_failure | multi_relation | bc_ppo | 0.800 +/- 0.163 | 0.800 +/- 0.163 | 0.386 +/- 0.056 | 0.805 +/- 0.079 | 48.129 +/- 4.724 | 0.200 +/- 0.163 | 89.800 +/- 34.865 |
| relay_failure | single | bc_ppo | 0.533 +/- 0.249 | 0.533 +/- 0.249 | 0.284 +/- 0.088 | 0.695 +/- 0.104 | 39.762 +/- 1.040 | 0.467 +/- 0.249 | 145.800 +/- 53.239 |
| scout_failure | multi_relation | bc_ppo | 0.800 +/- 0.283 | 0.800 +/- 0.283 | 0.386 +/- 0.101 | 0.784 +/- 0.161 | 53.528 +/- 6.280 | 0.200 +/- 0.283 | 89.800 +/- 60.105 |
| scout_failure | single | bc_ppo | 0.733 +/- 0.377 | 0.733 +/- 0.377 | 0.359 +/- 0.136 | 0.789 +/- 0.160 | 39.159 +/- 1.510 | 0.267 +/- 0.377 | 103.667 +/- 80.139 |

## Boundary

```text
A paper robustness claim requires matched training budgets, fixed evaluation seeds, and enough episodes per checkpoint-scenario.
Use small-episode runs for diagnostics only; reserve 30+ episode runs for formal tables.
```
