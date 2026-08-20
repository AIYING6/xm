# T5 — Offline Decision-Coupling Evidence

## Protocol

`T5-SUPPORT-RESPONSE-OFFLINE-FALSIFICATION-V1` reused only the five frozen T1 UTR/SG final checkpoints and native actor-legal telemetry. It constructed no environment, generated no rollout/tape, performed no optimizer update, and did not alter historical results. Each checkpoint was exactly 116,728 parameters; each seed supplied 3,600 deterministic stratified samples, with 3,205–3,289 failure-condition samples used in the response test.

## Candidate-specific tests

| Test | Pre-registered question | Result | Interpretation |
|---|---|---|---|
| T5.1 response separation | Do good and weak policies differ after legal-state matching? | PASS (T4) | Good−weak mask TVD `+0.283`; permutation-control TVD `+0.100`. |
| T5.2 topology response consistency | Is good pre→early attacker response at least as directionally consistent as weak? | **FAIL** | Good cosine `0.846`; weak `0.881`; good−weak `−0.036`. |
| T5.3 role specificity | Do frozen responses establish stable cross-role response directions needed for a role-specific coupling? | **NOT ESTABLISHED** | The response-contrast audit produced no stable aggregate cross-role cosine; T4 role-level action differences alone do not identify a transferable coupling rule. |
| T5.4 topology specificity | Is the utilization gap topology-transition relevant? | PASS (T4) | Good−weak mask-TVD gap grows from `0.145` pre-onset to `0.322` early post-onset. |
| T5.5 downstream stage | Is the main gap downstream of representation? | PASS (T4) | Raw/SG/pre-policy probe good−weak AUC gaps are only `+0.016/+0.008/+0.006`. |

The negative T5.2 result is decisive for this candidate. It is not enough that good policies are more sensitive to support; a topology-equivariant response regularizer would need the desirable response pattern itself to be present in good policies. It is not.

## Auxiliary descriptive check

The high-minus-low local support-quality sensitivity is positive in all five frozen seeds, but it does not rescue the candidate: the topological response direction is not more consistent in good seeds at the transition being targeted. This distinction prevents substituting a magnitude-only observation for an unverified response-consistency principle.

## Conclusion

T4 remains valid evidence of a support-utilization gap. T5 shows that it does not identify the particular action-response invariant required for the sole reviewed structural mechanism. This is a falsification result, not evidence against the frozen topology-robustness problem.

Machine-readable output: `results/development/t5_support_response_falsification_run1/t5_support_response_falsification.json`.
