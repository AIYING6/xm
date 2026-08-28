# H2 zero-training gate report

Status: `H2_WEAK_CANDIDATE`

## Integrity

- six completed B3 trajectories; 1,000,192 steps each; 3,000 retained evaluation rows; fixed development tape.
- analysis reads archived logs/telemetry only; no training, evaluation rerun, checkpoint promotion, or algorithm change.

## Candidate pattern and its limits

The following descriptive sequence occurs for DRTP seed2702:

1. At 0.25M, training return is not weak, but critic value loss is higher than
   the two favorable DRTP seeds (0.603 versus 0.275/0.323).
2. By 0.50M, approximate KL is higher than both favorable DRTP seeds
   (0.00176 versus 0.000235/0.00124), while its failure-group q distance from
   uniform rises from 0.202 in 0–0.25M to 0.602 in 0.25–0.50M.
3. In that same 0.25–0.50M block, at tau=60 after a scheduled failure,
   DRTP-2702 has lower information-path availability (0.339) than DRTP-2701
   (0.568), DRTP-2703 (0.702), and paired UTR-2702 (0.798). Its task-support
   rate is also far below paired UTR-2702 (0.007 versus 0.125).
4. At 1M, DRTP-2702 is unfavorable to paired UTR in all four fault conditions
   (Delta J from -85.84 to -89.85; timeout higher by 0.13 to 0.28).

This is a time-ordered **candidate**, not a proven mechanism. Its limits are
decisive: early task competence is not consistently weak; DRTP-2703 also has
large q deviations without the same final reversal; later 2702 information
path availability recovers; and only one adverse seed is available. Thus
neither the required cross-seed replication nor a unique DRTP causal pathway
is established.

## Frozen action

No new training, 3M continuation, rerun, seed replacement, or stabilization
modification is authorized by this audit. A future request may propose the
smallest independent new-seed falsification experiment for this *specific*
candidate, but only after separate human review; it may not modify DRTP.
