# PR-DRTP B4 zero-training feasibility contract

**Status:** `FROZEN_BEFORE_NEW_TAPE_EVALUATION`
**Scope:** Mainline B only. Mainline A evidence, manuscript and claims are immutable.

## Scientific question

The sampler-level stabilization candidates TR, uniform anchoring, KLR and
PP-DRTP did not reproducibly remove training-seed downside. B4 therefore asks a
different, falsifiable engineering question:

> Can a fixed training-support-only risk score select one deployable Original
> DRTP policy from a three-seed population while preserving average return and
> reducing catastrophic downside on a disjoint fresh outcome tape?

B4 does not claim to stabilize a single stochastic training trajectory. It
tests a population-level reliability protocol and performs no training.

## Retrospective boundary

The source checkpoints and some earlier outcome evaluations were inspected
before this contract was written. B4 is therefore exploratory feasibility, not
prospective confirmation. The two B4 episode-ID namespaces are new, disjoint
and frozen before execution, but a favorable B4 result can authorize only a
new prospective contract using new populations.

Five chronologically eligible 0.5M cohorts contribute exactly their first
three numerically sorted paired UTR/Original-DRTP seeds. This mechanical rule
retains seeds 2901--2903, 3101--3103, 3201--3203, 3401--3403 and 3501--3503.
Seeds 3504 and 3505 are excluded solely to keep three seeds per cohort; their
known outcomes did not determine the exclusion.

## Frozen populations and independent unit

The independent unit is a complete three-member population (`n=5`
populations). Models, evaluation episodes and condition cells inside a
population are repeated or technical observations, not independent `n`.

| Population | Members | Fixed single-start baseline |
| --- | --- | --- |
| P1 | 2901, 3403, 3502 | 2901 |
| P2 | 2902, 3101, 3503 | 3101 |
| P3 | 2903, 3102, 3201 | 3201 |
| P4 | 3103, 3202, 3401 | 3401 |
| P5 | 3203, 3402, 3501 | 3501 |

Each population contains three different historical cohorts. Baseline seeds
rotate across the five cohorts and were fixed before the new tapes were run.

## Frozen selector

Only Original-DRTP checkpoints are evaluated on the selector tape. It contains
50 paired episode IDs under seven conditions representing N/F0/TE/TL/DS/DL/CP
training support. The selector never reads the outcome tape.

Candidates must have zero mean constraint violation in every selector
condition. Among eligible candidates, select lexicographically by:

1. highest minimum of the seven condition-level mean mission scores;
2. highest arithmetic mean of those seven means;
3. lowest numeric training seed.

No threshold, weight, fitted model, sweep or outcome-contingent fallback is
allowed.

## Fresh exploratory outcome evaluation

All 15 paired UTR/Original-DRTP checkpoints are evaluated on disjoint episode
IDs 590000--590099 under nominal, F0, early-onset, long-duration and compound
conditions. Final 0.5M checkpoints are used uniformly; no checkpoint promotion
or best-milestone selection is permitted.

Define `G_s = J_pert_mean(DRTP_s) - J_pert_mean(UTR_s)`. The selected
population output inherits the paired UTR of the selected seed. Evaluation
episodes are paired technical repetitions.

## Feasibility gate

`PR_FEASIBILITY_GO` requires all frozen conditions:

1. Selected means for nominal, F0, perturbation mean and perturbation worst are
   each no more than `epsilon_J=7.874919837916801` below fixed-baseline means.
2. Worst selected gain exceeds worst baseline gain by more than `epsilon_J`;
   selected catastrophic count is zero and no greater than baseline.
3. Range and sample SD of the five selected gains both decrease.
4. At least four of five selected gains are nonnegative.
5. At least two fixed-baseline gains exceed `epsilon_J`, and every corresponding
   selected output retains that baseline robust mean within `epsilon_J`.
6. Pooled selected collision/timeout deltas versus paired UTR are at most 0.05;
   every selected population-condition delta is at most 0.10; constraint
   violations remain zero.
7. All checkpoint hashes, tape hashes, population membership, selector
   isolation and evaluation-cell counts pass integrity checks.

Any scientific failure is `PR_FEASIBILITY_NO_GO`. Any missing/corrupt artifact,
selector leakage or incomplete cell is `PR_FEASIBILITY_TECHNICAL_INVALID`.

## Resource accounting and stopping rule

The selector represents three Original-DRTP training trajectories per deployed
population (3x training cost before selection), plus 1,050 selector episodes
per population. B4 reports these costs explicitly. It must not be described as
equal-compute to a single DRTP run.

B4 performs evaluation only. No training, continuation, parameter tuning,
population regrouping, seed replacement, selector-v2, ensemble or distillation
is authorized. A GO supports only prospective design; a NO-GO closes this
fixed maximin selector.
