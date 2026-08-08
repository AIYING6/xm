# Paper Evidence Pack

## Central question

Under strict intermittent sensing, limited communication, and temporary relay failure, can task-graph-driven multi-relation coordination improve the *timing* of heterogeneous UAV team recovery rather than only terminal task completion?

## Central claim

Within the locked nominal 3DOF held-out distribution, EA-RG provides a reproducible early post-failure recovery advantage over MAPPO; its full-horizon recovery is competitive rather than uniformly superior, and its zero-shot transfer is distribution-dependent.

## Evidence chain

1. **Primary:** matched-exposure KM/RMST analysis on locked held-out episodes; RMST80 carries the most stable cross-seed Full-vs-MAPPO signal.
2. **Supporting:** held-out reliability, controlled graph baselines, ablations, Gate Prior trajectory analysis, and robustness conditions.
3. **Boundary:** P3-A frozen zero-shot OOD aggregate and family decomposition.
4. **Diagnostics:** Task-Support temporal windows, Role-Pair non-benefit, per-cell OOD saturation, profiling details, and representative cases.

## Implementation chain

The environment supplies 3DOF constraints, strict sensing, delivered communication adjacency, delay, dropout, and relay failure. The actor uses no-graph, single-graph, or multi-relation graph encoders; the multi-relation path has perception, communication, and task-support adjacencies, edge-aware attention, and an optional static role-pair gate initialized by Gate Prior.

## Explicit boundary

No evidence supports full 6DOF JSBSim execution, realistic radar/missile closure, human-UAV teaming, universal OOD generalization, or independent value of static Role-Pair Modulation.
