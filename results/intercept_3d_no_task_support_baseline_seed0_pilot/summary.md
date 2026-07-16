# 3DOF Straight-Target Baseline Protocol

Generated: 2026-07-16T13:33:06

## Protocol

```text
training/evaluation replicate seeds = [0]
methods = ['bc_ppo']
evaluation episodes per replicate = 5
target policy = straight
graph encoder = multi_relation
graph relation ablation = no_task_support
BC = 80 demonstration episodes, 30 epochs, unweighted cross entropy
PPO = 20 updates, 4 environments, 64 rollout steps, learning rate 5e-05
PPO entropy coefficient = 0.001
All learned methods use the same 64-dimensional network and 3DOF environment settings.
The geometric controller has no training seed; its replicate rows use the same evaluation seed blocks.
```

## Aggregate Results

| Method | Success | Chain Closed | Attack Window | Tracking | Collision | Constraint | Steps |
|---|---:|---:|---:|---:|---:|---:|---:|
| RI-GMAPPO BC-to-PPO | 0.200 +/- 0.000 | 0.200 +/- 0.000 | 0.600 +/- 0.000 | 0.161 +/- 0.000 | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 217.0 +/- 0.0 |

## Boundary

```text
This protocol validates the 3DOF straight-target training curriculum only.
It is a baseline prerequisite, not evidence for the multi-relation graph or topology-curriculum contribution.
```
