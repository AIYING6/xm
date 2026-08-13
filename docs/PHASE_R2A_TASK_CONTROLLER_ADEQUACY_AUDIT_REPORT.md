# Phase R2-A Task/Controller Adequacy Audit Report

**Status:** DIAGNOSIS COMPLETE; amendment required before re-execution  
**Training:** not started  
**Canonical data/checkpoints:** not used

## Question

R2-A separates two possible causes of the R1–R2 gate failure:

1. the legal transparent controller cannot establish the intended
   Scout–Relay–Attacker information path; or
2. the Relay failure is not a sufficient cause of information loss because a
   terminal sensing or alternative direct path is already active.

No endpoint, TTL, geometry, failure timing, or seed set was changed during
this audit. The audit used 18 diagnostic-only episodes and timestep-level
telemetry.

## Findings

### A. Pre-failure establishment

The strict `relay_dependency_eligible_t` state was rare in the legal arm, even
though the attacker often had some legal target information. This confirms
that “attacker has information” is not equivalent to “the frozen primary
Scout–Relay–Attacker chain is established”. The legal controller was pursuing
the target from local observations but was not maintaining a formation that
simultaneously preserved both communication hops and Scout sensing.

The structural arm established the primary state more often, but not in every
episode. Its target pursuit also moved the attacker toward the target, which
could activate an alternative terminal sensing route.

### B. Failure dependency

During the relay fault, the Relay–Attacker communication edge was absent, as
expected. However, structural episodes still showed legal attacker information
because the attacker had either entered the terminal sensing envelope or had a
post-fault direct Scout–Attacker route. Those are legal information sources,
but they mean Relay failure is not the sole cause of loss in those episodes.

This is not evidence of a hidden graph channel. It is an inadequacy of the
eligibility/trigger condition for testing Relay criticality: it allowed a
pre-fault episode to enter the fault window without first excluding an already
available alternative path.

### C. Recovery

The previous A1 replay showed that among episodes that actually recorded a
strict information loss, the fixed repositioning controller recovered through
the legal alternative path in all observed cases. R2-A does not replace that
result or promote it to a new adequacy result.

## Root-cause classification

| Component | Diagnosis |
| --- | --- |
| Geometry | Direct recovery geometry is feasible. |
| Primary chain | Not reliably maintained by the current legal controller. |
| Relay criticality | Not guaranteed at fault trigger because alternative paths are not excluded. |
| Cache/TTL | No evidence in this audit that TTL alone explains the remaining legal information. |
| Recovery controller | Works after an actual strict loss in the observed sample. |

## Decision

R2-A confirms a controller/eligibility adequacy issue, not an algorithm issue.
No MARL training is authorized. The next action is a separately committed
amendment that requires:

1. a transparent formation controller that actively maintains Scout–Relay and
   Relay–Attacker communication while keeping the attacker outside the
   terminal sensing envelope before the fault; and
2. a pre-fault trigger condition that records the absence of direct
   Scout–Attacker communication and terminal attacker sensing.

The recovery endpoint remains unchanged. Phase 3A and Role-Gate retention
remain NO-GO/UNRESOLVED, respectively.
