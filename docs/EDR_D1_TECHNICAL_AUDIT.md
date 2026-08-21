# EDR-D1 Technical Audit

**Protocol:** `EDR-D1-TECHNICAL-AUDIT-V1`  
**Result:** `TECHNICAL_PASS`  
**Machine-readable evidence:** `results/development/edr_d1_technical_audit_run3/edr_d1_technical_audit.json`

| Audit | Result | Evidence |
|---|---:|---|
| A — syntax/import/runtime/checkpoint | PASS | Deterministic EDR forward, save/reload and one-update finite-value smoke passed. |
| B — parameter equality | PASS | SG = EDR = `116,728`. |
| C — deletion locality | PASS | Surviving contribution max/mean error `0.0`, tolerance `1e-7`. |
| D — SG positive control | PASS | Same surviving contribution changes by max `0.05942583` after the legal deletion. |
| E — real F0 relevance | PASS | Frozen seed-2202, episode `920000`: at post-step 43 Relay→Attacker and Scout→Attacker are both legal; at post-step 45 Relay→Attacker is removed, Scout→Attacker remains legal. |
| F — actor legality | PASS | Existing T0/T1 actor-boundary tests plus EDR tests passed. |
| G — baseline non-regression | PASS | Existing SG adapter and telemetry regressions passed. |
| H — deterministic forward | PASS | Same EDR checkpoint/state produces identical deterministic actions. |

The audit ran eight regression tests in total.  The first unsuccessful audit
selection was discarded because it chose an F0 episode with no legal direct
Scout→Attacker edge; the accepted run uses the frozen telemetry record matching
the specified topology transition.  No long EDR MARL trajectory was run during
the audit.

