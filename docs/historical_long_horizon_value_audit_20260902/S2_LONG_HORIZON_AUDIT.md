# S2 Conservative-DRTP long-horizon audit

**Verdict:** `LONG_HORIZON_RETEST_NOT_JUSTIFIED`.

Historical budgets: [0.5, 1.0]M env steps.
Saved task-policy/runtime milestones: [0.25, 0.5]M.
Exact runtime recovery recorded: `True`.

## Existing matched performance evidence

Development: mean +8.581; median +9.185; wins 3/3 versus Original DRTP.
Closest Longer Replication: 1.0M, mean -10.141, median -9.421, wins 2/5, new catastrophes 1.

## Curve maturity

Training-only reward rose modestly during the final quarter; no intermediate frozen task evaluation exists to establish a late relative recovery.

## Audit conclusion

The closest frozen 1M conservative replication already reversed the local 0.5M performance relation and increased dispersion.
