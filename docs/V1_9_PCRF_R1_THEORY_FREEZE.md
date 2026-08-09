# v1.9 PCRF-R1 Theory Freeze

**Status: D0-R1 implementation frozen; a new D1-R1 engineering validation is
required before D2. No training, held-out evaluation, OOD, or paper claim is
authorized by this document.**

## Decision

PCRF-R1 retains the D0 candidate's three recipient-specific legal relation
factors and removes neither actor-boundary masking nor the no-union-residual
constraint. It makes one narrowly scoped pre-D2 correction: relation fusion is
now defined as a baseline gate plus a conflict-conditioned deviation, rather
than treating equal sources as necessarily one-third each.

For receiver \(i\), let \(h_i^P,h_i^C,h_i^T\) be the perception,
delivered/cache-valid communication, and task-support factor outputs. Then

\[
w_i = \operatorname{softmax}(\log \pi_0 + \Delta(c_i)),\qquad
h_i = \sum_{r\in\{P,C,T\}} w_{ir}h_i^r .
\]

\(\pi_0\) is a learned but receiver-invariant baseline distribution. The
correction satisfies \(\Delta(0)=0\) exactly by subtracting its
zero-conflict response. Thus a no-conflict input recovers \(\pi_0\), not a
post-hoc equal-weight convention.

## Legal conflict descriptor

The descriptor is a function only of the receiver's already masked legal
graph view:

\[
c_i=[\tilde a_i^P,\tilde a_i^C,\tilde a_i^T,
d_{PC},d_{PT},d_{CT},\operatorname{age}_C,1-\operatorname{confidence}_C].
\]

Here \(\tilde a\) is relation support centered across the three factors, the
\(d\)'s are pairwise relation disagreement, and age/confidence are aggregated
only across actually delivered communication edges. No critic state,
simulator-global state, pending/dropped packet payload, or unavailable
teammate geometry may enter \(c_i\).

## Frozen mechanism predictions

1. With neutral conflict fields, PCRF-R1 gate equals its learned baseline.
2. Under a controlled legality-preserving conflict intervention, the gate may
   depart from baseline; the direction is a learned response, not a hard age
   monotonicity rule.
3. PCRF-R1 does not claim a large advantage when sources agree.
4. Any future performance advantage must be tested first against a strong
   single graph with the identical legal node/edge fields, relation/type
   identity, packet metadata, task compatibility, parameter budget, optimizer,
   rollout budget, selector, and evaluation episodes.

## Consequences for earlier engineering artifacts

D1's `D1_ARTIFACT_GATE_PASS` remains a valid audit of the prior PCRF candidate
and of the persistence pipeline. It is **not** evidence that PCRF-R1 has been
engineered on CUDA. Because PCRF-R1 changes the fusion semantics, a short
D1-R1 run must repeat the runtime, R5, D0-R1, snapshot, and event-record gate
before D2-R1 is allowed to start. No D1 score may be compared across the two
versions.

## D2 and F1 preconditions

Before D2-R1, record PCRF-R1 source commit/archive provenance and pass the
new D1-R1 artifact gate. Before F1, freeze all of the following without seeing
formal outcomes:

- five method-blocked training seeds for each of PCRF-R1, wider single graph,
  and matched-information non-graph;
- a method-independent training schedule and a shared confirmatory episode
  bank;
- a practical RMST80 effect threshold \(\delta_{\min}\), justified in units
  of the task control/communication time scale;
- the primary comparator and hierarchical paired-bootstrap implementation;
- controlled F2 conflict interventions and PCRF-R1 without conflict
  conditioning.

The numerical value of \(\delta_{\min}\) is deliberately unresolved here; it
requires an author decision based on the physical control interval, not a
value chosen after observing training results.
