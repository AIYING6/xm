# DRTP-STAB-A0 Counterexamples

The audit actively searched the preserved historical record for observations
that would invalidate an adaptive-weight-only explanation.

| Counterexample | Consequence |
|---|---|
| Strong held-out DRTP seed2001 ended with F0 weight `0.07`, equal to weak seed2002. | Persistent low F0 weighting is not seed2002-specific. |
| Strong development DRTP seed1901 ended with F0 weight `0.05`, lower than weak seed2002. | F0 de-emphasis does not uniquely imply failure. |
| Strong held-out seed2003 accumulated more CP/DL exposure than seed2002. | CP/DL concentration does not uniquely imply failure. |
| Seed2002 late PPO diagnostics were not more extreme than paired UTR or strong DRTP runs. | Generic PPO instability is not supported. |
| Final held-out evaluation occurred only at 10M. | A final-performance reversal cannot be placed causally before or after a weight event. |

These counterexamples rule out the proposed A0 requirement that the observed
weight pattern be both pre-divergence and materially absent from strong seeds.
They do not prove adaptive sampling is harmless; they show the available
history cannot identify it as the single actionable amplifier.

## Backup recovery addendum

The full logs strengthen the counterexample set: weak seed2002 has lower
all-run `TV_w` (12.270) than strong seeds1901 (14.904) and 2001 (13.376),
while strong seed2003 has the highest ranking-switch count (77). The proposed
common unstable-weight explanation is therefore contradicted by the observed
five-seed histories.
