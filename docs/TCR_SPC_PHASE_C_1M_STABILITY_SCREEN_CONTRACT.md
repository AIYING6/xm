# TCR/SPC Phase C — 1M Multi-Seed Stability Screening Contract

## Status and authorization

**Status: FROZEN FOR PHASE-C EXECUTION ONLY.** This contract authorizes the 1M development stability screen described below. It does not authorize a 3M continuation, 5M/10M training, a new held-out tape, canonical seeds, a method change, a PPO change, or post-result threshold changes.

The historical DRTP development and held-out conclusions remain immutable. In particular, this is not a re-run, repair, or re-interpretation of DRTP.

## Methods and invariants

The only three methods are:

| Arm | Actor-gradient operation |
| --- | --- |
| `utr_sg` | Identical split/bookkeeping path, with projection disabled. |
| `spc_sg` | Symmetric two-class PCGrad-style projection. |
| `tcr_sg` | One-sided projection of a conflicting failure gradient away from the nominal gradient. |

All arms retain exactly 116,728 trainable parameters, the matched Single-Graph actor and critic, PPO hyperparameters, reward, S2 environment, failure semantics, actor information boundary, 4x64 rollout, and 256-graph stratified actor minibatch. They use two nominal and two non-nominal environment streams, yielding exactly 128 nominal and 128 failure samples per actor projection update. Conditional on failure, the six frozen groups `F0`, `TE`, `TL`, `DS`, `DL`, and `CP` are uniformly cycled by the same fixed sampler in every arm.

No arm may instantiate DRTP `q`, EMA, difficulty, completed-return feedback, return-adaptive sampling, a new encoder, a new loss family, or condition metadata in actor/critic inputs.

## Training trajectories

The complete development seed set is `2002, 2101, 2102, 2103, 2104`.

- `2002` is the declared stress-development seed. It has historical viewed status and is permanently development-only.
- `2101`–`2104` must pass the launch-time prior-use audit against baseline commit `b3e13c1`; no prior training, tuning, or confirmatory result is permitted.
- Canonical seeds `0`–`4` are prohibited.
- `2001/2002/2003` are permanently not held-out; no result from them may be labelled held-out.

Every method-by-seed cell runs from scratch for exactly 3,907 updates × 4 environments × 64 steps = **1,000,192 environment steps**. Runtime-state persistence is enabled from update zero. The final update checkpoint is the only checkpoint used for Phase-C method comparison. Checkpoints may be written for recoverability but may never be promoted, selected, resumed from historical artifacts, or used to exclude a seed.

## Development evaluation tape

The sole Phase-C tape is the new development-only namespace **440000–440099**. It has 100 base episode IDs reused across each of the following twelve conditions:

1. `nominal`
2. `f0_seen_44_80`
3. `timing_28_80`
4. `timing_36_80`
5. `timing_52_80`
6. `timing_60_80`
7. `duration_44_40`
8. `duration_44_60`
9. `duration_44_100`
10. `duration_44_120`
11. `compound_28_120`
12. `compound_60_120`

The tape is non-canonical and development-only. Namespaces 380000–380099, 420000–420099, and 430000–430099 are forbidden. The tape manifest and its SHA256 are created before any Phase-C performance evaluation and bind all 15 final checkpoints to identical episode descriptors.

## Required final-checkpoint outcomes

For every method × seed, report `J_nominal`, `J_F0`, `J_OOD_mean`, `J_OOD_worst`, collision, timeout, constraint violation, failure exposure, per-condition returns, and seed-wise directions relative to paired `utr_sg`. The independent inferential unit is the training seed, never a pooled episode.

For `spc_sg` and `tcr_sg`, additionally report conflict rate, pre-projection cosine, post-projection cosine, \(\lVert g_N\rVert\), \(\lVert g_F\rVert\), projection magnitude, and final actor-gradient norm. `utr_sg` records the same telemetry with projection disabled.

`J_OOD_mean` and `J_OOD_worst` are respectively the mean and minimum `J` over conditions 3–12. Safety and exposure aggregates are computed across `F0` plus all ten OOD conditions.

## Pre-registered catastrophic-seed classification

For a candidate arm (`tcr_sg` or `spc_sg`) and the same training seed's paired `utr_sg` reference, define:

\[
r_{F0}=J_{F0}^{candidate}/J_{F0}^{UTR},\qquad
r_{worst}=J_{OOD,worst}^{candidate}/J_{OOD,worst}^{UTR}.
\]

The seed is **catastrophic** if either performance combination holds:

- \(r_{F0}<0.70\) and \(r_{worst}<0.85\); or
- \(r_{worst}<0.70\) and \(r_{F0}<0.85\).

It is also catastrophic under the safety-associated combination:

- `timeout_candidate - timeout_utr > 0.20`; and
- \(r_{F0}<0.85\) or \(r_{worst}<0.85\).

The definition is identical for SPC and TCR. It is frozen before training and cannot be changed after any Phase-C result is seen.

## Decision algorithm

The only allowed decisions are `PHASE-C GO`, `PHASE-C NO-GO`, `PHASE-C EARLY NO-GO`, and `TECHNICAL INVALID`.

`TECHNICAL INVALID` applies to any information-boundary, sampler, runtime-persistence, projection, tape, checkpoint, or integrity-contract failure.

`PHASE-C EARLY NO-GO` applies if TCR has at least 2/5 catastrophic seeds, shows cross-seed bifurcation materially worse than UTR, or has systemic safety deterioration. A favorable pooled mean cannot override this result.

For this contract, **materially worse cross-seed bifurcation** means all three of: (i) the TCR seed-wise `J_OOD_worst` range is more than twice the UTR range; (ii) the TCR sample standard deviation is more than twice the UTR sample standard deviation; and (iii) at least one paired TCR `J_OOD_worst` ratio is below 0.85. **Systemic safety deterioration** means any nonzero TCR constraint-violation aggregate, or both a pooled failure-timeout increase above 0.05 and failure-timeout increase above 0.05 in at least 3/5 paired seeds. These definitions are pre-result execution rules, not retrospective interpretations.

`PHASE-C NO-GO` applies if TCR has exactly one catastrophic seed, or if it has none but both pooled `J_OOD_mean` and pooled `J_OOD_worst` are not higher than UTR and fewer than 3/5 seed-wise `J_OOD_worst` directions are positive.

`PHASE-C GO` requires all of the following: zero catastrophic TCR seeds; valid exposure and zero constraint violation; no systematic safety deterioration; pooled OOD mean and worst at least non-inferior to UTR; positive OOD-worst direction in at least 3/5 seeds; no clear systematic inferiority to SPC; and no catastrophic stress-seed-2002 outcome.

GO means only that TCR is eligible for a separately authorized 1M→3M continuation. It is not a superiority, asymmetric-anchor, held-out, or paper-method confirmation.

SPC remains a mandatory diagnostic control. TCR better than UTR but comparable to SPC does not support an asymmetric-anchor claim; SPC better than UTR while TCR is worse rejects the nominal-anchor hypothesis; only stable TCR superiority over both can motivate later validation.

## Stop rule

After all 15 trajectories and their unified final-checkpoint evaluation are audited, Phase C stops. No continuation, held-out, canonical, OOD formal, ablation, architecture, projection, PPO, environment, reward, or threshold modification is authorized by this contract.
