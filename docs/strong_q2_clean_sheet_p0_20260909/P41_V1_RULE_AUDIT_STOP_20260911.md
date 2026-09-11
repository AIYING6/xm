# P41 v1 rule audit: stop

## Verdict

`P41_T1_T3_STOP` — no learning is authorized.

## What was checked

The minimal recoverable-service-chain environment was smoke tested with the
standard environment interface. Four legal simple policies (static assignment,
value-greedy, earliest-deadline, and topology-greedy) and an audit-only oracle
were rolled out on the three predeclared scenarios.

Source:
`artifacts/diagnostics/p41_recoverable_service_chain_rule_audit_20260911_v2/P41_RULE_AUDIT.json`.

## Why it stopped

All four non-oracle rules completed all available requests in every scenario.
The audit consequently found no unique rule winner, no cross-scenario rule
reversal, and no gap between the simple rules and the oracle. Relay
reconfiguration occurred, but it imposed no consequential opportunity cost.

This means the v1 task contains an event sequence but not a discriminative
coordination decision. It must not be made harder by blindly changing a deadline
or a reward coefficient until a desired method wins.

## Permitted v2 reconstruction principles

Any replacement task must introduce the following semantic properties together,
then rerun a newly frozen rule audit:

1. A service commitment must consume enough time/capacity that accepting a
   currently known request can preclude a later request.
2. The later request must be forecastable through a legal, imperfect public or
   local signal; otherwise no legal policy can make a meaningful defer/commit
   choice before its release.
3. Relay relocation must create a temporary coverage loss that can invalidate a
   currently useful information chain, not merely delay a redundant one.
4. At least one scenario must favor early commitment, and another must favor
   deferral/reconfiguration. The task cannot pass if all simple policies tie or
   one fixed policy is near the audit oracle throughout.
5. The actor must never receive future request truth, the oracle allocation, or
   the final evaluation tape.

The next artifact is a **new task contract**, not a parameter tweak to P41 v1;
no DRTP, PLR, or new learner is authorized until that contract passes T1--T3.
