# KLR long-horizon audit

**Verdict:** `LONG_HORIZON_RETEST_WEAKLY_JUSTIFIED`.

Historical budgets: [0.5]M env steps.
Saved task-policy/runtime milestones: [0.25, 0.5]M.
Exact runtime recovery recorded: `True`.

## Existing matched performance evidence

Development: mean +23.252; median +31.447; wins 2/3 versus Original DRTP.
Replication A: 0.5M, mean -0.871, median -5.200, wins 2/5, new catastrophes 1.
Replication B: 0.5M, mean +15.989, median +4.018, wins 3/5, new catastrophes 1.

## Curve maturity

Training-only reward rose modestly during the final quarter, but there are no intermediate matched task evaluations showing candidate catch-up or rank reversal.

## Audit conclusion

It is the only candidate with one positive final replication cohort and no 1M test, but the two 0.5M cohorts disagree and both contain a new catastrophic seed.
