# v1.9 PCRF-R2 result-independent manuscript skeleton

**Writing status:** pre-result scaffold only. It deliberately contains no F1
validation number, selected-checkpoint outcome, F2 partial result, OOD result,
or ablation result. Populate result-bearing statements only after the relevant
frozen artifact gate has passed and the author has reviewed the complete data.

## Working paper argument

> In a 3DOF heterogeneous UAV coordination task with a pre-specified relay
> failure, we test whether preserving recipient-legal direct perception and
> delivered/cache-valid communication as distinct actor evidence sources with
> conflict-conditioned fusion improves time to stable legal task-chain
> establishment over a source-aware unified graph, subject to an untouched
> confirmatory evaluation and bounded task-level interpretation.

This is an **algorithmic research** paper. The headline claim is conditional
on F2 and is limited to the primary matched architecture comparison. It is not
a recovery claim, a capture/interception-completion claim, or a claim that a
legacy EA-RG implementation remains valid evidence.

## Terminology ledger

| Canonical term | First use / definition | Do not substitute with |
|---|---|---|
| PCRF-R2 | perception--communication residual fusion, R2 two-source policy | EA-RG, PCRF-R1, multi-relational policy |
| P | receiver's direct local target-perception evidence | global perception, teammate truth |
| C | actually delivered and cache-valid communication evidence | communication reachability alone, stale/expired packet |
| recipient-specific actor contract | actor may use only evidence legally available to that receiver at that step | centralized observation |
| source-aware single-R2 | unified graph receiving the same tagged legal P/C raw fields as PCRF-R2 | generic GAT baseline |
| matched-information non-graph-R2 | no-message-passing comparator receiving the same legal P/C fields | standard MAPPO |
| RMTE\(_\tau\) | task-defined restricted mean time to stable establishment after failure onset | conventional KM/RMST without qualification |
| terminal-failure incidence | collision/constraint terminal outcome before establishment by the horizon | censoring rate |
| RMPE\(_\tau\) | restricted mean time to physical-engagement readiness | capture time, interception completion, mission success |

## Section architecture

### 1. Introduction

1. **Context.** State the coordination problem under intermittent sensing,
   packet delivery delay/loss, cache expiry, and relay failure.
2. **Gap.** Explain that a graph edge/mask alone does not establish legal actor
   information provenance, and that merging direct perception with delivered
   communication destroys source identity.
3. **Question.** Pose the falsifiable PCRF-R2 versus source-aware single-R2
   contrast under equal raw actor information.
4. **Contribution and boundary.** State the source contract, the R2
   source-preserving fusion, and the confirmatory protocol. Do not claim an
   advantage before the F2 review.

### 2. Task, information contract, and estimands

1. Define the 3DOF heterogeneous agents, target, relay-failure onset, and
   legal stable task-chain establishment event.
2. Define P and C and the cache-expiry exclusion rule. Expired, pending,
   dropped, invalid and undelivered packets create zero C node, edge and
   adjacency entries.
3. Separate decentralized actor information from centralized critic-only
   `share_obs` information.
4. Define RMTE80 as the primary endpoint and RMTE220 as secondary. Terminal
   failures before establishment contribute the restriction horizon rather
   than being ordinary right-censoring.
5. Define the outcome decomposition: establishment, terminal failure, and
   active-but-unestablished. Define RMPE only as physical-engagement readiness.

### 3. PCRF-R2 method

1. **Source factorization.** Define \(G_i^P\), \(G_i^C\), masks \(m_i^P,m_i^C\),
   and source-free \(z_i^{ctx}\).
2. **Separate encoders.** Present \(h_i^P=m_i^P F_P(G_i^P)\) and
   \(h_i^C=m_i^C F_C(G_i^C)\), with no union residual or third relation.
3. **Neutral conflict deviation.** Define the legal descriptor
   \(c_i=[a_i^P-a_i^C,d_{PC},age_C,1-confidence_C]\), baseline logits
   \(\beta\), and \(\Delta(c_i)=g(c_i)-g(0)\). State the exact neutral
   condition \(\Delta(0)=0\).
