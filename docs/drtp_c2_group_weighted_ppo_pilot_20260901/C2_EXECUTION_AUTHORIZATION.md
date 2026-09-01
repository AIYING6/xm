# C2 execution authorization

**Status:** `C2_EXECUTION_AUTHORIZED`.

The user authorized exactly the frozen C2 pilot after the P0 readiness gate:

- `utr_sg`, `drtp_sg`, and `group_weighted_utr_sg`;
- seeds 4801--4810, reported as Cohort A and Cohort B separately;
- 1,953 updates / 499,968 training environment steps per trajectory; and
- only the frozen 500k development evaluation and C2 gate.

The authorization excludes early stopping, seed replacement, reruns,
checkpoint promotion, weight tuning, automatic continuation, any C3 or longer
run, and any Mainline A change.
