# P1B Decision Memo v1.1 — recovery headline decision

- date: 2026-08-07
- protocol: survival-protocol-v1.1 (frozen before running; tag `survival-protocol-v1.1`)
- local re-execution on locked held-out data; results identical to the sandbox run
  (verified cell-by-cell: RMST summary, sensitivity table, bootstrap intervals)
- status: DECISION MADE — conservative comparator/time-scale claim

## 1. Data audit (11/11 PASS, local)

| check | value |
|---|---|
| rows | 10,800 |
| recovered | 5,358 |
| exposed unrecovered | 714 |
| unexposed (pre-termination) | 4,728 |
| recovery-clock mismatches | 0 |
| censor-time mismatches | 0 |
| horizon | 260 (all formal runs) |
| primary cells (method×seed×scenario, Early+Nominal) with exactly 100 exposed | 54/54 |
| delayed+late exposed (pooled) | 672 (method-dependent: full 8 … no_graph 204) |

## 2. Primary RMST(220), mean ± SD over 3 training seeds

| method | RMST(220) | Δ_s (Full − method, per seed) | Δ mean |
|---|---:|---|---:|
| **EA-RG Full** | **14.47 ± 3.10** | — | — |
| w/o Role-Pair Mod | 13.63 ± 3.86 | +5.88 / −6.90 / +3.53 | +0.83 |
| HAPPO | 14.14 ± 2.94 | +4.64 / −1.00 / −2.67 | +0.32 |
| MAPPO | 20.39 ± 7.72 | −1.22 / −17.67 / +1.11 | −5.93 |
| Wider Single-Graph | 16.49 ± 8.64 | −9.01 / +0.87 / +2.06 | −2.03 |
| w/o Task-Support | 29.57 ± 24.31 | −3.54 / −45.85 / +4.07 | −15.11 |
| w/o Gate Prior | 48.48 ± 41.72 | −18.41 / −3.41 / −80.23 | −34.01 |
| Single Graph | 68.28 ± 91.99 | +5.25 / −7.10 / −159.60 | −53.82 |
| No Graph | 78.03 ± 36.91 | −27.00 / −61.04 / −102.65 | −63.56 |

Negative Δ = Full better. Negative Δ_s means Full's RMST is smaller.

## 3. Decision Gate outcome

- **Gate A fails**: Full is NOT better than HAPPO on primary RMST (14.47 vs 14.14), and
  the Full−HAPPO seed deltas are mixed (+4.64 / −1.00 / −2.67).
- **Gate B does not cleanly pass**: Full is better than MAPPO and wider single-graph on
  the mean, but the wider-single-graph advantage is driven by seed0 (−9.01), with seed1/2
  slightly reversed (+0.87 / +2.06) — not a stable full-horizon superiority.
- **Gate C is not literal**: Full's RMST(220) mean is still better than MAPPO/wider.

=> **NO CLEAN A/B/C GATE — conservative comparator/time-scale claim.**

> EA-RG shows a directionally consistent early post-failure recovery advantage over MAPPO
> under matched failure exposure, while full-horizon censor-aware recovery is competitive
> rather than uniformly superior to HAPPO and the wider single-graph baseline.

This sentence becomes the P2 recovery core narrative.

## 4. Early-window evidence (the robust, reproducible result)

Full vs MAPPO per-seed Δ_s at early windows are ALL negative (3/3 seeds):

| τ | Δ_s (seed0/1/2) | bootstrap 95% CI | P(Δ<0) |
|---|---:|---|---:|
| 50 | −3.09 / −4.57 / −1.66 | [−4.71, −1.70] | 1.0000 |
| 80 | −2.64 / −7.27 / −1.21 | [−7.16, −1.05] | 0.9996 |
| 100 | −2.42 / −9.07 / −0.84 | [−8.84, −0.57] | 0.9937 |

τ = 80 has task meaning: node-failure active duration = 80 steps — EA-RG re-establishes
the task chain faster while the failed node is still down. τ=220 interval crosses 0
([−17.0, +2.2]).

## 5. Headlines removed (must NOT appear in P2)

1. "EA-RG recovers ~34% faster than HAPPO" — holds only for conditional mean E[T|rec]
   (10.8 vs 16.3); primary RMST 14.47 vs 14.14 does not support it. Remove from Abstract.
2. "59% faster than wider single-graph" as a headline — seed-mixed at τ=220.
3. "RPG sacrifices a little reliability for faster recovery" — RMST Full 14.47 vs
   w/o-RPG 13.63 with mixed seed deltas; no causal speed-for-reliability story.

## 6. Component verdicts (frozen)

- **Role-Pair Modulation**: "provides limited independent benefit under primary
  RMST(220)" (mean slightly worse than Full; seed-mixed). Auxiliary static modulation.
- **Gate Prior**: strong average damage on removal (14.47 → 48.48) but high seed
  heterogeneity (−18.4 / −3.4 / −80.2); keep as "structured initialization improving
  optimization stability and cross-seed consistency within the role-pair modulation
  design" — NOT a necessary component claim.
- **Task-Support**: removal hurts on average (14.47 → 29.57) but seed-mixed
  (−3.54 / −45.85 / +4.07); keep as "empirically supported task-dependent relation";
  do NOT upgrade to a post-failure reorganization mechanism.

## 7. P2 implications

1. Abstract: drop conditional-time percentages vs HAPPO/wider as headline; lead with
   early-recovery-relative-to-MAPPO + competitive full-horizon.
2. t_rec renamed: **conditional mean recovery time among recovered failure-exposed
   episodes**.
3. RQ2 main evidence: KM + RMST(220) + early-window sensitivity (τ=80 rationale).
4. Delayed/Late: terminal reliability / landmark sensitivity only.
5. Discussion: acknowledge full-horizon HAPPO and w/o-RPG competitiveness.
6. No retraining.
