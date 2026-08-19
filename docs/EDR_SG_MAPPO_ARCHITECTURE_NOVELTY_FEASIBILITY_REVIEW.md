# EDR-SG-MAPPO Architecture & Novelty Feasibility Review

**Review type:** zero-training architecture and prior-art feasibility review
**Date:** 2026-08-19
**Authorized candidate:** Edge-Deletion-Resilient SG-MAPPO (EDR-SG-MAPPO)
**Decision:** **C — NO_GO**

## 0. Scope, authority, and immutable history

This review is the author's prospective reopening of the architecture-level
Route-B question:

`ROUTE_B_ARCHITECTURE_METHOD_REOPENED_BY_AUTHOR`.

It does **not** change the historical result in
[`POST_TCR_ROUTE_DECISION_REVIEW.md`](POST_TCR_ROUTE_DECISION_REVIEW.md):
**R1 — FREEZE PROBLEM / BUILD SYSTEM-ROBUSTNESS PAPER** remains the project
fallback and the historical DRTP/TCR conclusions remain closed.  This review
does not implement EDR, create a tape, run a smoke test, train a policy, use a
held-out/canonical seed, or change the environment, reward, PPO, actor
information boundary, or Single-Graph baseline.

The review also excludes DRTP-style adaptive return weighting, curriculum or
adaptive exposure, TCR/SPC/other gradient surgery, reward redesign, checkpoint
selection, and any actor input containing a failure label, global topology,
shortest path, global route, or future link state.

## 1. Question and candidate claim boundary

The physical mechanism already established by the frozen task is:

\[
\text{relay-node failure}
\;\rightarrow\;
\text{legal communication-edge removal and path reconfiguration}
\;\rightarrow\;
\text{coordination degradation}.
\]

The candidate does **not** claim that a relay is always the sole information
path, that surviving messages are unchanged globally, or that an action must
be invariant to a deletion.  Its only proposed architectural property is much
narrower:

> Removing one incoming legal edge must not renormalize the pre-nonlinearity
> contributions of that receiver's other surviving incoming edges.

The proposed family can be written as

\[
\begin{aligned}
m_{ij} &= a_{ij}\,\gamma_{ij}\,
          \phi(h_j,e_{ij},r_i,r_j),\\
\gamma_{ij} &= \sigma(g(\cdot)),\\
c_i &= \frac{1}{C}\sum_j m_{ij},\\
z_i &= f_{\rm local}(o_i,r_i) + W_c c_i,
\end{aligned}
\]

where `a_ij` is the existing legal adjacency mask and `C` is fixed when the
architecture/configuration is frozen, not the instantaneous degree.  For the
current four-node graph, a possible future fixed choice would be the frozen
maximum graph-slot count `C = 4`; a future variable-size setting would have to
freeze `C = N_max` before training.  This review does **not** authorize either
choice or an implementation.

## 2. Q1 — Does the current SG have a deletion-induced nonlocal change?

**Answer: yes, within the receiver's incoming neighbourhood.**

The active matched-SG encoder is two
`GraphAttentionLayer`s in
[`algorithms/ri_gmappo/simple_ri_gmappo.py`](../algorithms/ri_gmappo/simple_ri_gmappo.py).
Each layer constructs a receiver-by-sender score, masks unavailable edges, and
applies `softmax(scores, dim=-1)` before `weights @ h`.  The graph convention
in the frozen 3D adapter is `A[receiver, sender] = 1`.

For a fixed receiver `i`, delete only incoming edge `(i,k)`.  Holding all
remaining score values fixed, ordinary softmax gives, for every surviving
sender `j != k`,

\[
\alpha'_{ij}=\frac{\alpha_{ij}}{1-\alpha_{ik}}.
\]

Thus every surviving attention weight changes whenever the deleted edge had
non-zero weight.  This is an algebraic property of neighbour-normalized
attention, not a learned failure mode.

A zero-training deterministic structural check was also run directly against
the current class (PyTorch seed `20260819`; batch size 1; four nodes;
`in_dim=5`, `out_dim=4`, `edge_dim=3`; initially dense adjacency; delete only
`A[0,2]`).  The first-layer receiver-0 weights changed as follows:

| Receiver 0, sender | Before deletion | After deleting sender 2 | Change |
|---|---:|---:|---:|
| 0 (survives) | 0.249118 | 0.340458 | +0.091340 |
| 1 (survives) | 0.238321 | 0.325703 | +0.087382 |
| 2 (deleted) | 0.268286 | 0.000000 | -0.268286 |
| 3 (survives) | 0.244274 | 0.333839 | +0.089564 |

The receiver-0 representation changed by L2 `0.130688`; an untouched
receiver's first-layer representation was unchanged in that one-layer test.
With the production two-layer encoder, a local first-layer change can then
propagate through later legal message passing.  This evidence establishes the
limited Q1 claim; it does **not** establish undesirable global policy change.

