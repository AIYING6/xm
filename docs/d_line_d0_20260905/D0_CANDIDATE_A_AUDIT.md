# D0 Candidate A — Failure-Aware Service Continuity Reconfiguration

## Verdict

`A_HARD_GATE_FAIL_NEAREST_NEIGHBOR_AND_SOLVER`.

The system problem is real, and its capacity-versus-continuity choice is genuinely temporal. It is not, however, a clean new deterministic-algorithm problem on the present evidence: the closest UAV and networking work already covers the proposed decision core, and the unrestricted formulation is a standard time-expanded multi-commodity-flow / assignment MILP.

## Reality boundary

| Category | Audited conclusion |
|---|---|
| Native system semantics | Multi-hop relay links have finite capacity; a route can fail; an active service may require migration without interruption. These are supported by A1–A4 in the nearest-neighbor matrix. |
| Reasonable abstraction | A service has a release, deadline, demand, route, and a one-slot migration/reconfiguration cost. |
| Unsupported as a core claim | A particular continuity deadline, switching price, or service priority chosen solely to force a proposed method to win. Those would have to be deployment-specified before any D1 contract. |

## Real competing decisions and deterministic counterexample

At slot 0 a single relay resource can either migrate service 1, yielding immediate utility 6, or be reserved so that service 2 can meet an unrecoverable continuity deadline at slot 1, yielding utility 10. Both actions are feasible at slot 0; capacity one makes them mutually exclusive. Greedy immediate migration returns 6 while reserve-then-serve returns 10. The difference is a hard future deadline, not a tuned scalar penalty. The executable fixed toy is in `D0_COUNTEREXAMPLE_TRUTH_TABLE.csv`.

This passes the *existence of a non-myopic conflict* test. It does not prove a new problem: A1 already has limited A2A capacity, route refreshment/resource allocation, connection migration, and a disruption-free migration condition; A2 separately addresses online failure reconfiguration.

## Nearest-neighbor attack

The closest works are A1–A8 in `D0_NEAREST_NEIGHBOR_MATRIX.md`.

- A1 is direct multi-hop UAV relay reconfiguration and already uses ILP for route refreshment plus a seamless-migration condition.
- A2 is direct failure-aware online UAV communication reconfiguration with capacity/overhead considerations.
- A3–A4 cover multi-UAV relay resource competition and freshness-sensitive trajectory/resource allocation.
- A5–A8 cover hard AoI feasibility, bandwidth scheduling, and dynamic reconfiguration delay/cost.

Therefore “failure + UAV + service continuity + relay capacity” is a composition of covered axes, not a demonstrated conceptual separation.

## Solver and theory audit

The natural binary variables are service-to-relay assignment, path use, migration, capacity reservation, and time. With normal flow conservation and deadlines, this is time-expanded multi-commodity flow plus switching binaries. Standard baselines would be MILP, min-cost flow/matching special cases, rolling-horizon MPC, and Lyapunov online control.

A worthwhile theorem would require a *new, source-native restriction* yielding, for example, an integral interval-flow relaxation or an online competitive ratio under disruption-free migration. No such restriction is presently identified that is not already within A1/A2/A5–A8. Complexity notation alone is not a contribution.

## Determinism, assets, and decision

An instance-driven deterministic benchmark is straightforward, but the current repository lacks transition-effective route, relay-capacity, and migration actions. Building those later would be permitted only after a problem passes novelty; it cannot rescue A now.

**Hard-gate result:** reality ✓; competing choice ✓; strict toy ✓; deterministic evaluation ✓; TG-VM separation ✓; nearest-neighbor novelty ✗; non-generic solver ✗; theory target ✗. Candidate A is not a D-line winner.
