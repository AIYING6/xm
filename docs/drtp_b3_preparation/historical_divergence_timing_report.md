# Historical divergence timing audit

Status: `HORIZON_PROXY_COMPLETE`.

This zero-training audit uses only archived formal and independent cohort
logs. At each fixed 500-update bin it calculates the paired DRTP-minus-UTR
mean training reward for each seed. A cohort-direction proxy requires at
least 3/5 pairs in opposing directions in the two cohorts and must persist
for two consecutive bins.

The first persistent proxy separation ends at **0.384M environment steps**.
This is not a final-performance onset and does not establish any mechanism;
it solely supports the prospective observation horizon. Consequently, B3's
1.000192M first-stage window can falsify the predeclared mechanism chain when
all six trajectories and telemetry products are valid.

The full binned cohort table is retained under the local audit output. The
tracked `divergence_timing_by_seed.csv` is the per-seed, per-bin provenance
table needed to reproduce this horizon judgment.
