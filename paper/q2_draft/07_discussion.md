# 7. Discussion

The evidence supports a narrow but useful conclusion: adaptive weighting over predefined topology perturbations can produce a strong average and median robustness upside while preserving the same policy architecture and legal information boundary. This is an empirical training-distribution result, not a general robustness guarantee.

The most important limitation is seed sensitivity. Development seed1902 violates the frozen retention contract in F0/OOD mean and shows a condition-level timeout breach. Held-out seed2002 is a severe reversal at 10M, with lower F0/OOD outcomes and higher timeout. No single actionable adaptive-training failure mechanism was identified by the forensic review, so these outcomes must be treated as genuine reliability evidence rather than as removable anomalies.

Safety is mixed. Development pooled collision and timeout are favorable for DRTP, but held-out collision is higher for DRTP in all three seeds and timeout reverses sharply at seed2002. The manuscript therefore does not claim that DRTP improves safety. Constraint violations remain zero in the cited audits.

The current evidence is limited to a heterogeneous three-UAV setting. The frozen architecture can be parameterized by agent count in code, but a fair 4/5-UAV study would require new role configurations, critic dimensions, failure semantics, and retraining. The paper should state this scope boundary rather than present an unsupported zero-shot scalability claim. Similarly, G0 found no actionable additional structural-topology generalization gap on its development-only suite; that result is a limitation/context statement, not a universal generalization claim.

Finally, DRTP is related to distributionally robust and topology-aware learning, but its defensible novelty lies in the integrated problem/evaluation package and bounded topology-group weighting. The paper should avoid first-ever language and acknowledge that external published methods were not fair drop-in comparators under the frozen contract.
