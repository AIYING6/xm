# G0 Frozen Unseen-Topology Suite

**Status:** development-only, frozen before policy evaluation.  
**Graph convention:** `A[receiver, sender]`; a listed `(src, dst)` removal sets
`A[dst, src]=0`.  
**Episode contract:** 50 deterministic episodes per condition, namespace
`950000–950049`; all frozen policies receive the identical episodes.

The suite uses only existing evaluation-side environment controls:
`comm_topology_mode={none,symmetric_longest_prune,directed_longest_prune}`
and existing node-failure semantics. It does not alter reward, dynamics,
actor observations, or policy parameters.

| ID | New structural property | Removed / unavailable communication | Preserved task structure | Class |
|---|---|---|---|---|
| U1 | unseen failure location | Scout-0 incident edges, steps 44–123 | Relay and Attacker remain; terminal attacker sensing remains legal | DEGRADED_BUT_FEASIBLE |
| U2 | unseen symmetric long-edge deletion | static `0→2` and `2→0` | `0↔1↔2` remains connected | FEASIBLE |
| U3 | unseen directed edge deletion | static Scout→Attacker `0→2` only | reverse direct edge and relay paths remain | FEASIBLE |
| U4 | unseen multi-edge / location shift | Scout-0 failure plus static direct-edge deletion | Relay--Attacker path remains during Scout failure | DEGRADED_BUT_FEASIBLE |
| U5 | connectivity-reducing directed path shift | Relay-1 failure plus static `0→2` deletion | reverse `2→0` direct communication and legal local terminal sensing remain | DEGRADED_BUT_FEASIBLE |
| U6 | diagnostic severe combined deletion | Relay-1 failure plus static `0↔2` deletion | no guaranteed forward information path | PHYSICALLY_INFEASIBLE_DIAGNOSTIC_ONLY |

`U6` is retained for transparency but excluded from the **primary** structural
generalization aggregate, because its post-onset forward communication graph
can become disconnected. U1–U5 are the primary suite. The static longest pair
is deterministic under the frozen business geometry: Scout `0` and Attacker
`2`. No topology may be deleted or added after results are observed.

For comparison, the same frozen tape additionally contains a nominal
reference, seen Relay-F0 `(44,80)`, timing parameter OOD `(20,80)`, and
duration parameter OOD `(44,140)`. Those two parameter cases are not claimed
to be structurally unseen.

## Pre-registered G0 decision quantities

The primary evidence is the five clean T1 UTR seeds and U1–U5. For each seed,
`structural gap = J_seen_F0 − mean(J_U1…J_U5)` and `parameter gap =
J_seen_F0 − mean(J_timing,J_duration)`. U6 is never included in this primary
aggregate.

- **A:** median structural gap exceeds `max(10, 15% × |J_seen_F0|)`, its
  median excess over the parameter gap exceeds `max(5, 10% × |J_seen_F0|)`,
  at least 4/5 seed differences are positive, and at least 3/5 primary
  topologies exceed the pooled structural-gap threshold.
- **B:** not A, but median structural gap exceeds `max(5, 5% × |J_seen_F0|)`,
  median structural-minus-parameter gap is positive, and at least 3/5 seeds
  have a positive structural-minus-parameter difference.
- **C:** otherwise, or if a primary condition fails legality/feasibility.

These criteria were added and frozen before any G0 rollout. They identify a
problem gap; they do not establish a new method or authorize training.
