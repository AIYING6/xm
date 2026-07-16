# LAG Role Graph Adapter Test

Generated: 2026-07-16T21:04:45

Purpose:

```text
Validate the duck-typed adapter that converts LAG-like simulator states into EA-RG-MAPPO-S role graph tensors.
This test uses fake simulator objects and does not claim real JSBSim validation.
```

## Summary

| Item | Value |
|---|---:|
| Checks | 26 |
| Failed | 0 |

## Checks

| Check | Status | Detail |
|---|---|---|
| state_count | ok | `states=4` |
| role_assignment | ok | `[0, 0, 1, 1]` |
| node_shape_r500 | ok | `(4, 15)` |
| edge_shape_r500 | ok | `(4, 4, 13)` |
| adj_shape_r500 | ok | `(4, 4)` |
| self_edges_r500 | ok | `[1.0, 1.0, 1.0, 1.0]` |
| enemy_edges_r500 | ok | `enemy_edges=8` |
| team_monotonic_r500 | ok | `team_edges=0` |
| no_nan_r500 | ok | `no NaN` |
| no_inf_r500 | ok | `no Inf` |
| node_shape_r1500 | ok | `(4, 15)` |
| edge_shape_r1500 | ok | `(4, 4, 13)` |
| adj_shape_r1500 | ok | `(4, 4)` |
| self_edges_r1500 | ok | `[1.0, 1.0, 1.0, 1.0]` |
| enemy_edges_r1500 | ok | `enemy_edges=8` |
| team_monotonic_r1500 | ok | `team_edges=4` |
| no_nan_r1500 | ok | `no NaN` |
| no_inf_r1500 | ok | `no Inf` |
| node_shape_r4000 | ok | `(4, 15)` |
| edge_shape_r4000 | ok | `(4, 4, 13)` |
| adj_shape_r4000 | ok | `(4, 4)` |
| self_edges_r4000 | ok | `[1.0, 1.0, 1.0, 1.0]` |
| enemy_edges_r4000 | ok | `enemy_edges=8` |
| team_monotonic_r4000 | ok | `team_edges=4` |
| no_nan_r4000 | ok | `no NaN` |
| no_inf_r4000 | ok | `no Inf` |

## Interpretation

```text
The adapter can already be tested without JSBSim by using LAG-like get_position/get_velocity/get_rpy methods.
The next real migration step is to run the same adapter on a real MultipleCombatEnv reset after JSBSim data is available.
```
