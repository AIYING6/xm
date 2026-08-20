# T4 — Frozen Policy Sensitivity Report

## Protocol

This report measures **offline action-distribution sensitivity** of frozen actors to currently recorded, locally plausible attacker support fields. It is neither an environment counterfactual nor a performance evaluation.

The five changed attacker-observation fields were: direct detection (18), inbound connectivity (28), inbound message age (29), target-cache age (30), and target-cache confidence (31). Two pre-specified probes were used:

1. **Mask probe:** sets them to locally plausible unavailable/stale values `(0, 0, 1, 1, 0)`.
2. **Permutation control:** permutes the complete five-field tuple only within recorded `(family, phase, progress bin, topology)` strata.

The statistic is total-variation distance (TVD) between the original and perturbed attacker action distributions. The second probe is important because it only substitutes values already recorded in the same coarse legal stratum.

## Failure-condition results

| Seed | Rank | Mask TVD | Permutation TVD |
|---|---|---:|---:|
| 2201 | Intermediate | 0.280 | 0.044 |
| 2202 | Good | 0.364 | 0.178 |
| 2203 | Weak | 0.077 | 0.027 |
| 2204 | Good | 0.487 | 0.090 |
| 2205 | Weak | 0.208 | 0.042 |

| Group | Mask TVD | Permutation TVD |
|---|---:|---:|
| Good (2202, 2204) | 0.426 | 0.134 |
| Weak (2203, 2205) | 0.142 | 0.034 |
| Good − weak | **0.283** | **0.100** |

Thus the effect is present under both a deliberately unavailable/stale support state and a within-stratum recorded-value control. It is not solely an artifact of one implausible masked input.

## Topology-transition focus

The good-minus-weak mask-TVD gap is `0.145` before the scheduled failure onset, rises to `0.322` in the early post-onset phase, and remains `0.310` later. The pre-registered amplification condition was `|early| > |pre| + 0.005`; it is satisfied by a wide margin.

This pattern is consistent with a utilization gap that becomes more visible around topology perturbation. It does **not** establish a causal performance mechanism: the probes are offline, and the same recorded states were not replayed in a simulator.

## Pre-registered decision inputs

The U1 rule required mask gap at least `0.02`, permutation gap at least `0.01`, topology amplification, and at least two absolute seed-level Spearman associations of `0.70` or greater. The observed values are `0.283`, `0.100`, amplification PASS, and three associations at `+0.80`; therefore the frozen result is U1.

No policy, optimization, or sampling change follows from this report without separate authorization.
