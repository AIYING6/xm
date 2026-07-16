# 3DOF Node-Failure Recovery Summary

Generated: 2026-07-16T20:50:58

Input:

```text
results\intercept_3d_strict_sensing_curriculum_seed0_pilot\robustness_eval\episode_metrics.csv
```

## Recovery Metrics

| Scenario | Pairs | Recovered Delta | Recovery Steps Delta | Chain-During-Failure Delta | Connectivity-During-Failure Delta |
|---|---:|---:|---:|---:|---:|
| relay_failure | 15 | +0.267 [-0.067, +0.600] | -56.0 [-126.9, +15.1] | +0.020 [-0.023, +0.063] | +0.013 [-0.014, +0.039] |
| scout_failure | 15 | +0.067 [-0.267, +0.400] | -13.9 [-84.9, +57.1] | +0.001 [-0.041, +0.044] | -0.003 [-0.031, +0.024] |

## Use Boundary

```text
Positive recovered/chain/connectivity deltas and negative recovery-step deltas favor the multi-relation graph.
Recovery-step values are censored by episode termination when a post-failure chain closure is not observed.
```
