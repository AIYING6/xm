# C-Line C0 theory and solver potential

## Attack

With binary service assignment, multihop routing, per-link capacity, switching/migration constraints, and time, the unqualified candidate naturally expands into a time-expanded multi-commodity flow / assignment MILP. That is a legitimate benchmark model, but it is not a high-ceiling deterministic algorithm contribution by itself. Generic MILP, greedy age ordering, min-cost flow, matching, or a standard rolling horizon controller would not satisfy the intended solver novelty.

The closest UAV-relay study already uses ILP route refreshment and derives a disruption-free migration condition (N1). The AoI literature already contains exact and low-complexity feasibility schedulers with guarantees (N5, N7). C0 has not shown a property that survives both bodies of work.

## What would be required before C1

Only a zero-training C0R audit may proceed, and only if it freezes one restricted problem that supplies all of the following before implementation:

1. a formal separation from N1's route refreshment and N5/N7's AoI scheduling;
2. a precise structural property, such as a provably lossless decomposition, matroid/flow integrality condition, exchange property, approximation bound, or online competitive/regret guarantee;
3. a proof that the property is not recovered by ordinary min-cost flow, matching, greedy deadline scheduling, generic MILP, or MPC;
4. an explicit account of which semantics are source-supported and which require a new benchmark contract.

Without all four, the appropriate result is `C0R_NO_GO`, not a solver implementation.
