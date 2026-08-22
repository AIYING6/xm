# DRTP-STAB-A0 Weight Dynamics

## Frozen mechanism

DRTP retains a 50% nominal anchor. Its six failure-group probabilities are
updated every 32 updates after a 128-update warmup using completed-return EMAs,
bounded exponentiated weighting, 0.5 smoothing, and a bounded simplex with
`q_min=0.05` and `q_max=0.35`. The frozen code preserves mass and bounds.

The log schema would support the requested M1--M6 descriptors (`DW`, total
variation, maximum dominance, entropy, ranking flips, and acceleration) if
the historical `weight_update` rows existed. They do not currently exist for
the relevant historical runs, so no numerical M1--M6 estimate is reported.

## Available seed2002 snapshots

| State | F0 | TE | TL | DS | DL | CP |
|---|---:|---:|---:|---:|---:|---:|
| approximately 0.5M | 0.07 | 0.05 | 0.09 | 0.10 | 0.34 | 0.35 |
| terminal | 0.07 | 0.22 | 0.05 | 0.05 | 0.25 | 0.35 |

The snapshots establish concentration on CP/DL and de-emphasis of F0. They do
not establish oscillation, abnormal total variation, ranking churn, or a
seed2002-specific instability signature.

## Interpretation

The available observations are compatible with adaptive under-exposure of F0,
but are not an actionable stability diagnosis. Successful DRTP seed2001 also
ended with F0=`0.07`; successful development seed1901 ended with F0=`0.05`;
and successful held-out seed2003 accumulated even more CP/DL exposure than
seed2002. Weight concentration therefore remains a correlate, not a unique
failure mechanism.

## Result

No evidence supports a claim that abnormal weight volatility or concentration
is present in both failed seeds and materially absent from strong seeds before
their behavioral divergence.

## Backup recovery addendum — controlling analysis

The recovered full trajectories preserve the same conclusion. Full-run
`TV_w` is 14.904/16.298/13.376/12.270/12.072 for seeds
1901/1902/2001/2002/2003 respectively. Thus weak seed1902 is highest, while
the severe held-out weak seed2002 is lower than strong seeds1901 and 2001.
Strong seed2003 has 77 top-1 ranking switches, above weak seeds1902 (32) and
2002 (37).

In the prespecified 0--0.25M interval, mean L1 weight movement is 0.04654
(strong 1901), 0.03684 (weak 1902), 0.03942 (strong 2001), 0.04338 (weak
2002), and 0.04815 (strong 2003). The failed seeds therefore do not share an
early excess-volatility, entropy-collapse, or ranking-churn signature.

Full metrics are in `artifacts/drtp_stab_a0/seed_weight_metrics.csv`.

Early difficulty-to-weight correlations are likewise non-diagnostic: 0.318,
0.138, 0.053, 0.117, and 0.252 for seeds 1901, 1902, 2001, 2002, and 2003.
The failed seeds are not the strongest difficulty-reactive trajectories.
