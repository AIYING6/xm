# Phase 2I Scientific Validity Audit — Closure

**Status:** CLOSED  
**Scope:** original nominal 3-UAV task and the first opt-in relay-dependent P0/P1 probe  
**Training status:** no canonical or formal training started

## Final finding

The original nominal task does not support a relay-dependent recovery claim.
Phase 2IA9 established that the attacker retained a direct target-information
route at every audited trigger and failure-active timestep.  The resulting
failure was a task-dependency mismatch, not evidence that the policy or
Role-Gate was ineffective.

The first opt-in Phase2IB P0 semantics correctly removed direct attacker
sensing and required a relay-routed cache.  Its frozen P1 transparent probe
then produced the following result in all six controller×seed cells:

| Cell criterion | Result |
| --- | ---: |
| Dependency eligibility | 100/100 episodes |
| Relay-channel loss after fault | 100/100 eligible episodes |
| Post-loss rebuild | 0/100 lost episodes |

Therefore P1 is `P1-INFEASIBLE` under the preregistered rule.  This is a
valid negative feasibility result: the P0 semantics created a dependency and
loss, but did not yet create a physically reachable alternative recovery path.
The P1 output is development-only and is not a performance result.

## Decisions

- Close the Phase 2IA audit chain; do not create IA10/IA11 patch stages.
- Keep Role-Gate retention `UNRESOLVED`; do not infer retention from this
  task-feasibility result.
- Archive original-task results as invalid for the relay-recovery claim; do
  not delete or rewrite their evidence chain.
- Do not start MARL training, canonical evaluation, survival/RMST analysis, or
  Phase 3A.
- Open the separately numbered `Phase R0–R2` scientific task redesign.

## Evidence boundary

The result supports only this statement:

> The original task lacked the intended relay dependency, and the first strict
> relay-dependent implementation created pre-fault eligibility and fault-time
> loss but no recoverable alternative path under its fixed P1 probe.

It does not support a claim about algorithm superiority, Role-Gate value,
success rate, recovery probability in a redesigned task, or publication
headline performance.
