# P40 G1--G3 zero-training audit

## Decision

**P40_STOP: the current local asset set cannot identify a topology-transfer
matrix, so no P40 training contract is authorized.**

This is an evidence stop, not a claim that cross-topology transfer is absent.
It prevents a long training run from being launched on an unmeasured mechanism.

## Evidence identity

This audit uses only the current DRTP final-evidence register and its registered
figure-source data. Historical `190x`, `200x`, `230x`, and `240x` experiments
are not used.

- Evidence register: `docs/drtp_submission_ready/DRTP_FINAL_EVIDENCE_REGISTER_20260908.md`.
- Final A/B endpoint rows:
  `docs/drtp_submission_ready/figure_source_data/Fig4_final_ab_paired_endpoint.csv`.
- Final A/B held-out structural rows:
  `docs/drtp_submission_ready/figure_source_data/Fig5_heldout_structural_endpoint.csv`.
- DRTP q milestones:
  `docs/drtp_submission_ready/figure_source_data/Fig3_q_evolution_milestones.csv`.

The referenced cloud archives named by the evidence register are not present in
the current local workspace. No unregistered result was substituted.

## G1: task-band check — PASS, descriptive only

The registered final A/B UTR rows show non-ceiling nominal and perturbed
performance, with nontrivial timeout rates and substantial condition/seed
variation. For example, cohort A includes perturbed UTR returns from about
79.75 to 240.99; cohort B includes approximately 164.98 to 222.78. The
structural held-out table also reports nonconstant return, success, and timeout
values across seeds and conditions.

Thus the final task is not supported by the available evidence as an all-success
or universal-timeout benchmark. This permits, but does not establish, a training
allocation question.

## G2: intervention heterogeneity — NOT IDENTIFIED

P40 requires values of

\[
T_{g \rightarrow h}=\Delta\,\text{validation performance on }h
\text{ after a matched policy update collected from }g.
\]

The registered final assets provide endpoint policy results and the realized
DRTP sampler trajectory. They do **not** include:

1. matched policy states before and after a source-group-specific update;
2. source-group-isolated update batches;
3. a disjoint training-side recipient probe tape; or
4. common-random-number estimates of the resulting recipient-condition change.

Consequently, q deviations from uniform can show only that DRTP changed the
training distribution. They cannot estimate a directed transfer effect or show
that a high-q group improved another topology condition.

## G3: allocation decision relevance — NOT IDENTIFIED

Because G2 is unavailable, no maximin transfer-coverage objective can be
computed. Any claimed P40 distribution would be determined by an unmeasured
matrix and would therefore collapse to a hand-designed prior, difficulty score,
or random reweighting. It would not be a new identifiable method.

## Required evidence before reconsideration

P40 can be reconsidered only after a new **micro-update audit** is designed and
frozen. It must:

- start from a registered checkpoint independent of final evaluation;
- use matched source-group batches and a fixed update count;
- evaluate all recipient groups on a disjoint, training-side common-random-number
  tape before and after each update;
- report uncertainty across independently initialized audit replicas;
- seal the final endpoint/OOD tape from both the matrix and sampler; and
- stop immediately if matrix rows are statistically and practically
  indistinguishable, or if the induced allocation equals UTR/DRTP/hardest-first.

This would be a new diagnostic experiment, not a reanalysis of current DRTP
results. Until it exists and passes, P40 has no basis for long training or for a
paper claim.
