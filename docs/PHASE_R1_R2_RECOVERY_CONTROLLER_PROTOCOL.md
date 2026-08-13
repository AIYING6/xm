# Phase R1–R2 Recovery Controller Protocol

**Protocol ID:** `PHASE-R1-R2-RC-V1`  
**Status:** FROZEN BEFORE EXECUTION  
**Training:** prohibited

## Geometry gate

The initial Scout–Attacker separation must be greater than their effective
direct communication limit, while the initial Scout–Relay and Relay–Attacker
links can support the primary chain.  The optimistic closing-time calculation
must be shorter than the post-fault horizon.  This is a read-only necessary
condition, not a performance result.

## Fixed recovery controller

Before failure, both transparent arms use the already defined deterministic
`structural_oracle` or `legal_observation` pursuit controller.  After the
pre-registered relay-1 failure, the controller is augmented by one fixed rule:

```text
Scout and Attacker steer toward each other at their available speed;
Relay follows the same deterministic pursuit rule.
```

The rule has no access to target truth for the legal-observation arm.  It uses
only the known failure state and local relative UAV geometry.  The rule does
not add a communication edge, edit a cache, or call a hidden recovery signal.

## Recovery evidence

Recovery is recorded only when, after a strict post-fault loss, the attacker
has a fresh post-fault target cache with path `[0, 2]`, or a separately logged
terminal direct sensing event inside the frozen terminal envelope.  A stale
relay cache is never recovery.

The executor must preserve timestep-level positions, communication adjacency,
cache path, cache delivery step, direct detection, failure state, and the four
episode endpoint flags.  It must not run MARL or read checkpoints.

## Pass rule

For every controller×seed cell of 100 episodes:

- at least 10 episodes must establish the pre-failure relay path;
- at least 80% of eligible episodes must lose legal attacker information;
- at least 50% of lost episodes must recover through a post-fault legal direct
  path or terminal sensing event;
- every recovery must have a post-fault delivery/sensing timestamp.

If any cell fails, R2 is `INFEASIBLE`; no training starts and no geometry,
endpoint, failure window, or seed set is changed in response.
