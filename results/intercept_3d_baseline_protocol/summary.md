# 3DOF Straight-Target Baseline Protocol

Generated: 2026-07-16T02:15:54

## Protocol

```text
training/evaluation replicate seeds = [0, 1, 2]
evaluation episodes per replicate = 30
target policy = straight
BC = 200 demonstration episodes, 80 epochs, unweighted cross entropy
PPO = 60 updates, 4 environments, 64 rollout steps
All learned methods use the same 64-dimensional network and 3DOF environment settings.
The geometric controller has no training seed; its replicate rows use the same evaluation seed blocks.
```

## Aggregate Results

| Method | Success | Chain Closed | Attack Window | Tracking | Collision | Constraint | Steps |
|---|---:|---:|---:|---:|---:|---:|---:|
| Geometric controller | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 0.437 +/- 0.001 | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 45.3 +/- 0.2 |
| RI-GMAPPO from scratch | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 0.070 +/- 0.052 | 0.000 +/- 0.000 | 0.278 +/- 0.481 | 247.5 +/- 21.7 |
| RI-GMAPPO BC-only | 0.844 +/- 0.077 | 0.844 +/- 0.077 | 0.967 +/- 0.033 | 0.386 +/- 0.026 | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 78.9 +/- 16.5 |
| RI-GMAPPO BC-to-PPO | 0.967 +/- 0.033 | 0.967 +/- 0.033 | 0.989 +/- 0.019 | 0.427 +/- 0.010 | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 52.6 +/- 7.3 |

## Boundary

```text
This protocol validates the 3DOF straight-target training curriculum only.
It is a baseline prerequisite, not evidence for the multi-relation graph or topology-curriculum contribution.
```
