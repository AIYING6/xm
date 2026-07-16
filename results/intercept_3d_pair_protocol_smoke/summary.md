# 3DOF Straight-Target Baseline Protocol

Generated: 2026-07-16T07:47:05

## Protocol

```text
training/evaluation replicate seeds = [6]
methods = ['bc_only', 'bc_ppo']
evaluation episodes per replicate = 1
target policy = straight
graph encoder = single
BC = 2 demonstration episodes, 1 epochs, unweighted cross entropy
PPO = 1 updates, 2 environments, 8 rollout steps, learning rate 0.0001
PPO entropy coefficient = 0.01
All learned methods use the same 64-dimensional network and 3DOF environment settings.
The geometric controller has no training seed; its replicate rows use the same evaluation seed blocks.
```

## Aggregate Results

| Method | Success | Chain Closed | Attack Window | Tracking | Collision | Constraint | Steps |
|---|---:|---:|---:|---:|---:|---:|---:|
| RI-GMAPPO BC-only | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 0.035 +/- 0.000 | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 260.0 +/- 0.0 |
| RI-GMAPPO BC-to-PPO | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 0.036 +/- 0.000 | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 260.0 +/- 0.0 |

## Boundary

```text
This protocol validates the 3DOF straight-target training curriculum only.
It is a baseline prerequisite, not evidence for the multi-relation graph or topology-curriculum contribution.
```
