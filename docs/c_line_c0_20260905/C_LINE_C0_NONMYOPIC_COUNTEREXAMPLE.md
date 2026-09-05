# C-Line C0 strict non-myopic counterexample

This is a fixed two-slot truth table, not a solver and not a benchmark.  It tests whether a candidate problem can contain a real decision conflict that a current-slot payoff rule cannot resolve.

## Frozen toy semantics

- One relay-capacity unit is available at each of slots 0 and 1.
- Service A can be completed immediately at slot 0 and has priority 6.
- Service B has priority 10 and a hard slot-1 deadline.
- Under a disruption-free migration requirement, B's route must reserve the only capacity unit at slot 0 before B may be served at slot 1.
- The two decisions at slot 0 compete for the same unit: serve A now, or reserve it to migrate B's route.

| Rule/policy | Slot-0 action | Current payoff | B feasible at deadline | Two-slot completed priority |
|---|---|---:|---:|---:|
| Myopic | serve A | 6 | No | 6 |
| Finite-horizon | reserve capacity for B migration, then serve B | 0 | Yes | 10 |

Thus the unique one-slot optimum is not the unique two-slot optimum: `6 > 0`, whereas `10 > 6`. The conflict uses two separate decisions—service selection and route-migration reservation—and a hard deadline, rather than a tuned penalty.

## Boundary

The concept of limited-capacity disruption-free migration is source-supported by N1. The exact two-slot latency and the numerical priorities are reasonable illustrative abstractions, not native measurements from the present environments. Therefore this proves that a C-line formulation *can be non-myopic*; it does not validate a final model, a solver, or a paper claim.
