# 3DOF Formal No-Role-Identity Ablation

Generated: 2026-07-16T10:22:41

This table compares the full multi-relation role graph against `no_role_identity`, which maps every role ID to the same neutral role inside the actor while preserving relation channels and edge features. Positive success/recovery deltas favor the full model; negative step deltas favor the full model.

| Scenario | N | Success full/no-role | Success delta [95% CI] | Recovery full/no-role | Recovery delta [95% CI] | Recovery-step delta [95% CI] | Steps delta [95% CI] |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| relay_failure | 90 | 1.000 / 0.978 | 0.022 [0.000, 0.056] | 1.000 / 0.978 | 0.022 [0.000, 0.056] | -4.856 [-11.944, -0.100] | -4.856 [-11.944, -0.100] |
| scout_failure | 90 | 0.967 / 0.978 | -0.011 [-0.067, 0.033] | 0.967 / 0.978 | -0.011 [-0.067, 0.033] | 2.222 [-7.244, 13.856] | 2.222 [-7.244, 13.856] |

## Interpretation

```text
Use this as auxiliary diagnostic evidence only. Relay failure supports a modest recovery-speed benefit from explicit role identity, but scout failure is mixed and does not support a broad no-role claim.
The stronger mechanism evidence remains no_task_support and no_role_pair_gate.
```
