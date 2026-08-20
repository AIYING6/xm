# T1 Seed-Level Reference and Prospective Ranking

## Scope and provenance

This document freezes the seed labels used by T2 **before** reading the
failure-aligned behavioral comparisons. It is a development-only description
of the completed T1 UTR-SG-MAPPO reference, not a method comparison or a final
paper result.

- Source run: `results/development/t1_telemetry_native_reference_1m_run1`
- Method: unchanged 116,728-parameter UTR-SG-MAPPO reference.
- Training: five independent seeds, 1,000,192 strict-continuous environment
  steps per seed.
- Evaluation: T1 tape `920000–920099`; 1,200 episodes per seed.
- Raw source closure: PASS for every seed.
- T2 offline derivative: `results/development/t2_telemetry_native_mechanism_final`.

`J_OOD_mean` is the mean of the ten OOD conditions, excluding nominal and
canonical F0. The row order below freezes the specified lexicographic ranking:
`J_OOD_worst` (descending), timeout (ascending), `J_OOD_mean` (descending),
then `J_F0` (descending).

## Frozen ranking

| Rank | Seed | Label | J_nominal | J_F0 | J_OOD_mean | J_OOD_worst | Collision | Timeout | Constraint | Survive-to-onset | Trigger success in risk set | Pre-trigger collision |
|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2202 | GOOD | 188.756 | 165.788 | 164.521 | 152.470 | 6.08% | 66.58% | 0.00% | 96.36% (1060/1100) | 100.00% | 3.64% (40/1100) |
| 2 | 2204 | GOOD | 121.801 | 116.938 | 116.834 | 109.139 | 2.08% | 97.33% | 0.00% | 100.00% (1100/1100) | 100.00% | 0.00% |
| 3 | 2201 | INTERMEDIATE | 84.409 | 60.938 | 61.909 | 53.845 | 0.00% | 100.00% | 0.00% | 100.00% (1100/1100) | 100.00% | 0.00% |
| 4 | 2203 | WEAK | 98.946 | 57.777 | 58.979 | 49.154 | 8.25% | 91.75% | 0.00% | 100.00% (1100/1100) | 100.00% | 0.00% |
| 5 | 2205 | WEAK | 61.882 | 44.521 | 45.089 | 38.109 | 0.00% | 100.00% | 0.00% | 100.00% (1100/1100) | 100.00% | 0.00% |

The labels are therefore immutable for T2:

- **GOOD:** seeds `2202`, `2204`
- **WEAK:** seeds `2203`, `2205`
- **INTERMEDIATE:** seed `2201`

## Interpretation boundary

The table establishes substantial development-seed dispersion. It does not
identify a causal mechanism, establish method superiority, or permit a change
to the frozen environment, actor boundary, algorithm, seed set, or evaluation
tape. Pre-onset collisions remain in both performance and safety denominators;
they are not evaluator failures.
