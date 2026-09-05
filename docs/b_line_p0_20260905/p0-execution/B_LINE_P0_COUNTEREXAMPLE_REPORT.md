# B-line P0 deterministic counterexample

**Verdict:** `B_P0_CONDITIONAL`.

The two scenarios have identical current geometry, current adjacency and remaining mission demand. Their only decision-relevant difference is the legal transition-history summary: current consecutive outage duration.

## Result

- Same current snapshot SHA-256: `7f5640f258e44086bfb926a9f61c21872a705b7c18977962309a1d826ccaebf5`.
- Newly disconnected: `continue_mission`.
- Persistent disconnected: `reconfigure_relay`.
- A snapshot-only deterministic rule must either violate the persistent-outage continuity constraint or choose a dominated reconfiguration in the newly-disconnected case.

## Boundary

This proves existence only under the frozen continuity contract. It does not establish that the present UAV environment exposes, requires, or can legally measure this duration state. That semantic alignment is the unresolved prerequisite for any P1 formalization.
