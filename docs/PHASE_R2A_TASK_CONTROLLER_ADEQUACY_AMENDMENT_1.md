# Phase R2-A Task/Controller Adequacy Amendment 1

**Protocol:** `PHASE-R1-R2-RC-V1`  
**Amendment:** `R2A-A1`  
**Status:** FROZEN BEFORE RE-EXECUTION

## Purpose

This amendment addresses the diagnosed adequacy problem without changing the
scientific endpoint, communication radius, information TTL, failure timing,
development seed set, or recovery definition.

## Frozen controller behavior

Before the relay fault, the transparent controllers use an explicit formation
layer in addition to their existing pursuit action:

1. Scout maintains target pursuit while remaining the only long-range target
   sensor.
2. Relay maintains a bounded geometric midpoint between Scout and Attacker so
   both Scout→Relay and Relay→Attacker communication links remain eligible.
3. Attacker follows the delivered target track but is constrained to remain
   outside the terminal sensing envelope before the fault.

After the frozen relay-1 fault, the existing recovery guidance is used: Scout
and Attacker move toward the legal direct-link geometry.

This is a transparent-controller protocol amendment, not a learned-policy
result and not a new model architecture.

## Frozen trigger guard

The failure trigger is allowed only when all of the following are true for two
consecutive timesteps:

```text
Scout has direct target detection
Scout->Relay communication is active
Relay->Attacker communication is active
Attacker has fresh relay-routed cache
Scout->Attacker communication is inactive
Attacker direct target detection is inactive
Attacker is outside terminal sensing range
```

The guard prevents an episode that already has a legal alternative path from
being misclassified as a Relay-critical episode. It does not force a new edge
or modify communication geometry.

## Frozen outcome gates

The existing R2 cell rules remain unchanged:

- at least 10 eligible episodes per controller×seed cell;
- at least 80% strict information loss among eligible episodes;
- at least 50% legal recovery among lost episodes.

All raw timestep provenance must be retained. If any cell fails, the result is
`R2-INFEASIBLE` and no MARL training starts.

## Prohibited changes

No changes are permitted to the primary recovery endpoint, cache TTL,
communication radius, failure duration, episode horizon, development seeds,
canonical seeds, or MARL training configuration during this re-execution.
