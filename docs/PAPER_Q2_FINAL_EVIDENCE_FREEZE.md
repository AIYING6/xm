# PAPER-Q2 Final Evidence Freeze

**Date:** 2026-08-23
**Status:** frozen zero-training closeout evidence.

## Immutable historical decisions

`DRTP_Q2_LIMITATION_ONLY`, the DRTP development `NO-GO`, and the held-out `FAIL` remain historical facts. This closeout does not relabel any of them as PASS.

## Evidence retained

| Contract | Method | Seed scope | J_N | J_F0 | J_OOD mean | J_OOD worst | Timeout | Collision |
|---|---|---|---|---|---|---|---|---|
| T1_1M | UTR-SG-reference | 2201-2205 pooled seed mean | 111.159 | 89.192 | 89.466 | 80.543 | 0.911 | 0.033 |
| DRTP_development_3M | UTR-SG | 1901-1902 pooled | 147.157 | 127.929 | 120.607 | 103.149 | 0.8086 | 0.0136 |
| DRTP_development_3M | DRTP-SG | 1901-1902 pooled | 171.007 | 183.88 | 183.464 | 172.241 | 0.56 | 0.0014 |
| DRTP_heldout_10M | UTR-SG | 2001-2003 pooled | 160.34133333333335 | 162.18733333333333 | 155.02133333333333 | 138.35399999999998 | 0.7784666666666666 | 0.0224 |
| DRTP_heldout_10M | DRTP-SG | 2001-2003 pooled | 221.493 | 168.89333333333335 | 170.14766666666668 | 144.75866666666667 | 0.7267 | 0.0303 |

The central causal ablation is matched UTR-SG-MAPPO versus DRTP-SG-MAPPO: the architecture, parameter count, PPO, seven topology groups, nominal anchor, environment, reward, actor boundary, budget, and evaluation protocol are matched; only group weighting differs.

## Mandatory limitations

- The 3M development and 10M held-out records are separate contract strata, not homogeneous replicates.
- All paired seeds remain visible, including development seed1902 and held-out seed2002.
- The evidence supports higher historical average/median robustness with non-negligible seed sensitivity; it does not support stable or universal superiority.
- The scope is the frozen 3-UAV heterogeneous simulation; scalability and hardware validation are not claimed.

## Claim boundary

Allowed wording: “DRTP shows higher average and median historical paired robustness under the frozen topology-perturbation protocol, while exhibiting non-negligible training-seed sensitivity.”

Prohibited wording: “stable,” “reliably superior,” “consistently outperforms,” “universal topology generalization,” or “deployment-ready.”
