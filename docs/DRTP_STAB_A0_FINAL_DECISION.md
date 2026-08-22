# DRTP-STAB-A0 Final Decision

## Historical status retained

- `DRTP_Q2_LIMITATION_ONLY`.
- Development seed1902 retention failure.
- Held-out seed2002 F0/OOD/timeout reversal.
- Held-out forensic classification: `C — NO_ACTIONABLE_CAUSE / INTRINSIC_SEED_SENSITIVITY`.
- `CONDITIONAL_PAPER_VIABLE_WITH_EXPLICIT_SEED_SENSITIVITY` remains a paper
  positioning statement only.

## A0 synthesis

The frozen sampler can in principle log the quantities needed for a rigorous
weight-dynamics analysis. The relevant historical time series are not retained
in the current evidence assets, and the historical summary evidence contains
three direct counterexamples to the proposed simple explanation: low F0 weight
and CP/DL concentration also occurred in strong DRTP seeds.

Seed2002 has an early internal learning deficit by about 1M and a 0.5M weight
snapshot, but the records do not establish a causal temporal order. PPO
diagnostics do not identify generic optimization instability. Offline replay
cannot be honestly executed without the archived difficulty/EMA trajectories.

## Final decision

\[
\boxed{\textbf{C — NO\_ACTIONABLE\_WEIGHT\_STABILITY\_CAUSE}}
\]

No `PRIMARY_STABILIZATION_PRINCIPLE` is defined. A0 does not authorize
Slow-DRTP, DRTP-v2, smoothing, trust-region weighting, implementation changes,
training, rollout, tape generation, new seeds, held-out use, or canonical use.

The only scientifically supported DRTP role remains transparent reporting as a
high-upside, seed-sensitive historical comparator/limitation within the
UTR-centered robustness paper.

## Backup recovery addendum — final evidence basis

Complete 10M development and held-out sampler/PPO histories were subsequently
recovered from the backup archives. They do not change the decision. Rather
than a data-availability limitation, the controlling reason for outcome C is
now empirical: seed1902 and seed2002 do not share abnormal pre-divergence
weight movement, while strong seeds exhibit equal or greater movement/ranking
churn. Offline smoothing reduces movement in every seed and remains nonuniform,
but cannot identify a failure-specific stabilization target.
