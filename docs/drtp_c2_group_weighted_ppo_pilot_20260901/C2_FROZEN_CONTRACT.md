# C2 frozen contract: fresh-seed group-weighted actor PPO pilot

## Scope

C2 will test whether the C1 local update advantage accumulates into a
meaningful training outcome.  It is a development-only, two-cohort 0.5M pilot
and is not authorized by this document.

## Methods and exposure control

Each of the ten fresh seeds is assigned to Cohort A (4801--4805) or Cohort B
(4806--4810).  Each cohort separately trains:

1. `utr_sg`: fixed-stratified collection and ordinary PPO;
2. `drtp_sg`: Original DRTP, retained solely as the high-upside reference; and
3. `group_weighted_utr_sg`: exactly the same fixed-stratified collection as
   UTR, with a bounded actor-only group-weighted PPO update.

The candidate's initial update uses unit weights.  Every later update uses
only the preceding training rollout's group-level mean absolute TD residual.
Failure weights are bounded in [0.75, 1.25], normalized to mean one over the
current failure graphs, and never apply to nominal graphs.  The critic,
reward, PPO objective, network and environment remain unchanged.

## Frozen limits

- 1,953 updates / 499,968 training environment steps per trajectory;
- exactly 30 trajectories; no early stopping, seed replacement, rerun,
  checkpoint promotion, weight sweep or continuation;
- only the frozen development tape at the 500k checkpoint; no formal,
  independent or held-out tape; and
- Cohort A and B must each pass.  Pooling ten seeds cannot produce success.

## Decision

For each cohort, C2 requires positive mean robust gain versus UTR, at least
three non-negative paired gains, no added catastrophic seed versus Original
DRTP, no larger gain range or sample SD than Original DRTP, retention of mean
and upper-tail Original-DRTP performance within frozen `epsilon_J`, unchanged
safety limits, and telemetry proving fixed collection plus auto-lagged
training-only weights.

`C2_EARLY_GO` requires both cohorts to satisfy every item.  Any cohort failure
is `C2_NO_GO`.  Neither outcome starts a longer run automatically.
