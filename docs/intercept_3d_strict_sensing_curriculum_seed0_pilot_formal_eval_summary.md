# 3DOF Node-Failure Recovery Summary

Generated: 2026-07-16T20:54:49

Input:

```text
results\intercept_3d_strict_sensing_curriculum_seed0_pilot\formal_eval\episode_metrics.csv
```

## Recovery Metrics

| Scenario | Pairs | Recovered Delta | Recovery Steps Delta | Chain-During-Failure Delta | Connectivity-During-Failure Delta |
|---|---:|---:|---:|---:|---:|
| relay_failure | 90 | +0.256 [+0.156, +0.367] | -53.9 [-75.3, -32.6] | +0.025 [+0.013, +0.038] | +0.016 [+0.008, +0.023] |
| scout_failure | 90 | +0.067 [-0.056, +0.189] | -14.0 [-39.9, +12.0] | +0.006 [-0.009, +0.020] | +0.002 [-0.008, +0.011] |

## Use Boundary

```text
Positive recovered/chain/connectivity deltas and negative recovery-step deltas favor the multi-relation graph.
Recovery-step values are censored by episode termination when a post-failure chain closure is not observed.
```
