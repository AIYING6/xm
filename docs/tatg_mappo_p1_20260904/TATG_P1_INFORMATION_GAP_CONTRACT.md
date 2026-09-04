# TATG-MAPPO P1 — topology-transition information gap

**Status:** `ZERO_TRAINING_POLICY_NEUTRAL_DIAGNOSTIC`.

## Precise question

P1 does **not** ask whether an old DRTP seed diverged, whether a policy will
obtain higher return, or whether the complete continuous observation is
non-Markov. It asks a smaller, falsifiable question:

> Can the current actor-legal *structural topology snapshot* distinguish a
> stable graph from a graph that has just lost or recovered a communication
> relation, after retaining the current edge-age proxy already exposed by the
> environment?

The candidate memory is exactly one preceding legal structural graph snapshot.
Its target is the transition class computed from the difference between two
consecutive legal communication-relation adjacencies. No hidden failure field
is exposed to a candidate policy or retained in a P1 row.

## Frozen diagnostic

Both cohorts contain ten fresh, disjoint state seeds. They use an identical
non-learning script: straight target motion, zero random dropout, fixed neutral
action index 13 for every blue UAV, one existing relay failure, and 32 captured
steps. The relay failure timing is used by the environment to generate a
transition; it is forbidden from the actor interface and is absent from the
ledger.

The current topology code contains only actor-legal communication and
task-support relations plus current blue-blue edge message ages. Thus the
existing snapshot age proxy is given full credit. Geometry, target state,
centralized share observations, return and reward are deliberately excluded
because P1 is about a topology representation, not a claim about the entire
continuous actor observation.

## Decision rule

Each cohort must independently contain at least ten loss and ten recovery
events, at least ten rows whose current topology code maps to more than one
transition label, and zero mixed-label one-step history codes. All labels are
deterministic set-membership counts; no classifier or fitted threshold is used.

`TATG_P1_INFORMATION_GAP_PRESENT` means only that a local topology-transition
residual has an information-theoretic role beyond the frozen structural
snapshot. It does **not** authorize a recurrent policy, an algorithm claim or
any PPO run. `TATG_P1_NO_INFORMATION_GAP` closes this route before any method
implementation.

## Novelty guard after a pass

The next audit must require a transition residual with an exact local update
rule and compare it fairly against both snapshot SG-MAPPO and capacity-matched
generic GNN+GRU. A pass cannot be used to rename a generic recurrent encoder as
TATG.
