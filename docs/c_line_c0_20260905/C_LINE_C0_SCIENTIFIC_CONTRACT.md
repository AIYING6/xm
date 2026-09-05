# C-Line C0 scientific contract

**Protocol:** `C-LINE-C0-PROBLEM-NOVELTY-REALISM-GATE-V1`
**Purpose:** falsify the candidate deterministic problem before designing an algorithm.

## Candidate question under attack

Can a deterministic controller jointly choose time-coupled relay-route reconfiguration and competing freshness-constrained service assignments after UAV-network failures in a way that is neither a snapshot-greedy scheduling problem nor a relabelled semantic-map planner?

The candidate is not granted novelty because it mentions UAVs, faults, AoI, service, or reconfiguration.  Each of those elements already appears in prior work.

## GO rule

`C0_GO` requires all six conditions:

1. source-supported task semantics;
2. at least two genuinely competing decision variables;
3. a strict, fixed non-myopic counterexample;
4. no nearest publication fully covers the proposed formal problem;
5. an identified non-generic solver/theory opportunity; and
6. TG-VM non-overlap.

## Frozen prohibitions

No solver, environment modification, training, RL, formal benchmark, weight tuning, checkpoint selection, evaluation-tape access, or automatic C1 transition is allowed in C0.

## Decision

The gate is intentionally conservative: `C0_CONDITIONAL`, not GO.  The strict counterexample establishes a real *class* of non-myopic decision conflict, but the closest-work and solver-structure attacks remain unresolved.
