# 3DOF Straight-Target Baseline Protocol

Generated: 2026-07-16T01:57:49

## Protocol

```text
training/evaluation replicate seeds = [9]
evaluation episodes per replicate = 2
target policy = straight
BC = 2 demonstration episodes, 1 epochs, unweighted cross entropy
PPO = 1 updates, 2 environments, 8 rollout steps
All learned methods use the same 64-dimensional network and 3DOF environment settings.
The geometric controller has no training seed; its replicate rows use the same evaluation seed blocks.
```

## Aggregate Results

| Method | Success | Chain Closed | Attack Window | Tracking | Collision | Constraint | Steps |
|---|---:|---:|---:|---:|---:|---:|---:|
| Geometric controller | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 1.000 +/- 0.000 | 0.433 +/- 0.000 | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 45.0 +/- 0.0 |
| RI-GMAPPO from scratch | 0.500 +/- 0.000 | 0.500 +/- 0.000 | 0.500 +/- 0.000 | 0.099 +/- 0.000 | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 187.0 +/- 0.0 |
| RI-GMAPPO BC-only | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 0.037 +/- 0.000 | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 260.0 +/- 0.0 |
| RI-GMAPPO BC-to-PPO | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 0.067 +/- 0.000 | 0.000 +/- 0.000 | 0.000 +/- 0.000 | 260.0 +/- 0.0 |

## Boundary

```text
This protocol validates the 3DOF straight-target training curriculum only.
It is a baseline prerequisite, not evidence for the multi-relation graph or topology-curriculum contribution.
```
