# PAPER-Q2 Final Statistics Report

**Independent unit:** training seed. Episodes are evaluation samples, not independent training replicates.

## Absolute strata

| Contract | Method | Seed scope | J_N | J_F0 | J_OOD mean | J_OOD worst | Timeout | Collision |
|---|---|---|---|---|---|---|---|---|
| T1_1M | UTR-SG-reference | 2201-2205 pooled seed mean | 111.159 | 89.192 | 89.466 | 80.543 | 0.911 | 0.033 |
| DRTP_development_3M | UTR-SG | 1901-1902 pooled | 147.157 | 127.929 | 120.607 | 103.149 | 0.8086 | 0.0136 |
| DRTP_development_3M | DRTP-SG | 1901-1902 pooled | 171.007 | 183.88 | 183.464 | 172.241 | 0.56 | 0.0014 |
| DRTP_heldout_10M | UTR-SG | 2001-2003 pooled | 160.34133333333335 | 162.18733333333333 | 155.02133333333333 | 138.35399999999998 | 0.7784666666666666 | 0.0224 |
| DRTP_heldout_10M | DRTP-SG | 2001-2003 pooled | 221.493 | 168.89333333333335 | 170.14766666666668 | 144.75866666666667 | 0.7267 | 0.0303 |

## Paired reliability summary

| Metric | Wins | Mean Δ | Median Δ | SD | IQR | MAD | Worst Δ |
|---|---|---|---|---|---|---|---|
| delta_nominal | 4/5 | 46.2314 | 40.794 | 63.39037716246843 | 43.742 | 33.885999999999996 | -16.254 |
| delta_F0 | 3/5 | 26.404 | 29.804 | 99.46706722830426 | 125.952 | 74.461 | -113.951 |
| delta_OOD_mean | 3/5 | 34.218399999999995 | 26.305 | 88.62939782769598 | 112.985 | 80.89500000000001 | -88.126 |
| delta_OOD_worst | 4/5 | 31.479400000000002 | 23.688 | 87.65819266218075 | 85.07400000000001 | 68.938 | -97.1 |

## Full paired seed record

| Seed | Stratum | ΔJ_N | ΔF0 | ΔOOD mean | ΔOOD worst | Note |
|---|---|---|---|---|---|---|
| 1901 | development_3M | 40.794 | 133.589 | 131.498 | 130.631 | positive on all published return deltas |
| 1902 | development_3M | 6.908 | -21.687 | -5.785 | 7.552 | F0/OOD mean negative; compound timeout breach +0.19 |
| 2001 | heldout_10M | 149.059 | 104.265 | 107.2 | 92.626 | positive returns; timeout lower |
| 2002 | heldout_10M | -16.254 | -113.951 | -88.126 | -97.1 | severe reversal; timeout higher |
| 2003 | heldout_10M | 50.65 | 29.804 | 26.305 | 23.688 | positive returns; timeout lower |

The five-pair cross-stratum summary is descriptive only because the two development pairs use a 3M contract and the three held-out pairs use a 10M contract. No pooled-episode significance test or homogeneous confirmatory p-value is permitted. The severe seed2002 reversal remains a required main-text reliability result.
