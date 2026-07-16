# 3DOF Topology Robustness Evaluation

Generated: 2026-07-16T19:31:00

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
target_policy = weaving
checkpoint_kind = actor_critic_best.pt
```

## Seed-Mean Summary

| Scenario | Graph | Train Method | Success | Chain | Tracking | Connectivity | Message Age | Timeout | Steps |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| relay_failure | multi_relation | bc_ppo | 0.267 +/- 0.218 | 0.267 +/- 0.218 | 0.253 +/- 0.057 | 0.258 +/- 0.065 | 75.026 +/- 16.207 | 0.733 +/- 0.218 | 226.033 +/- 32.028 |
| relay_failure | single | bc_ppo | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 0.095 +/- 0.007 | 0.209 +/- 0.022 | 93.186 +/- 9.071 | 1.000 +/- 0.000 | 260.000 +/- 0.000 |
| scout_failure | multi_relation | bc_ppo | 0.144 +/- 0.204 | 0.144 +/- 0.204 | 0.223 +/- 0.046 | 0.257 +/- 0.021 | 80.836 +/- 7.203 | 0.844 +/- 0.197 | 241.322 +/- 21.740 |
| scout_failure | single | bc_ppo | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 0.100 +/- 0.010 | 0.233 +/- 0.029 | 92.839 +/- 7.828 | 1.000 +/- 0.000 | 260.000 +/- 0.000 |

## Boundary

```text
A paper robustness claim requires matched training budgets, fixed evaluation seeds, and enough episodes per checkpoint-scenario.
Use small-episode runs for diagnostics only; reserve 30+ episode runs for formal tables.
```
