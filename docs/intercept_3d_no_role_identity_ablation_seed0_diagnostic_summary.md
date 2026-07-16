# 3DOF Seed-0 No-Role-Identity Diagnostic

Generated: 2026-07-16T09:55:27

This is a one-seed diagnostic comparison. It supports promoting `no_role_identity` to a formal three-seed ablation because recovery-step degradation is clear in both node-failure scenarios, but it is not itself manuscript-level statistical evidence.

| Scenario | N | Success full/no-role | Success delta [95% CI] | Recovery full/no-role | Recovery delta [95% CI] | Recovery-step delta [95% CI] | Steps delta [95% CI] |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| relay_failure | 30 | 1.000 / 0.900 | 0.100 [0.000, 0.200] | 1.000 / 0.900 | 0.100 [0.000, 0.200] | -21.900 [-43.367, -0.633] | -21.900 [-43.367, -0.633] |
| scout_failure | 30 | 1.000 / 0.933 | 0.067 [0.000, 0.167] | 1.000 / 0.933 | 0.067 [0.000, 0.167] | -14.767 [-36.033, -0.500] | -14.767 [-36.033, -0.500] |

## Decision

```text
Promote to formal three-seed ablation. Use matched seeds, relay/scout node-failure scenarios, and the same BC-to-PPO plus topology-curriculum budget as the other mechanism ablations.
```
