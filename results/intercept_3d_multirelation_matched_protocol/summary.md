# 3DOF Straight-Target Baseline Protocol

Generated: 2026-07-16T11:11:33

## Protocol

```text
training/evaluation replicate seeds = [0, 1, 2]
methods = ['bc_only', 'bc_ppo']
evaluation episodes per replicate = 30
target policy = straight
graph encoder = multi_relation
BC = 200 demonstration episodes, 80 epochs, unweighted cross entropy
PPO = 60 updates, 4 environments, 64 rollout steps, learning rate 5e-05
PPO entropy coefficient = 0.001
All learned methods use the same 64-dimensional network and 3DOF environment settings.
The geometric controller has no training seed; its replicate rows use the same evaluation seed blocks.
```

## Aggregate Results

| Method | Success | Chain Closed | Attack Window | Tracking | Collision | Constraint | Steps |
|---|---:|---:|---:|---:|---:|---:|---:|
| RI-GMAPPO BC-only | 0.933 +/- 0.115 | 0.933 +/- 0.115 | 0.989 +/- 0.019 | 0.416 +/- 0.041 | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 59.8 +/- 24.7 |
| RI-GMAPPO BC-to-PPO | 0.922 +/- 0.107 | 0.922 +/- 0.107 | 0.978 +/- 0.038 | 0.414 +/- 0.039 | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 62.3 +/- 22.8 |

## Boundary

```text
This protocol validates the 3DOF straight-target training curriculum only.
It is a baseline prerequisite, not evidence for the multi-relation graph or topology-curriculum contribution.
```
