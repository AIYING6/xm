# Phase R2B Business-Grounded Relay-Dependent Operating Window

**Protocol ID:** `PHASE-R2B-BGW-V1`  
**Status:** FROZEN DESIGN — final recovery-task design attempt  
**Training:** prohibited until R2B passes

## Operational rationale

The mission is not a compact formation. The Scout occupies a lower search
corridor, the Attacker occupies an upper standoff/terminal-preparation
corridor, and the Relay occupies the bridge corridor between them. The
separation is operational: the attacker does not enter the scout's search
sector before a failure, while the relay provides the cross-sector track link.

The frozen operating window is therefore:

```text
Scout -> Relay communication       = true
Relay -> Attacker communication    = true
Scout -> Attacker communication    = false
Attacker terminal target sensing   = false
Scout target sensing               = true
```

The role regions are defined relative to the target reference position
`(10,000, 0, 5,000)`:

- Scout search corridor: lower lateral sector, with target distance within the
  Scout radar envelope;
- Attacker standoff corridor: upper lateral sector, outside direct Scout–
  Attacker communication and outside terminal sensing range;
- Relay bridge corridor: the midpoint corridor between Scout and Attacker,
  satisfying both communication hops.

After Relay failure, the mission priority changes: Scout and Attacker may
leave their nominal corridors and reposition until a legal post-fault direct
Scout→Attacker link is formed. This is an explicit mission-position versus
communication-resilience trade-off, not a free graph edge.

## Frozen geometric window

For a candidate state, with `R_SA` the effective Scout–Attacker direct
communication limit:

```text
d(S,R) <= R_SR
d(R,A) <= R_RA
d(S,A) > R_SA
d(A,T) > terminal_sensing_range
d(S,T) <= scout_radar_range
```

The recovery condition is:

```text
(d(S,A) - R_SA) / (v_S + v_A) < remaining_horizon_after_failure
```

The map must distinguish `relay_dependent`, `direct_bypass`, `disconnected`,
and `recovery_unreachable` states. Communication radius, TTL, endpoint,
failure duration, and recovery definition are not adjusted to obtain a map
PASS.

## Transparent gates

R2B uses fixed role-specific mission-position controllers, not compacting
formation control:

1. **P — Pre-establishment:** the Scout senses the target and both relay hops
   remain active for two consecutive observations.
2. **L — Loss dependency:** at the frozen Relay-1 failure, no direct
   Scout–Attacker communication, terminal attacker sensing, stale alternative,
   or hidden graph route is available; the strict attacker information state
   must become unavailable.
3. **R — Recovery:** after loss, the fixed repositioning rule produces a new
   post-failure legal Scout→Attacker path or terminal sensing event.

The same cell thresholds remain: at least 10 eligible episodes per
controller×seed cell, at least 80% loss conditional on eligibility, and at
least 50% recovery conditional on loss. The bypass audit is mandatory for
every trigger.

## Stop rule

R2B is the final recovery-task design attempt. If a business-grounded map and
transparent replay do not satisfy P/L/R without outcome-driven parameter
changes, the strict relay-recovery claim is closed. The project may then
continue only as a bounded heterogeneous communication/task-graph robustness
study. No R2C or R2D task patches are permitted.
