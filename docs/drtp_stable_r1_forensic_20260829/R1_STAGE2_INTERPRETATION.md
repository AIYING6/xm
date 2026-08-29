# R1 Stage-2 milestone interpretation

Stage-2 consumed the immutable forensic archive with SHA256 `c316d72fdf23e75f99bc48ff425c7443caf4b3305eec9bcc6e34fd235d72e5d5`. It evaluated 30,000 frozen development-tape episodes: three arms, five seeds, four milestones, five conditions, and 100 common episode IDs per cell. No training, continuation, checkpoint promotion, or checkpoint selection occurred.

## Temporal task outcome

`G` denotes `J_pert_mean(method) - J_pert_mean(UTR)`.

| Seed | 0.25M Conservative G | 0.5M | 0.75M | 1M | Interpretation |
|---:|---:|---:|---:|---:|---|
| 3001 | -11.70 | -7.45 | -94.77 | -78.31 | Both Original DRTP and Conservative deteriorate strongly at 0.75M (Original G=-82.54). This is not Conservative-specific evidence. |
| 3003 | -13.30 | +13.37 | -6.22 | -7.95 | Conservative is ahead of Original through 0.5M, then loses relative to it by 0.75M; this is the first persistent Conservative-specific reversal. |
| 3004 | +5.39 | -20.22 | +30.29 | -26.70 | The largest reversal occurs between 0.75M and 1M: Original remains positive (+45.27 to +30.82), whereas Conservative falls from +30.29 to -26.70. |

Thus the available checkpoints do not support one common timing for every bad seed. A generic 0.25M or 0.5M intervention would not be mechanism-aligned. The most informative counterfactual remains seed3004, whose policy degradation is late (0.75M–1M) and Conservative-specific.

## Training and sampler dynamics

Across Conservative failure seeds, critic/value loss, advantage standard deviation, and gradient norm are often higher than in the two success seeds; however, their timing is not uniform. PPO KL and clip fraction remain small rather than displaying a common blow-up. Every Conservative seed has 118 adaptation boundaries, while trust-region activation and distance from uniform do not isolate the three failure seeds from the two successes. These are descriptive associations, not an actionable causal chain.

## Decision boundary

Stage-2 rejects the simple explanation that one shared sampler excursion precedes all three failures. It also does not establish a repeatable PPO/critic precursor in at least two failure seeds that is absent from successful controls. Therefore Stable-v2 is **not scientifically authorized** from this evidence alone. Any future mechanism proposal must first define and independently test a repeated, time-leading candidate without changing the historical R1 decision.
