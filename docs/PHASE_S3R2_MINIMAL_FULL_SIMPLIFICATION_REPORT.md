# Phase S3-R2 Minimal Full Simplification Report

**Protocol:** `PHASE-S3-R2-V1`  
**Artifact class:** DEVELOPMENT_ONLY  
**Decision:** **NO-GO — Multi-Relation encoder diagnosis required**

## Scope and provenance

S3-R2 trained only the simplified Full arm:

```text
Multi-Relation graph + MAPPO + union/global residual
Role-Gate: removed
```

The three development seeds were `1501`, `1502`, and `1503`. Each completed
782 updates, equal to 200,192 environment steps. Each fixed final checkpoint
was evaluated on the same 100 nominal/failure pairs with IDs `340000–340099`.
Checkpoint hashes matched their manifests, and all final PPO diagnostics were
finite. No canonical seed, canonical result, or Phase 3A training was used.

## Results

| Seed | `J_nominal` | `J_failure` | `Delta_J` | Exposure | Horizon success nominal/failure |
|---:|---:|---:|---:|---:|---:|
| 1501 | 14.340 | 1.029 | 13.312 | 1.00 | 0.00 / 0.00 |
| 1502 | 30.094 | 12.064 | 18.029 | 1.00 | 0.00 / 0.00 |
| 1503 | 17.492 | -1.858 | 19.350 | 1.00 | 0.00 / 0.00 |
| **Mean** | **20.642** | **3.745** | **16.897** | **1.00** | **0.00 / 0.00** |

The matched Single-Graph comparator on the same S3-R tape has seed-level
nominal means `32.547`, `24.037`, and `51.182`, with mean `35.922`; its mean
`Delta_J` is `7.607`. Thus simplified Full reaches only 57.5% of the
comparator's nominal mean and has a larger average failure degradation.

## Pre-registered gate assessment

| Gate | Result | Evidence |
|---|---|---|
| All runs complete with finite diagnostics | PASS | 3/3 runs, 782/782 updates, final checkpoint hashes match. |
| Shared tape and exposure provenance | PASS | IDs `340000–340099`, all 100 failure pairs exposed in each seed. |
| Nominal within 10% of Matched SG | **FAIL** | `20.642 / 35.922 = 57.5%`, not at least 90%. |
| Lower `Delta_J` in ≥2 seeds and mean | **FAIL** | Lower in only seed 1501; mean `16.897 > 7.607`. |
| No low-competence pseudo-robustness seed | PASS | All simplified nominal seed means are positive, but this does not rescue the failed competence gate. |

The simplified Full did not recover nominal competence to the capacity-matched
Single-Graph level. Removing Role-Gate also did not improve the robustness
estimand against that comparator. The result therefore does not support
entering S4 or Phase 3A.

## Interpretation boundary

This is a development diagnosis, not a paper superiority result. The evidence
supports the narrow conclusion that **Role-Gate removal alone is insufficient
to make the current Multi-Relation encoder competitive at 200,192 steps**.
It does not prove that every possible multi-relation encoder is invalid.

The training seed, not the 300 episode-level observations, is the independent
replication unit. Episode-level rows are used for paired diagnostics and
provenance; no episode-level significance test is claimed.

The horizon-success field remained zero for all three simplified Full seeds.
This is a secondary warning and does not replace the primary `J` / `Delta_J`
screen, but it reinforces that the policy has not demonstrated stable task
completion.

## Final decision and next step

```text
S3-R2 = NO-GO
Role-Gate removal did not solve the nominal-competence problem.
S4 = NO-GO
Phase 3A = NO-GO
```

Do not extend training blindly and do not alter the S2 environment to improve
these results. The next permitted work is a separately frozen
**Multi-Relation encoder diagnosis** covering relation aggregation, branch
scale/normalization, union residual dominance, attention degeneration, and
actor-side optimization. Any repair must be tested under an equal-budget,
pre-registered development protocol before canonical training is discussed.
