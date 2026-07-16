# 3DOF Straight-Target Baseline Protocol

Generated: 2026-07-16T17:49:38

## Protocol

```text
training/evaluation replicate seeds = [0]
methods = ['bc_ppo']
evaluation episodes per replicate = 30
target policy = straight
graph encoder = multi_relation
graph relation ablation = none
graph message ablation = none
graph input ablation = no_role_identity
BC = 200 demonstration episodes, 80 epochs, unweighted cross entropy
PPO = 60 updates, 4 environments, 64 rollout steps, learning rate 5e-05
PPO entropy coefficient = 0.001
All learned methods use the same 64-dimensional network and 3DOF environment settings.
The geometric controller has no training seed; its replicate rows use the same evaluation seed blocks.
```

## Aggregate Results

| Method | Success | Chain Closed | Attack Window | Tracking | Collision | Constraint | Steps |
|---|---:|---:|---:|---:|---:|---:|---:|
| RI-GMAPPO BC-to-PPO | 0.900 +/- 0.000 | 0.900 +/- 0.000 | 1.000 +/- 0.000 | 0.413 +/- 0.000 | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 67.6 +/- 0.0 |

## Boundary

```text
This protocol validates the 3DOF straight-target training curriculum only.
It is a baseline prerequisite, not evidence for the multi-relation graph or topology-curriculum contribution.
```
