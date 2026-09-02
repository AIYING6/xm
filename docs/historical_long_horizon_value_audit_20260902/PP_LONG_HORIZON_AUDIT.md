# PP-DRTP long-horizon audit

**Verdict:** `LONG_HORIZON_RETEST_NOT_JUSTIFIED`.

Historical budgets: [0.5]M env steps.
Saved task-policy/runtime milestones: [0.25, 0.5]M.
Exact runtime recovery recorded: `True`.

## Existing matched performance evidence

Development: mean +38.202; median +10.788; wins 3/3 versus Original DRTP.
Independent Replication: 0.5M, mean -8.106, median -23.862, wins 2/5, new catastrophes 2.

## Curve maturity

Training-only reward rose modestly in both studies, but no frozen intermediate task evaluation shows that PP gains were accumulating rather than remaining cohort-specific.

## Audit conclusion

The independent P4 cohort reversed the P3 pilot with two new catastrophes; PP also carries extra probe interaction cost.
