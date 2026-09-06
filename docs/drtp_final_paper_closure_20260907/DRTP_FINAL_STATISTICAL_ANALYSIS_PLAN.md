# DRTP final statistical analysis plan

## Analysis unit and endpoint

The primary independent unit is the training seed. Each arm uses the same five seeds within cohort A or B. The primary model is the final checkpoint at 39,063 updates / 10,000,128 environment steps. No intermediate checkpoint, early stopping event, or best-return checkpoint is eligible for final analysis.

## Primary comparison

For each cohort separately, compare Original DRTP with UTR using perturbed return. Report every seed, cohort mean, median, minimum, maximum, sample SD, MAD, and the paired differences. The paper's primary statement is based on direction and magnitude across both cohorts, not on a requirement that every seed beat UTR.

## Safety and reliability reporting

For the same fixed endpoint, report collision and timeout separately; do not use one to compensate for deterioration in the other. Interpret lower tail, spread, catastrophic outcomes and safety jointly with mean and median. A wider raw range caused by improved upper-tail returns is described as a distributional observation, not automatically as degradation.

## Cohort rule

Do not merge A and B to manufacture a confirmatory result. Main text displays each cohort separately. A pooled ten-seed number, if shown, is explicitly descriptive and cannot replace cohort-specific evidence.

## OOD, PLR and six-UAV blocks

1. Held-out/OOD: retain all frozen conditions; report condition-level and cohort-level paired deltas.
2. PLR-style comparator: report its matched A/B cohorts separately, with the same endpoint budget and tape as UTR/DRTP.
3. Six-UAV: report the 2S/2R/2T matched endpoint only after all ten runs and fixed evaluation files exist.

## Forbidden post hoc actions

- Excluding a seed, condition, safety metric or cohort because it is unfavorable.
- Selecting a checkpoint by outcome.
- Replacing a missing endpoint with an intermediate result.
- Changing DRTP, UTR, PLR or the six-UAV environment after observing outcomes.

