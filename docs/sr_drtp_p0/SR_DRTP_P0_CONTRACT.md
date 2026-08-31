# SR-DRTP P0 contract

**Status:** `P0_IMPLEMENTATION_AND_TECHNICAL_AUDIT_ONLY`  
**Mainline A:** `FROZEN / UNCHANGED`  
**Long training:** `NOT AUTHORIZED`  
**Algorithm activation:** `NOT AUTHORIZED`

## Scientific question

Can read-only, training-only signals later identify training states in which a
stability intervention would be useful while healthy Original-DRTP trajectories
remain unchanged?

P0 does **not** answer this question empirically. It establishes only whether
the instrumentation and an update-boundary exact shadow branch are technically
sound enough for a separately authorized P1 to test the question.

## Historical boundary

The previous Selective-KLR Intervention Utility P1 is retained as negative
evidence for a **KL-only** gate: among 88 alarms, most rollback-minus-accept
probe differences were practically near zero and the few beneficial/harmful
events did not form a seed-level generalizable selector. It was an
accept-versus-actor-rollback probe, not a complete short training continuation.
It therefore neither establishes nor precludes a broader risk-state signal
using sampler, training-dynamics, and training-only probe observables.

The existing `MECHANISM_DISCOVERY_NO_GO` decision remains in force for all
previous local patches (TR, anchor, fixed KLR/KLB, PP, PR, CV and KL-only
selector). P0 grants no exception for an algorithm or a new trajectory.

## P0-authorized work

1. Audit Original DRTP, PP, S2 and KLR state/telemetry boundaries.
2. Add default-off, write-only SR-DRTP training telemetry.
3. Prove exact save/reload at an update boundary and an isolated exact-replay
   shadow continuation.
4. Record the limitations of prior KL-only shadow probes.

## Explicit prohibitions

- No cloud or local development training beyond CPU technical smoke tests.
- No sampler guard, PPO/update guard, selector, threshold tuning, parameter
  sweep, checkpoint promotion, early stopping, or performance rerun.
- No formal, independent, held-out, or manuscript evaluation tape in telemetry
  or shadow logic.
- No modification to Mainline A code, evidence, manuscript, or claims.

## P0 outcome

`P1_READY` requires all technical checks to pass:

- default-off produces no SR telemetry artifact and remains trajectory-exact;
- enabled telemetry is write-only and training-only;
- runtime snapshots retain model, optimizer, environment, observation,
  sampler, and RNG state;
- an exact-replay shadow from an update boundary matches an uninterrupted
  continuation exactly;
- the shadow manifest attests to no algorithm intervention or evaluation
  leakage.

Otherwise output `P1_NOT_READY` and stop. `P1_READY` is **not** a mechanism
GO and does not authorize P1 training.
