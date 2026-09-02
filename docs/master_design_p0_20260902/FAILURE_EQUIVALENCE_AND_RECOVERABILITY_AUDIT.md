# Failure equivalence and recoverability audit

Before training, enumerate all masks allowed at each scale and calculate the task-relevant signature:

`(directed edge set, role-labelled degree vector, SCCs, legal reachability, path count, edge-disjoint count, internally-node-disjoint count, shortest legal route, cut edges/nodes, redundancy tier)`.

Masks with the same signature **and** same actor-observable/legal-action consequence are one condition; they are not duplicated as separate samples. A condition is Tier R only if at least one legal information route and a physically reachable success maneuver remain. Tier C has a route but low redundancy or tight message-age/rerouting margin. Tier I has no legal success route and is excluded from ordinary mean-performance comparisons.

Expected main-scale B target: at least five recoverable equivalence classes after symmetry collapsing, at least two critical classes, and at least one explicit impossible cut-set reference. Failure to meet three genuinely different recoverable classes is a benchmark stop/redesign gate.
