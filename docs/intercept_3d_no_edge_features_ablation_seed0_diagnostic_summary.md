# 3DOF Seed-0 No-Edge-Features Diagnostic

Generated: 2026-07-16T16:26:09

This is a one-seed diagnostic comparison. It is useful for deciding whether `no_edge_features` deserves formal ablation budget, but it is not manuscript-level statistical evidence.

| Scenario | N | Success full/no-edge | Success delta [95% CI] | Recovery full/no-edge | Recovery delta [95% CI] | Recovery-step delta [95% CI] | Steps delta [95% CI] |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| relay_failure | 30 | 1.000 / 0.967 | +0.033 [+0.000, +0.100] | 1.000 / 0.967 | +0.033 [+0.000, +0.100] | -7.067 [-21.267, +0.100] | -7.067 [-21.267, +0.100] |
| scout_failure | 30 | 1.000 / 1.000 | +0.000 [+0.000, +0.000] | 1.000 / 1.000 | +0.000 [+0.000, +0.000] | -0.033 [-0.233, +0.133] | -0.033 [-0.233, +0.167] |

## Decision Boundary

```text
Promote this ablation only if the seed-0 diagnostic shows a clear and interpretable degradation when edge features are removed.
If the signal is mixed or improves the ablated policy, keep it as an internal diagnostic and use formal budget elsewhere.
```
