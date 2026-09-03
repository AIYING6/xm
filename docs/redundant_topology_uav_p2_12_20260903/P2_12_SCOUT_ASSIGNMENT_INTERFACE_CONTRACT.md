# P2.12 — Scout assignment-observation interface audit

## Motivation

P2.11 found zero distinct-objective coverage by final Scout policies across
all retained P2.9 policies. P2.12 tests a single minimal interface change:
append a frozen, role-local objective preference one-hot for Scouts in the
same existing assignment append block used by Terminals.

## Frozen semantics

- assignment is the y-lane rank bijection from initial geometry to objective
  y-lane rank;
- terminal mapping is unchanged;
- Scout mapping uses the same initial geometry and objective order;
- Relay receives zeros in the append block;
- the append block is available from reset and remains stable through an
  episode;
- default `assignment_observation=False` preserves the legacy observation
  shape and values exactly;
- enabling Scout preference requires `assignment_observation=True` and does
  not append a second block.

## Explicit non-changes

No reward, transition, topology, fault, action mask, route, deadline,
learner, PPO, sampler, evaluation tape, or training seed is changed.

## Scope

P2.12 is deterministic interface validation only. It does not run PPO,
training rollouts, policy evaluation, or checkpoint selection. A PASS only
permits a future fresh-seed learnability qualification request; it does not
authorize it automatically.
