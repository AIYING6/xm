# Historical-method reclassification

## Method-level view

| Method | Cross-cohort performance classification | Reliability classification | Interpretation |
| --- | --- | --- | --- |
| Original DRTP | PERFORMANCE_MIXED | RELIABILITY_NOT_IMPROVED | Formal 10M evidence is performance-positive; independent matched evidence reverses direction, so the publishable claim is bounded performance upside rather than universal reliability. |
| S1 TR | PERFORMANCE_SUCCESS | RELIABILITY_NOT_IMPROVED | A local performance-positive signal did not protect lower-tail reliability. |
| S2 Conservative | PERFORMANCE_SUCCESS | RELIABILITY_MIXED | The strongest local sampler-stabilization signal; it remains development-only and its predeclared reliability gate did not pass. |
| Conservative-DRTP R1 | NO_CLEAR_PERFORMANCE_VALUE | RELIABILITY_NOT_IMPROVED | Independent replication reversed the local conservative result. |
| KLR | PERFORMANCE_MIXED | RELIABILITY_NOT_IMPROVED | A promising pilot did not survive final two-cohort replication. |
| KLB | NO_CLEAR_PERFORMANCE_VALUE | RELIABILITY_NOT_IMPROVED | No matched performance value was retained. |
| PP-DRTP | PERFORMANCE_MIXED | RELIABILITY_NOT_IMPROVED | The local rescue signal reversed in independent validation. |
| CV-DRTP | NO_CLEAR_PERFORMANCE_VALUE | RELIABILITY_NOT_IMPROVED | Both validation cohorts were adverse relative to Original DRTP. |
| Reliable-DRTP ensemble | PERFORMANCE_MIXED | RELIABILITY_NOT_IMPROVED | A positive cohort-A mean did not persist in cohort B and did not protect against catastrophic bundles. |
| Group-weighted PPO | NO_CLEAR_PERFORMANCE_VALUE | RELIABILITY_NOT_IMPROVED | The same-rollout local mechanism did not accumulate into reliable fresh-seed policy performance. |

## No empirical policy-performance classification

| Method | Historical status | Reclassification | Reason |
| --- | --- | --- | --- |
| PR-DRTP / population selector | B4_ZERO_TRAINING_FEASIBILITY_ONLY | NO_EMPIRICAL_PERFORMANCE_EVIDENCE | The archived artifact is a zero-training feasibility audit, not a matched performance experiment. |
| Selective-KLR / SR-DRTP gate | P1_GATE_NO_GO | NO_EMPIRICAL_PERFORMANCE_EVIDENCE | This was an observational matched-shadow utility audit; no final policy arm was trained or evaluated as a performance candidate. |
