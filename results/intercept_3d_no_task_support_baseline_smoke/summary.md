# 3DOF Straight-Target Baseline Protocol

Generated: 2026-07-16T13:29:11

## Protocol

```text
training/evaluation replicate seeds = [0]
methods = ['bc_only']
evaluation episodes per replicate = 2
target policy = straight
graph encoder = multi_relation
graph relation ablation = no_task_support
BC = 5 demonstration episodes, 1 epochs, unweighted cross entropy
PPO = 60 updates, 4 environments, 64 rollout steps, learning rate 0.0001
PPO entropy coefficient = 0.01
All learned methods use the same 64-dimensional network and 3DOF environment settings.
The geometric controller has no training seed; its replicate rows use the same evaluation seed blocks.
```

## Aggregate Results

| Method | Success | Chain Closed | Attack Window | Tracking | Collision | Constraint | Steps |
|---|---:|---:|---:|---:|---:|---:|---:|
| RI-GMAPPO BC-only | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 0.083 +/- 0.000 | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 260.0 +/- 0.0 |

## Boundary

```text
This protocol validates the 3DOF straight-target training curriculum only.
It is a baseline prerequisite, not evidence for the multi-relation graph or topology-curriculum contribution.
```
