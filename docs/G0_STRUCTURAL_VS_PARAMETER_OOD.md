# G0 structural versus parameter OOD

## Frozen comparison

Parameter OOD changes failure timing or duration within the previously exposed Relay-1 failure family. Structural OOD changes failed node, communication-edge availability, directionality, or their composition. The comparison was defined before evaluation and uses the same deterministic episode namespace and policy checkpoints.

## UTR seed-level gaps

| seed | J seen F0 | J structural mean | J parameter mean | structural gap | parameter gap | structural−parameter |
|---|---|---|---|---|---|---|
| 2201 | 60.141 | 61.534 | 54.758 | -1.393 | 5.383 | -6.776 |
| 2202 | 176.081 | 173.834 | 172.092 | 2.247 | 3.989 | -1.742 |
| 2203 | 58.007 | 72.661 | 60.483 | -14.654 | -2.476 | -12.178 |
| 2204 | 119.091 | 100.528 | 115.438 | 18.564 | 3.654 | 14.910 |
| 2205 | 44.438 | 51.388 | 41.463 | -6.950 | 2.975 | -9.925 |

The structural gap is `J_seen_F0 − mean(J_U1…J_U5)`. The parameter gap is `J_seen_F0 − mean(J_timing,J_duration)`. A positive structural-minus-parameter value means structural OOD is more damaging for that seed under the frozen definition.

## Decision rule application

- Median structural gap: `-1.392966`
- Median structural-minus-parameter gap: `-6.775951`
- Positive seed differences: `1/5`
- Primary topology cells above A threshold: `0/5`
- A pooled threshold: `13.732736`
- Pre-registered outcome: **C — NO_ACTIONABLE_TOPOLOGY_GENERALIZATION_GAP**

No threshold was selected after looking at performance. U6 is excluded from the primary mean because the frozen feasibility audit marked it diagnostic-only.
