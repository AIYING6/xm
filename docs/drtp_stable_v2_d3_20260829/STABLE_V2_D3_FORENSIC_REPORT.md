# Stable-v2 pilot D3 zero-training forensic

Source decision: `PILOT_NO_GO`. Source archive SHA256: `ac3e93c5c48e02fef605a23e8328b33f14b2ae4eb4372c44ffc2a80d48fdb7a0`.
No training or checkpoint evaluation was executed.

| Seed | Rollbacks | First rollback | First train divergence | First q divergence | G Original | G KLR | KLR−Original |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 3101 | 13 | 72 | 72 | 160 | 6.367 | 37.814 | 31.447 |
| 3102 | 9 | 142 | 143 | 160 | -24.155 | 32.938 | 57.093 |
| 3103 | 14 | 111 | 112 | 160 | 47.234 | 28.449 | -18.785 |

The full-rollback KLR candidate is closed under its frozen gate because upper-tail retention failed.
The result is nevertheless informative: all three KLR gains are positive, the catastrophic seed was removed,
and dispersion fell sharply, while seed3103 lost 18.785 points relative to its Original DRTP counterpart.

Rollback frequency is not an outcome discriminator: seed3101 benefited with 13 events, seed3102 benefited with
9, and seed3103 degraded with 14. Maximum attempted KL is likewise not a stable separator. The evidence supports
trajectory redirection by rare interventions, not a claim that one KL magnitude or event count causes failure.

For every seed, the training trajectory diverges at or immediately after the first rollback, while the first
sampler-q divergence appears later at update 160. This ordering is consistent with actor intervention preceding
sampler/exposure feedback; it does not prove that the later sampler change causes the final outcome.

## Seed3103 condition boundary

| Condition | J Original | J KLR | KLR−Original |
|---|---:|---:|---:|
| nominal | 68.328 | 88.767 | 20.438 |
| F0_44_80 | 48.768 | 26.733 | -22.035 |
| T28_28_80 | 47.960 | 35.043 | -12.918 |
| D120_44_120 | 42.335 | 24.212 | -18.122 |
| C28_120 | 38.797 | 16.730 | -22.066 |

Seed3103 is not a global optimization collapse: KLR improves nominal score but loses across all four failure
conditions, and its later training-return segments are not worse than Original. The upper-tail failure is therefore
fault-conditional and cannot be diagnosed from aggregate training return, trigger count, or maximum KL alone.

The only authorized next step is a zero-training design audit for one softer KL intervention that preserves the
attempted actor-update direction (for example backtracking/projection) instead of all-or-nothing rollback. This
does not authorize a new model, threshold sweep, seed reuse, training, or any change to mainline A.
