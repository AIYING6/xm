# 3DOF Interception Environment Smoke Test

Generated: 2026-07-30T00:22:52

Purpose:

```text
Validate the first 3DOF heterogeneous UAV interception environment before connecting it to EA-RG-MAPPO-S training.
This is an interface and dynamics smoke test, not a learning result.
```

## Summary

| Policy | Episodes | Success | Collision | Constraint Violation | Mean Steps | Mean Tracking | Mean Attack Window | Mean Connectivity | Mean Message Age |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| geometric | 5 | 0.800 | 0.200 | 0.000 | 146.4 | 0.667 | 0.266 | 1.000 | 0.267 |
| geometric_dropout | 5 | 0.800 | 0.200 | 0.000 | 146.4 | 0.600 | 0.266 | 1.000 | 0.300 |
| random | 5 | 0.000 | 0.000 | 0.000 | 260.0 | 0.000 | 0.000 | 0.133 | 156.667 |

## Interface Checked

```text
reset -> obs, share_obs, graph_obs
step -> obs, share_obs, graph_obs, rewards, dones, infos
obs shape = (3, 34)
share_obs shape = (3, 47)
node_feat shape = (4, 20)
edge_feat shape = (4, 4, 18)
adj shape = (4, 4)
relation_adj shape = (3, 4, 4)
```

## Boundary

```text
The smoke test proves that the 3DOF environment interface, graph observations, and mission-chain metrics are finite and executable.
It does not yet prove trainability or paper-level performance.
```
