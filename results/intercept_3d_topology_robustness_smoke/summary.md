# 3DOF Topology Robustness Evaluation

Generated: 2026-07-16T11:33:10

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
| nominal | multi_relation | bc_ppo | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 0.437 +/- 0.000 | 1.000 +/- 0.000 | 50.074 +/- 0.000 | 0.000 +/- 0.000 | 45.000 +/- 0.000 |
| nominal | single | bc_ppo | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 0.437 +/- 0.000 | 1.000 +/- 0.000 | 42.370 +/- 0.000 | 0.000 +/- 0.000 | 45.000 +/- 0.000 |
| range_050 | multi_relation | bc_ppo | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 0.103 +/- 0.000 | 0.204 +/- 0.000 | 146.209 +/- 0.000 | 1.000 +/- 0.000 | 260.000 +/- 0.000 |
| range_050 | single | bc_ppo | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 0.106 +/- 0.000 | 0.147 +/- 0.000 | 158.113 +/- 0.000 | 1.000 +/- 0.000 | 260.000 +/- 0.000 |
| relay_failure | multi_relation | bc_ppo | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 0.437 +/- 0.000 | 0.926 +/- 0.000 | 50.296 +/- 0.000 | 0.000 +/- 0.000 | 45.000 +/- 0.000 |
| relay_failure | single | bc_ppo | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 0.437 +/- 0.000 | 0.926 +/- 0.000 | 42.593 +/- 0.000 | 0.000 +/- 0.000 | 45.000 +/- 0.000 |

## Boundary

```text
These rows reuse nominally trained checkpoints. A paper robustness claim still requires matched topology-curriculum retraining and a final fixed evaluation suite.
Use this table to select disruption levels that are neither saturated nor trivial.
```
