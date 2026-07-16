# LAG Role Graph Wrapper Test

Generated: 2026-07-16T21:04:46

Purpose:

```text
Validate a thin reset/step wrapper that exposes EA-RG-MAPPO-S graph tensors from a LAG-like environment.
This test uses fake simulator objects and does not claim real JSBSim validation.
```

## Summary

| Item | Value |
|---|---:|
| Checks | 11 |
| Failed | 0 |

## Checks

| Check | Status | Detail |
|---|---|---|
| `reset_passthrough` | ok | {'reset_count': 2} |
| `reset_node_shape` | ok | (4, 15) |
| `reset_edge_shape` | ok | (4, 4, 13) |
| `reset_adj_shape` | ok | (4, 4) |
| `reset_role` | ok | [0, 0, 1, 1] |
| `step_passthrough` | ok | step_count=1 |
| `last_graph_updated` | ok | step graph cached |
| `step_state_refresh` | ok | altitude feature changed after step |
| `no_nan` | ok | no NaN |
| `no_inf` | ok | no Inf |
| `close_passthrough` | ok | env closed |