The baseline mechanism follows the original graph-attention construction,
which normalizes attention over a node's neighbourhood
([Veličković *et al.*, 2018](https://arxiv.org/abs/1710.10903)).

## 3. Q2 — Would the EDR form have the requested stronger locality property?

**Answer: yes mathematically, provided every surviving edge's inputs are
unchanged and the denominator is fixed.**

Let the only graph edit be `a_ik: 1 -> 0`.  For every surviving `j != k`, all
arguments of `m_ij` are identical before the downstream update, so

\[
m'_{ij}=m_{ij},\qquad
c'_i-c_i=-\frac{m_{ik}}{C}.
\]

The deleted message is removed, and no surviving edge contribution changes
through denominator renormalization.  This is strictly stronger than the
current softmax-local behaviour above.

The property has important limits:

- It is a **pre-nonlinearity, one-hop contribution** property only.
- It does not make `z_i`, later-layer states, attention, policy logits, or
  actions invariant: removal of `m_ik` can and should change them.
- It does not cover a physical event that simultaneously changes several legal
  edges, edge features, caches, or node states.  A future technical audit would
  need separate synthetic single-edge deletion and environment-snapshot tests.
- A fixed `C` intentionally reduces total residual magnitude after a deletion.
  That supports locality, but it may also underweight a still-valid direct path;
  it is a hypothesis, not a benefit already demonstrated.

## 4. Q3–Q5 — Task relevance, legality, and legal replanning

### Q3. Is the property relevant to relay failure?

**Yes, mechanistically.**  Relay failure removes legal communication edges and
may remove task-support edges because task support in this environment gates
delivered communication rather than creating an independent channel.  Under
the current encoder, the disappearance of a relay edge mechanically rescales a
surviving direct Scout-to-Attacker or other legal edge even if that survivor's
own descriptor did not change.  EDR targets exactly that normalization effect.

The relevance is bounded: a relay event is often a multi-edge/topology-state
change, so deletion locality alone does not establish mission robustness.

### Q4. Can EDR remain inside the frozen actor information boundary?

**Yes, if it reuses only current actor inputs.**  The narrowest lawful split is:

| Component | Permitted future inputs | Explicitly forbidden |
|---|---|---|
| `f_local(o_i,r_i)` | the existing actor-local `obs[i]` and its own role identity; these already contain self state, legally available target estimate/cache, local connectivity and age/confidence | `share_obs`, other agents' observations, global target truth, simulator failure truth, full topology/path summaries, future edges |
| `m_ij, gamma_ij` | the existing SG `node_feat`, `edge_feat`, `role`, and legal `adj` tensors, with their current frozen semantics | new shortest-path features, route labels, global connectivity, failure labels, privileged direct/relay labels, or a new hidden information channel |

The current actor already keeps `obs_encoder(obs)` as a local policy input and
uses `node_feat`, `edge_feat`, `role`, and `adj` for the legal graph branch.
An EDR design must not widen either interface.  Role-conditioned transforms are
not necessary for the locality proof because role information is already in the
current node/role input path; adding a new role-pair gate would increase both
capacity and overlap with the earlier rejected architecture family.

### Q5. Would EDR forbid valid path re-planning?

**No.**  It imposes no representation, action, or communication-invariance
loss.  A surviving direct edge can have a distinct `gamma_ij` and payload based
on its own current legal edge state; downstream nonlinear layers and the local
actor branch remain free to respond to the post-failure graph.  EDR would only
prevent a survivor from changing *solely because another incoming edge was
removed from a softmax denominator*.

## 5. Q6–Q7 — Prior-art positioning and novelty assessment

### What is already established

The candidate's constituent operations are established rather than novel:

| Candidate element | Primary prior work and consequence |
|---|---|
| Per-edge message followed by permutation-invariant sum aggregation | The general Message Passing Neural Network formalism already uses learned messages and a node update from aggregated neighbour messages ([Gilmer *et al.*, 2017](https://proceedings.mlr.press/v70/gilmer17a/gilmer17a.pdf)). |
| Fixed/global-degree rather than instantaneous-degree normalization | Structural Message Passing explicitly uses a global average-degree normalization in a message-passing construction ([Vignac, Loukas & Frossard, 2020](https://proceedings.neurips.cc/paper_files/paper/2020/file/a32d7eeaae19821fd9ce317f3ce952a7-Paper.pdf)). |
| Sigmoid edge gates plus residual graph updates | Residual Gated Graph ConvNets already combine edge gates and residuality ([Bresson & Laurent, 2017](https://arxiv.org/abs/1711.07553)). |
| Learned communication gating / selective message integration in MARL | IC3Net learns continuous communication gates ([Jain, Sukhbaatar & Singh, 2019](https://openreview.net/pdf?id=rye7knCqK7)); ATOC learns when and how to integrate communication ([Jiang & Lu, 2018](https://proceedings.neurips.cc/paper/2018/file/6a8018b3a00b69c008601b8becae392b-Paper.pdf)). |
| Training/evaluating resistance to structural edge perturbation | Edge deletion/dropout and structural robustness are established GNN research objects, e.g. DropEdge ([Rong *et al.*, 2020](https://arxiv.org/abs/1907.10903)), certified structural robustness ([Wang *et al.*, 2021](https://arxiv.org/abs/2008.10715)), and edge-dropping robustness work such as ADEdgeDrop ([Chen *et al.*, 2024](https://arxiv.org/abs/2403.09171)). |

These references do not refute the physical importance of relay failure.  They
do show that the proposed equations are a direct, unsurprising composition of
known message passing, gating, fixed normalization, and local/residual paths.
The named *edge-deletion locality property* is a clear implementation
specification, but it is an algebraic consequence of this familiar sum-gated
aggregation rather than a new learning principle.

### Q6. Is EDR meaningfully distinguishable from prior work?

**No, not at the level authorized here.**  The only potentially distinctive
piece is applying the locality specification to a frozen relay-failure MARL
benchmark.  That is a useful ablation/engineering rationale, but not a
sufficient architecture-level method contribution: a reviewer can reasonably
describe EDR as a gated MPNN or residual gated graph layer with a fixed
normalizer, evaluated under edge failures.

### Q7. Is that novelty enough to justify another development cycle?

**No.**  A publication-level claim would need a substantively new robust graph
communication principle, an analysis that exceeds the one-line deletion
identity, or an independently compelling empirical result.  The first would
require changing the authorized candidate; the second alone remains too close
to known gated message passing; the third cannot be assumed before spending a
new multi-seed training cycle.  Given the closed DRTP/TCR histories and the
current Route-A fallback, the expected evidential gain does not justify even a
new 0.3M screening round for this mechanism as specified.

## 6. Q8 — Capacity, computation, and a hypothetical fair screen

**Technically affordable, but not scientifically warranted.**  The current
matched SG has `116,728` parameters and uses two edge-feature GAT layers at
hidden width 115 and edge width 17.  One existing graph layer contains 15,640
parameters (projection 13,225; attention 230; edge-score MLP 2,185).

A minimal factorized EDR message of the form `P h_j + E e_ij`, reusing the
existing edge-gate MLP and adding no learned `W_c`, would contain approximately
17,480 parameters per graph layer: an increase of 1,840 per layer, or 3,680
total.  That would raise the actor from 116,728 to approximately 120,408
parameters (+3.15%).  A learned 115-by-115 `W_c` would add 13,340 parameters
per use (+11.4% once; +22.8% twice), before any role-pair transform.

Therefore a future fair comparator would need a fresh parameter audit and
capacity match; it cannot inherit the old matched-SG claim.  A factorized edge
message is likely affordable for the present four-node graph, although it has
more per-edge work than projecting a node once and then applying scalar
attention.  Technical affordability is not a reason to train when the method
identity is insufficiently distinct.

## 7. Required answers and decision ledger

| Question | Finding | Status |
|---|---|---|
| Q1: Current SG nonlocal under deletion? | Yes: softmax rescales surviving incoming contributions; both algebra and deterministic structural check confirm it. | PASS |
| Q2: EDR supplies stronger deletion locality? | Yes, for pre-nonlinearity one-hop contributions under a single-edge edit and fixed `C`. | PASS |
| Q3: Relevant to relay failure? | Yes, it targets a real normalization artefact during legal edge/path changes, but not all event effects. | PASS |
| Q4: Actor-boundary legal? | Yes, only if it reuses the exact current local/graph input interfaces. | PASS |
| Q5: Preserves legal re-planning? | Yes; no invariance constraint prevents post-failure adaptation. | PASS |
| Q6: Meaningfully different from prior work? | No: core mechanism overlaps gated MPNNs, residual gated graph layers, message gating, and structural-edge robustness literature. | **FAIL** |
| Q7: Enough novelty for another development cycle? | No: locality is a specification/ablation rationale, not a defensible new method principle. | **FAIL** |
| Q8: Implementable and affordable? | Probably, subject to new parameter matching; this cannot overcome Q6–Q7. | PASS |

### Final outcome: C — NO_GO

EDR exposes a genuine and well-defined sensitivity in the current GAT, but the
authorized formulation is not sufficiently distinguishable from established
gated message-passing architectures to justify another algorithm-development
cycle.  No EDR implementation, tape, smoke run, 1M screen, held-out run, or
canonical experiment is authorized by this review.

## 8. Consequence and stop rule

Keep the R1 Route-A system-robustness paper as the active publication route.
The current SG normalization finding may be reported only as an architectural
limitation/ablation rationale if later relevant; it must not be presented as an
unvalidated EDR improvement.  Reopening Route B again would require a new
author-approved proposal whose method-level distinction is established before
implementation, rather than another variation of edge gating, aggregation
normalization, residual fallback, or optimizer control.
