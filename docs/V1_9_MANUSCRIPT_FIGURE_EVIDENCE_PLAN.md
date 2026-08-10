# v1.9 Manuscript Figure and Evidence Plan

**Status:** planning record only.  This document does not authorize a new
experiment, access to the untouched F2 population, or use of F1 validation
numbers as paper evidence.

## Governing principle

The eventual number of manuscript figures is determined by the number of
scientific claims that have independent, confirmatory evidence—not by the
number of implemented modules.  A panel is retained only when it contributes a
distinct link in the claim-to-evidence chain.  The final main-text figure count
may therefore be smaller than this plan if a planned claim lacks support.

The primary architecture comparator is PCRF-R2 versus source-aware
single-R2.  Matched-information non-graph is a secondary comparator.  Legacy
three-relation PCRF-R1, Task-Support, union residual, and Role-Pair must not be
presented as v1.9 headline innovations.

## Candidate main-text figures

| Figure | Claim addressed | Required evidence | Status / restriction |
| --- | --- | --- | --- |
| Fig. 1 — Task and method contract | The task has two legally distinct actor information sources: direct local perception (P) and actually delivered, cache-valid communication (C); PCRF-R2 fuses them with a baseline gate plus conflict deviation. | 3DOF task schematic; recipient-specific P/C contract; age-expiry exclusion; architecture/comparator matching. | Can be drafted before F2.  It must not imply a performance advantage. |
| Fig. 2 — Primary architecture comparison | PCRF-R2 has (or does not have) an earlier stable legal task-chain establishment than source-aware single-R2 under the frozen protocol. | Untouched F2, all eight training seeds, paired evaluation IDs, RMTE80 primary effect with hierarchical bootstrap; establishment and terminal-failure incidences; RMTE220 secondary. | Cannot be plotted until F2 is separately authorized and complete. |
| Fig. 3 — Secondary representation comparison | PCRF-R2 has (or does not have) value beyond a matched-information non-graph representation. | The same F2 population, metrics, pairing and statistical hierarchy as Fig. 2. | Secondary only; MAPPO/HAPPO are not pure architecture comparators. |
| Fig. 4 — Post-onset mechanism diagnostic | Any observed end-to-end advantage is, or is not, retained when methods start from identical failure-onset simulator states. | Frozen common-onset-state diagnostic, matched onset states/history/cache under the recipient-specific contract, pre-specified paired analysis. | Secondary diagnostic; it cannot replace Fig. 2 or retroactively alter F2. |
| Fig. 5 — Endpoint construct validity | Stable task-chain establishment is accompanied by, or distinguishable from, earlier physical-engagement readiness. | F2 outcome decomposition and frozen RMPE80/RMPE220; empirical establishment, terminal-failure and active-unestablished proportions. | RMPE means physical-engagement readiness—not interception, capture, or mission completion. |
| Fig. 6 — Graded OOD generalization | The method has a defined robustness boundary across all pre-frozen geometry, communication, maneuver and joint severities. | Entire pre-registered graded OOD matrix, reported without selecting favorable severities. | Requires separate OOD authorization after F2. |
| Fig. 7 — Conflict-deviation necessity | The PCRF-R2 conflict deviation has, or does not have, a measurable optimization/decision contribution. | Pre-registered Full versus Delta=0 ablation with shared legal information, budget and analysis. | Requires separate ablation authorization after F2. |

## Recommended visual form

- **Fig. 1:** schematic-led composite.  Show raw source provenance before the
  encoder, the age-validity cutoff before the C branch, and matched comparator
  inputs/parameter counts.  Do not draw unavailable global truth as actor input.
- **Fig. 2:** hero quantitative figure.  Use paired seed-level effects and
  hierarchical-bootstrap intervals, accompanied by the complete outcome
  decomposition rather than a bar chart alone.  If an event-time curve is used,
  show empirical establishment incidence / CIF semantics, never a KM curve
  that censors terminal failures.
- **Figs. 3–5:** compact quantitative panels using the same method colors,
  training-seed nesting and effect-direction convention as Fig. 2.
- **Figs. 6–7:** only include if the whole pre-registered matrix is available;
  absence of a favorable result is not a reason to omit a frozen condition.

## Candidate main-text tables

| Table | Content | Evidence gate |
| --- | --- | --- |
| Table 1 | Method/input fairness: P/C sources, actor information contract, hidden dimension, parameter count, training budget and selector. | Static audits and frozen F1 protocol. |
| Table 2 | F2 primary and secondary endpoints: RMTE80, establishment incidence, terminal-failure incidence, RMTE220, RMPE; paired effect and interval. | F2 only. |
| Table 3 | Common-onset mechanism diagnostic and prespecified conflict-condition results. | Separate diagnostic only. |
| Table 4 | Full graded OOD and/or Delta=0 ablation results. | Only after those protocols are authorized and completed. |

## Supplementary evidence

Supplementary material should contain the actor-information provenance matrix,
age-valid cache counterfactuals, terminal-outcome/RMTE estimand definition,
all seed/checkpoint/provenance records, full F2 episode-level source data,
natural P/C-conflict prevalence, complete OOD grids, and full ablation outputs.
F1 validation trajectories may be included only as training/selection
diagnostics; they are not confirmatory performance evidence.

## Claim-to-figure decision rules

1. If F2 does not support PCRF-R2 versus source-aware single-R2, do not claim
   multi-source graph-representation superiority, irrespective of comparisons
   with standard MAPPO/HAPPO.
2. If end-to-end F2 supports PCRF-R2 but the common-onset diagnostic does not,
   retain only the end-to-end task-performance wording; do not claim a pure
   post-onset conflict-handling mechanism.
3. If RMPE is not aligned with task-chain establishment, report that boundary
   and do not upgrade the claim to capture/interception/mission success.
4. If a planned OOD or ablation study is not authorized or not supported, omit
   its main-text claim rather than adding an exploratory substitute.

## Current writing boundary

During F1, only the Fig. 1 schematic and result-independent templates may be
prepared.  No F1 validation number, training curve, selected checkpoint or
partial seed result may populate a manuscript result panel.  Final main-text
figure selection occurs only after F2 and any separately authorized diagnostic,
OOD, or ablation gates.
