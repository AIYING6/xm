# EDR-Q2 — Structural Property Audit

## Protocol

`EDR-Q2-STRUCTURAL-PROPERTY-AUDIT-V1` uses only a frozen seed-2202 final SG
checkpoint and real F0 telemetry. It constructs no environment, performs no
rollout or optimizer update, and writes no model asset. Output:
`results/development/edr_q2_structural_property_audit_run2/edr_q2_structural_property_audit.json`.

## Results

| Test | Result | Status |
|---|---|---:|
| A: SG vulnerability | Legal Relay→Attacker deletion changes surviving softmax weights by max `0.05372`, surviving contribution L2 by `0.09666`, and receiver aggregate L2 by `0.25877`. | PASS |
| B: EDR locality | Surviving gate max change `0.0`; surviving contribution L2 change `0.0`. | PASS |
| C: Relay relevance | F0 onset is 44; actor graph at 43 has Relay→Attacker `1`, while actor graph at 45 has `0`; legal Scout→Attacker remains `1`. | PASS |
| D: structural action propagation | SG logit L2 change `0.76659`; analytical EDR logit L2 `0.41831`. | Diagnostic only |

The one-step timing is expected: failure becomes active after step 44, and the
actor first receives the updated graph at step 45. This is a real legal
topology transition, not an artificial blackout.

## Boundary

Test D is not performance evidence: EDR is an untrained, parameter-reusing
analytical prototype. The audit demonstrates a propagation pathway only. The
property is one-hop and pre-nonlinearity; multi-edge physical effects and
mission robustness require future training evidence.
