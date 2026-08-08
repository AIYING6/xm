# NO_GRAPH_BASELINE_INVARIANCE_AUDIT_V1_8

**Result: PASS for the tested fixed trajectory; MAPPO/HAPPO checkpoint reuse is
conditionally permitted under the frozen protocol.**

## Audit design

Legacy v1.6 was loaded directly from git revision `f0c7f57` while corrected v1.8
was loaded from the repaired working tree. Both environments used the same
configuration, seed `431`, one-step packet delay, zero stochastic dropout, a
fixed 12-step multi-agent action sequence, and the same relay-failure window
(agent 1, steps 4–7). The audit compares the actual no-graph environment path,
not graph tensors.

The script is [audit_no_graph_baseline_invariance_v1_8.py](../scripts/audit_no_graph_baseline_invariance_v1_8.py).
Observed result: `PASS (12 transitions, seed=431)` with exact array equality and
scalar equality (tolerance `1e-6`).

## Compared quantities

At reset and every transition, the audit compared:

- each agent observation and centralized `share_obs`;
- rewards and done flags;
- success, collision, constraint violation, and derived termination reason;
- blue UAV position, speed, heading, climb state, and energy;
- target position, speed, heading, and climb state;
- relay-failure activity timing;
- sensing outcome (`detected_by`) and attack-window logic;
- all emitted `info` fields, including timeout/chain/connectivity metrics.

## Interpretation

The v1.8 packet and graph repair adds recipient-specific actor graph views and
sender-status caches. It does not alter the tested no-graph observation,
physics, reward, transition, termination, sensing, target, or failure process.
Therefore the existing MAPPO/HAPPO checkpoints may be reused as frozen
system-level comparators under the R7 protocol. This is not evidence that their
actor information matches corrected graph methods; it only establishes
trajectory-level environment invariance. If a future configuration changes any
of the audited quantities, reuse is revoked and MAPPO/HAPPO must be retrained.

This is one fixed-seed/action audit, not a performance result or a substitute
for formal evaluation.
