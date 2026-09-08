# 6-UAV V3 Q0 outcome

**Protocol:** `DRTP-6UAV-V3-SUSTAINED-SUPPORT-Q0-V1`
**Verdict:** `V3_Q0_PASS`
**Evidence status:** environment-semantic diagnostic only; not manuscript
performance evidence.

The scripted feasibility witness verified the intended task semantics for two
deterministic seeds:

| Condition family | Witness endpoint | Interpretation |
| --- | --- | --- |
| Nominal | both objectives complete in 3 transitions | two relays concurrently provide fresh support. |
| Single upstream/downstream fault | both objectives complete in 3 transitions | a relay reassignment remains legal and sufficient. |
| Balanced compound fault | both objectives complete in 3 transitions | redundancy remains usable under nontrivial edge loss. |
| Relay-node/cross/same-relay capacity fault | exactly one objective complete by the deadline | the failure creates a sustained partial service deficit, not an all-route cutset. |

This Q0 pass permits only the next engineering phase: an independently
specified UTR-only learnability pilot after a flexible relay action head and
matching runner are audited. It does not establish that a learned UTR policy
will recover, that DRTP will improve, or that V3 is admissible for the main
paper.