4. **Availability-masked fusion.** Give the two-source masked-softmax equation;
   state single-source unit weighting and `mP=mC=0` fallback to \(z_i^{ctx}\).
5. **CTDE and comparators.** State actor/critic separation and the matching of
   raw P/C inputs, parameter capacity and training budget across PCRF-R2,
   source-aware single-R2 and matched-information non-graph-R2.

### 4. Experimental protocol

1. State the F1 training population: three methods, eight formal training
   seeds each, 300 updates, eight environments, rollout length 128 and four
   PPO epochs. Explain that F1 validation only selects checkpoints.
2. State the frozen F2 matrix: 24 selected checkpoints, 300 shared paired
   episode IDs per checkpoint, deterministic actions, and no adaptive changes.
3. State the primary comparison: PCRF-R2 versus source-aware single-R2 using
   \(\Delta RMTE80=RMTE80^{PCRF}-RMTE80^{single}\), with pre-frozen practical
   threshold \(-4\) steps.
4. State hierarchical paired bootstrap: outer training-seed resampling then
   matched episode resampling, 10,000 resamples.
5. List result-independent controls: actor-boundary tests, source parity,
   age-validity counterfactuals, terminal-estimand regression and immutable
   checkpoint/event-record provenance.

### 5. Results and interpretation placeholders

| Planned subsection | Required evidence before prose may be completed | Claim boundary |
|---|---|---|
| Primary architecture comparison | Complete F2 artifact gate and frozen bootstrap output | Only PCRF-R2 versus source-aware single-R2 |
| Outcome decomposition and RMPE | Complete F2, all terminal outcomes and physical-readiness fields | RMPE is not capture or mission completion |
| Secondary non-graph comparison | Complete F2 secondary analysis | Does not replace the primary graph comparator |
| Common-onset diagnostic | Separately authorized and completed diagnostic | Cannot replace end-to-end F2 |
| Conflict-deviation ablation | Separately authorized Full versus \(\Delta=0\) evidence | Required for a mechanism-necessity claim |
| Graded OOD | Entire pre-frozen severity matrix | Omit if not completed; never choose favorable cells |

## Figure and table map

| Item | Role | Gate |
|---|---|---|
| Fig. 1 | Task and source-contract schematic | May be finalized now; no performance wording |
| Fig. 2 | Primary F2 architecture comparison and full outcome decomposition | F2 complete and author-reviewed |
| Fig. 3 | Secondary matched-information non-graph comparison | F2 complete |
| Fig. 4 | Common-onset mechanism diagnostic | Separate authorization/completion |
| Fig. 5 | RMTE--RMPE construct-validity relationship | F2 complete |
| Table 1 | Raw actor-information and capacity parity | Static audits/F1 freeze |
| Table 2 | F2 primary and secondary endpoints | F2 complete |

## Claim-evidence decision rules

1. Claim `source-preserving architecture superiority` only if the PCRF-R2
   versus source-aware single-R2 RMTE80 contrast has the pre-frozen favorable
   direction, reaches the practical threshold, has stable seed-level effects,
   has a supporting hierarchical interval, and does not exchange an RMTE gain
   for an important terminal-failure increase.
2. If the primary contrast fails, retain the implementation and protocol
   contribution but remove the superiority claim. Do not extend training,
   change seeds, endpoints, checkpoint selection or architecture after F2.
3. If end-to-end F2 supports PCRF-R2 but the common-onset diagnostic does not,
   claim only end-to-end task performance, not pure post-onset conflict
   handling.
4. If RMTE and RMPE are not aligned, state that task-chain establishment is
   not an independently validated interception/completion endpoint.

## Current writing boundary

Safe work before F2 completion: Fig. 1 visual/source-contract review, this
result-independent Methods/Protocol structure, terminology consistency,
reproducibility documentation, and a blank Results table layout.

Forbidden before the complete F2 artifact and analysis review: any manuscript
result sentence, advantage adjective, effect size, method ranking, F1
validation curve, checkpoint-selection outcome, or post-hoc experiment plan.
