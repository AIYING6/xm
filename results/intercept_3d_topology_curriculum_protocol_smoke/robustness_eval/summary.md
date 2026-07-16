# 3DOF Topology Robustness Evaluation

Generated: 2026-07-16T12:01:48

Purpose:

```text
Zero-shot evaluation of existing 3DOF checkpoints under communication range compression, dropout, delay, radar dropout, and temporary communication-node failure.
This identifies the topology disruptions worth using for staged retraining; it is not yet a topology-curriculum training result.
```

## Configuration

```text
episodes_per_checkpoint_scenario = 1
training_seeds = [0]
train_methods = ['bc_ppo']
graph_encoders = ['single', 'multi_relation']
scenarios = ['nominal', 'range_050', 'relay_failure']
target_policy = straight
checkpoint_kind = actor_critic_best.pt
```

## Seed-Mean Summary

| Scenario | Graph | Train Method | Success | Chain | Tracking | Connectivity | Message Age | Timeout | Steps |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| nominal | multi_relation | bc_ppo | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 0.417 +/- 0.000 | 1.000 +/- 0.000 | 47.273 +/- 0.000 | 0.000 +/- 0.000 | 44.000 +/- 0.000 |
| nominal | single | bc_ppo | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 0.417 +/- 0.000 | 1.000 +/- 0.000 | 43.333 +/- 0.000 | 0.000 +/- 0.000 | 44.000 +/- 0.000 |
| range_050 | multi_relation | bc_ppo | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 0.430 +/- 0.000 | 0.163 +/- 0.000 | 217.630 +/- 0.000 | 0.000 +/- 0.000 | 45.000 +/- 0.000 |
| range_050 | single | bc_ppo | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 0.430 +/- 0.000 | 0.022 +/- 0.000 | 254.222 +/- 0.000 | 0.000 +/- 0.000 | 45.000 +/- 0.000 |
| relay_failure | multi_relation | bc_ppo | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 0.417 +/- 0.000 | 0.939 +/- 0.000 | 47.424 +/- 0.000 | 0.000 +/- 0.000 | 44.000 +/- 0.000 |
| relay_failure | single | bc_ppo | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 0.417 +/- 0.000 | 0.939 +/- 0.000 | 43.485 +/- 0.000 | 0.000 +/- 0.000 | 44.000 +/- 0.000 |

## Boundary

```text
These rows reuse nominally trained checkpoints. A paper robustness claim still requires matched topology-curriculum retraining and a final fixed evaluation suite.
Use this table to select disruption levels that are neither saturated nor trivial.
```
