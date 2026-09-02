# MASTER_DESIGN_P0 contract

**Protocol:** `MASTER-DESIGN-P0-ZERO-TRAINING-V1`  
**Scope:** static scientific and engineering design only.  
**Status:** complete; P1 is not authorized.

This audit creates a separate future benchmark namespace, `redundant_topology_uav`, and preserves the frozen 3-UAV Scout--Relay--Attacker A-line unchanged. It performs no environment import, modification, rollout, policy evaluation, new-seed creation, hyperparameter sweep, or training.

The P0 decision is intentionally narrower than a research claim: the layered redundant-topology question is justified, but the present 3-UAV implementation is not a scalable generator and cannot be repurposed without a new semantic specification. Therefore the only valid final verdict is `MASTER_DESIGN_REQUIRES_REDESIGN`.

## Non-negotiable future gates

1. Prove actor-side task-information legality for every nominal and failure graph.
2. Freeze role differentiation, success semantics, and normalized reward/metric definitions before implementation.
3. Implement a new generator in an isolated namespace; do not patch the frozen A-line environment.
4. Pass graph-equivalence, recoverability, information-boundary, smoke, and comparator-mapping gates before any learning experiment.
5. No candidate method is predeclared the winner; all training-distribution methods remain hypotheses.
