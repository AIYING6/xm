# D0 Candidate C — Recovery-Aware State Migration / Reconfiguration

## Verdict

`C_HARD_GATE_FAIL_NEAREST_NEIGHBOR_AND_SOLVER`.

Recovery does not imply immediate failback is a real systems observation. But stateful service migration, reconfiguration delay/cost, handover cost, and failback/hysteresis are established networking problems. A UAV setting alone does not create a new algorithmic core.

## Reality boundary

| Category | Audited conclusion |
|---|---|
| Native system semantics | Stateful services have migration/interruption costs; recovered resources can be used later than physical recovery; handover/failback can cause churn. C1–C6 support this. |
| Reasonable abstraction | A temporary route reservation can be held after a link recovers, with a bounded switching/reinstatement cost. |
| Unsupported as a core claim | A recovery-uncertainty distribution or hysteresis coefficient picked after observing solver performance. |

## Real competing decisions and deterministic counterexample

At slot 0 an apparently recovered path can be used for immediate utility 5, or a temporary reservation can be held. Capacity one means immediate failback removes the only buffer required by a service deadline at slot 1; holding the reservation returns 8. Thus immediate failback is strictly suboptimal. This is a legitimate temporal coupling, but it is the classic failback/handover trade-off rather than evidence of an unexplored UAV problem.

## Nearest-neighbor attack

The closest works are C1–C7 in `D0_NEAREST_NEIGHBOR_MATRIX.md`.

- C1 and C2 formulate stateful SFC/cloud-network reconfiguration under delay/cost and migration trade-offs.
- C3 uses handover cost and hysteresis specifically to prevent association flapping.
- C4 defines service continuity as preserving service state.
- C5/C6 address fault-tolerant stateful VNF recovery and flow handover/state migration.
- C7 demonstrates failure-triggered online UAV network reconfiguration.

The candidate would therefore need a special recovery-state graph with a provably different property. No such property was identified before formulation.

## Solver and theory audit

The direct models are dynamic programming for small systems, time-expanded MILP, online control with switching costs, or standard hysteresis thresholding. Potential statements such as bounded switching or a threshold policy are already natural targets in handover/reconfiguration research. No new topology-specific decomposition or approximation structure is presently specified.

## Determinism, assets, and decision

This can be evaluated deterministically using fault/recovery traces, but the existing environments do not include explicit route state, service migration state, failback actions, or capacity reservation. The required new interface is large relative to the currently demonstrated novelty.

**Hard-gate result:** reality ✓; competing choice ✓; strict toy ✓; deterministic evaluation ✓; TG-VM separation ✓; nearest-neighbor novelty ✗; non-generic solver ✗; theory target ✗. Candidate C is not a D-line winner.
