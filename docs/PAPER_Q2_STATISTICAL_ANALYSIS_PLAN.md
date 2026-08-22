# PAPER-Q2 Statistical Analysis Plan

**Status:** frozen planning artifact; zero training. **Generated:** 2026-08-22

## Statistical unit and contract separation

The independent unit is the **training seed**, not an episode and not a pooled row. Paired differences are computed only within the same seed and the same frozen contract. T1 UTR (seeds 2201–2205), DRTP development (1901–1902, 3M), and DRTP held-out (2001–2003, 10M) are reported as separate strata. A cross-stratum summary, if shown, is descriptive only and never an inferential claim.

## Metric hierarchy

Primary robustness outcomes: `J_F0`, `J_OOD_mean`, `J_OOD_worst`, and timeout rate. Secondary outcomes: `J_nominal`, collision rate, constraint violation, exposure/risk-set validity, path switching, task-support utilization, and maneuver/control burden.

For each method and contract report raw seed values, paired DRTP−UTR deltas, win count, mean, median, IQR or MAD, worst paired degradation, and dispersion. For n=5, use seed-level paired bootstrap only as a descriptive interval and label it as such; do not imply asymptotic population inference. For n=2 or n=3 strata, show all points and avoid formal significance claims.

## Required plots/tables

Show all seed points, not only pooled means. Use paired slope/dot plots for deltas, condition-wise distributions for OOD, and separate safety panels. Any interval must state whether it is seed bootstrap, episode bootstrap, or a descriptive spread; episode bootstrap cannot replace seed replication.

## Missing-data and invalidity policy

No post-hoc seed exclusion, checkpoint promotion, or censoring of pre-trigger terminations. Technical invalidity is reserved for documented crash, corruption, or protocol failure. Policy failures remain performance/safety outcomes. Historical `DRTP_Q2_LIMITATION_ONLY` and held-out FAIL are immutable.

## Interpretation boundary

Positive mean and median do not establish seed stability. A result can support “higher average/median robustness with non-negligible initialization sensitivity” only if the worst seed, held-out reversal, safety deltas, and contract separation are all visible.
