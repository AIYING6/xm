# v1.9 G0-R2 Final Theory and Comparator Freeze

**Status: `G0_R2_THEORY_AND_COMPARATOR_FROZEN`.**

**Execution status: the separately authorized source-separated implementation
and D0-R2 audit now pass; D1-R2, D2, GPU run, formal training, held-out
evaluation, OOD, ablation, and manuscript revision remain unauthorized.**

This release follows the completed novelty kill-check, which passed only with
a narrowed claim.  It supersedes no v1.8 protocol and does not rehabilitate
the terminated three-relation PCRF-R1 line.

## 1. Frozen research question and prohibited substitutes

The question is exactly:

> Under recipient-specific, delivery-grounded actor information, does retaining
> the provenance of direct perception and actually delivered/cache-valid
> communication until fusion improve time to first stable legal task-chain
> establishment, relative to an equally informed, near-capacity-matched unified
> single-graph encoder when those sources are temporally or semantically
> inconsistent?

The following are not substitutes for this question and cannot be claimed as
R2 novelty: separate encoders in general, generic attention/gating, delayed
message handling, uncertainty-aware evidence fusion, graph MARL, UAV limited
communication, or receiver-specific messaging.  The nearest-work obligations
are frozen in [the novelty kill-check](V1_9_G0_NOVELTY_KILLCHECK.md), with
T2MAC, CDCMA, CoDe, Communication-Aware UAV MARL, and AsynCoMARL as first-tier
comparative literature.

## 2. Frozen two-source actor contract

For receiver \(i\), only these two target-evidence sources may enter the
candidate representation:

| Source | Permitted target evidence | Mandatory exclusion |
|---|---|---|
| `P` — direct perception | locally sensed target claim, availability mask, and direct-sensing quality | delivered packet content, cached teammate claim, packet age/confidence |
| `C` — communication | only actually delivered and cache-valid packet snapshot claim(s), sender/provenance, generation/delivery timing, age, and confidence | pending, dropped, expired, invalid, or undelivered packets; simulator truth |

The shared context contains only receiver self state, own role/task context,
local attack availability, and fixed vehicle capability.  It contains no
target estimate, target cache, packet-derived target age/confidence, teammate
payload, critic/shared state, or simulator-global quantity.  Thus it cannot
reconstruct one source through a common-observation path.

Every future comparator receives the same recipient-specific raw P/C/context
fields, masks, packet/cache semantics, geometry, and role/task context.  Any
missing or unavailable quantity is masked/zeroed before feature construction;
an attention adjacency of zero is not accepted as a leakage defense.

## 3. Frozen candidate mechanism and null behavior

PCRF-R2 alone may use separate factor encoders and the availability-masked
baseline-plus-deviation fusion below:

\[
h_i^P=m_i^P F_P(G_i^P),\qquad h_i^C=m_i^C F_C(G_i^C),
\]

\[
c_i=[a_i^P-a_i^C,\ d_{PC},\ \operatorname{age}_C,\ 1-\operatorname{confidence}_C],
\qquad \ell_i=\beta+\Delta(c_i)-\Delta(0).
\]

`d_PC` is a masked content discrepancy between legal direct target claims and
legal delivered target claims; it is not a graph-adjacency overlap statistic.
The exact neutral state has balanced availability, zero disagreement, fresh
communication, and confidence one, and must give \(\Delta(c_i)=0\) exactly.
With one legal source its weight is exactly one; with neither legal source the
fused evidence is zero and the policy uses only legal source-free context.

No third relation, Role-Pair headline mechanism, unrestricted union residual,
or extra adaptive module is part of R2.  A later result may not be used to add
one.

## 4. Comparator hierarchy and causal interpretation

| Tier | Comparison | What it may identify |
|---|---|---|
| Primary | PCRF-R2 vs wider single graph | value, if any, of retaining P/C provenance to fusion under equal legal raw information and near-matched capacity |
| Secondary | PCRF-R2 vs matched-information non-graph | whether graph aggregation adds value beyond source-preserving pooling |
| System reference only | PCRF-R2 vs standard MAPPO/HAPPO, if their no-graph invariance remains documented | system-level context; never pure architecture superiority |

The wider single graph must retain all P/C tags, masks, age/confidence,
geometry, and conflict-relevant fields.  It differs only by using one shared
encoder over `P union C`; it must not be made weaker by withholding metadata.
The non-graph model receives the same fields before a deterministic,
source-preserving pooling step.  A pre-encoder input-hash/provenance audit must
demonstrate parity for every method and seed before any future launch.

## 5. Preregistered falsification states and predictions

The mandatory diagnostic states are: agreement; fresh P/stale-or-low-confidence
C disagreement; P unavailable/C valid; C unavailable/P valid; and
relay-failure-induced P/C disagreement.  All methods see the same environment
and packet processes.  Every cell must be reported, including failures; these
states never replace nominal primary evaluation.

The mechanism hypotheses are limited to:

1. **H1 architecture:** PCRF-R2 can beat the wider single graph on the frozen
   primary endpoint only under the later-frozen practical and precision rules.
2. **H2 specificity:** any difference must be directionally more favorable in
   predeclared P/C-conflict exposure than in agreement states; no universal
   advantage is predicted.
3. **H3 necessity:** an otherwise matched `PCRF-Delta0` control is required
   before claiming that the conflict deviation, rather than factor width alone,
   is explanatory.

Failure of H1 ends the architecture-superiority headline.  Failure of H2 or
H3 ends the conflict-mechanism claim.  These outcomes are scientific results,
not reasons to alter R2 after looking at performance.

## 6. Still-unset formal constants and resulting stop rule

No numerical choice is invented here.  Before a D2/F1 release, the author must
freeze without inspecting R2 performance:

- practical margin \(\delta_{min}\);
- common seed rule (direct 8 or a direction-neutral 5-to-8 precision
  expansion) and its variance/CI-width thresholds;
- method-blind endpoint adequacy bounds;
- validation/checkpoint selector and all training-budget details;
- confirmatory episode bank and evaluation anchor; and
- formal `PCRF-Delta0` control budget.

The endpoint origin remains failure onset; the event is first `K=4`
consecutive-step legal task-chain establishment.  Collision and constraint
termination are absorbing no-establishment outcomes by \(\tau\), not ordinary
early right censoring.  The primary analysis resamples training seeds, then
matched evaluation episodes.

Until the listed constants are frozen, the only permissible next stage is a
separately authorized implementation/D0-R2 integrity stage; no performance
comparison or GPU experiment is permitted.

## 7. Release state

The novelty, theory/comparator, implementation, and D0-R2 integrity gates are
now closed; see [D0-R2 audit](V1_9_D0_R2_IMPLEMENTATION_AUDIT.md).  The next
possible decision is **whether to authorize D1-R2 engineering-only runs**.
D2 and every later stage remain blocked pending a separate D1 pass and author
authorization.
