# 3DOF Node-Failure Recovery Summary

Generated: 2026-07-16T12:50:42

Input:

```text
C:\Users\96251\Documents\Codex\2026-07-12\ni\work\ri_gmappo_uav\results\intercept_3d_node_failure_curriculum_formal_node_failure_eval\episode_metrics.csv
```

## Recovery Metrics

| Scenario | Pairs | Recovered Delta | Recovery Steps Delta | Chain-During-Failure Delta | Connectivity-During-Failure Delta |
|---|---:|---:|---:|---:|---:|
| relay_failure | 90 | +0.078 [+0.022, +0.133] | -16.2 [-28.0, -4.5] | +0.002 [-0.004, +0.009] | +0.001 [-0.003, +0.006] |
| scout_failure | 90 | +0.022 [-0.033, +0.078] | -4.4 [-16.2, +7.3] | -0.004 [-0.011, +0.003] | -0.003 [-0.007, +0.001] |

## Use Boundary

```text
Positive recovered/chain/connectivity deltas and negative recovery-step deltas favor the multi-relation graph.
Recovery-step values are censored by episode termination when a post-failure chain closure is not observed.
```
