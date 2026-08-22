# DRTP-STAB-A0 PPO Interaction

The historical held-out forensic compared late 5M--10M PPO summaries for
seed2002. DRTP had value loss `0.510`, gradient norm `4.69`, approximate KL
`0.00150`, clip fraction `0.0137`, and explained variance `0.974`; the paired
UTR values were `0.573`, `4.76`, `0.00164`, `0.0155`, and `0.970`.

These ranges do not indicate a seed2002-specific numerical PPO explosion.
Seed2002's maximum/95th-percentile gradient norms (`54.97`/`12.35`) were also
lower than successful DRTP seed2001 (`147.47`/`22.11`) and seed2003
(`113.86`/`19.09`). Late 9.5M--10M parameter displacement was comparable
across the relevant runs (seed2002 DRTP `0.149`; DRTP seeds2001/2003
`0.138`/`0.133`; UTR seed2002 `0.144`).

Therefore generic PPO/optimization instability is not supported. Since the
per-update PPO and q histories are unavailable, lead/lag tests between KL,
clip fraction, difficulty and weight changes are not estimable. This is an
evidence limit, not a negative finding about all possible interactions.

## Backup recovery addendum

Full PPO logs are now available and confirm the original aggregate conclusion:
no seed2002-specific KL, clip-fraction, gradient, value-loss, or entropy
explosion precedes the final held-out reversal. This does not prove PPO played
no role; it rejects generic numerical PPO instability as the actionable A0
target.
