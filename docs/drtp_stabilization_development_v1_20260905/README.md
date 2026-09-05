# DRTP Stabilization Development V1

This is a bounded development study for **Global-Anchored EGTR**, not a new
mechanism/root-cause audit and not confirmatory paper evidence.

It compares matched 1M trajectories for UTR, Original DRTP, EGTR, and three
fixed Global-Anchored EGTR strengths (`alpha = 0.35, 0.55, 0.75`) on three
development seeds.  Every arm retains the same environment, PPO, reward,
architecture and frozen failure semantics.  Only reset-time sampler logic
differs.

The anchored sampler first follows the unchanged EGTR evidence → projection →
local L1 trust-region path.  Its applied next-reset distribution is then:

`q_final = (1 - alpha) q_UTR + alpha q_EGTR`.

This gives a directly logged global UTR-distance bound while retaining a
nonzero adaptive path for every positive alpha.  Training creates no online
evaluation.  Fixed endpoint evaluation and the development assessment are
separate actions; neither a V2 revision nor confirmation may start
automatically.

The only permissible development outcomes are `V1_STRONG`,
`V1_PROMISING_NEEDS_ONE_REVISION`, and `V1_WEAK`.  They are based on the full
trade-off profile—upside, lower tail, central tendency, spread, nominal
retention, safety and observed sampler adaptivity—rather than one metric.
