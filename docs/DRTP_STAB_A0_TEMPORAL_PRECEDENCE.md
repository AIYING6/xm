# DRTP-STAB-A0 Temporal Precedence

## Pre-registered question

The relevant question is whether an abnormal adaptive-weight signature occurs
before, or at least around, the first reproducible policy/performance
divergence. Final-weight differences alone are insufficient.

## Seed2002

The maintained held-out forensic report establishes an early internal learning
deficit by approximately 1M steps: DRTP EMA nominal/F0/mean-other values were
56.2/52.9/46.2 versus UTR values 114.9/94.7/94.6. By approximately 3M the
DRTP internal values had recovered substantially. The report also preserves a
0.5M adaptive-weight snapshot showing F0 de-emphasis and CP/DL concentration.

This supports only the interval statement:

\[
T_{\mathrm{weight\ snapshot}} \lesssim 0.5\mathrm{M},\qquad
T_{\mathrm{internal\ deficit}} \approx 1\mathrm{M}.
\]

It does **not** establish that weight dynamics caused the deficit: the
available records contain no continuous q/difficulty trajectory, no aligned
training-time behavior telemetry, and no per-milestone held-out evaluation.
The final F0/OOD reversal was measured only at 10M.

## Seed1902

Seed1902 was a frozen weak development seed at 3M (`J_F0` and OOD-mean
directions unfavorable, plus one timeout safety breach). No continuous
historical weight or behavioral telemetry is available to date its divergence.

## Classification

Temporal precedence for adaptive-weight amplification is **unresolved**, not
confirmed. The evidence cannot distinguish H1 (weights first) from H2
(policy/return dynamics first), and therefore cannot support an intervention.

Machine-readable event boundaries are in
`artifacts/drtp_stab_a0/temporal_events.json`.
