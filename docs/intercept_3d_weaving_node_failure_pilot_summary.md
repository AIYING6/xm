# 3DOF Weaving Node-Failure Pilot

Generated: 2026-07-16T11:32:47

Zero-shot scenario-depth pilot under target_policy=weaving. Existing straight-target topology-curriculum checkpoints are reused without retraining.

| Scenario | N | Success single/multi | Success delta [95% CI] | Recovery single/multi | Recovery delta [95% CI] | Steps delta [95% CI] | Timeout delta [95% CI] |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| relay_failure | 90 | 0.000 / 0.267 | 0.267 [0.178, 0.356] | 0.000 / 0.267 | 0.267 [0.178, 0.356] | -33.967 [-46.067, -22.611] | -0.267 [-0.356, -0.178] |
| scout_failure | 90 | 0.000 / 0.144 | 0.144 [0.078, 0.222] | 0.000 / 0.144 | 0.144 [0.078, 0.222] | -18.678 [-28.756, -9.611] | -0.156 [-0.233, -0.089] |

## Interpretation

```text
The maneuvering target creates strong separation between single-graph and multi-relation, but absolute success is still low; treat as scenario-depth pilot, not main-table evidence until a milder curriculum raises success.
```
