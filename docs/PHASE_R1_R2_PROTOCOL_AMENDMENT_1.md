# Phase R1–R2 Protocol Amendment 1

**Protocol:** `PHASE-R1-R2-RC-V1`  
**Amendment:** `A1`  
**Status:** FROZEN BEFORE RE-EXECUTION

## Reason for amendment

The first implementation replay exposed two execution-semantic mismatches:

1. In relay-dependent mode, Relay 1 could still satisfy the generic radar
   predicate and generate a direct `[1,2]` cache. This is not the frozen R0
   operational task, whose long-range target sensor is Scout 0.
2. The legacy `success -> done` rule could terminate a transparent episode
   immediately after the pre-failure chain closed, before the pre-registered
   failure and recovery window was observed.

These are implementation/protocol-consistency defects, not outcome-driven
changes to geometry, communication range, failure timing, seeds, or endpoint.

## Frozen amendment

When `relay_dependent_task=True`:

- Scout 0 remains governed by the existing radar geometry and may generate
  target detections.
- Relay 1 may forward delivered track information but may not originate a
  direct target detection.
- Attacker 2 may directly sense only within the frozen terminal sensing range
  and FOV; outside that range it requires legal delivered information.

For R1/R2 transparent feasibility replay only, set
`min_success_step=1000` while the episode horizon remains 260 steps. This
prevents legacy terminal success from censoring the frozen failure/recovery
window. Collision, constraint, and timeout behavior remain unchanged. The
development artifact is mechanism-only and is not a performance result.

No other parameter or definition changes. The primary endpoint remains:

```text
pre_failure_chain_established
AND chain_lost_after_failure
AND post_failure_chain_recovered_after_loss
```

The original failed replay is retained as an implementation audit artifact and
is not overwritten or relabeled as a result.
