# DRTP/UTR Q2 Formal Paired Five-Seed Confirmation Contract

**Protocol:** `DRTP-UTR-Q2-FORMAL-PAIRED-5SEED-V1`  
**Status:** `FROZEN BEFORE PERFORMANCE / LONG TRAINING STARTED 2026-08-24`
**Purpose:** close the single remaining high-value evidence gap with one
prospective, common-contract UTR-versus-DRTP comparison. This is not a rescue
of the historical held-out result and does not erase any prior decision.

## 1. Immutable history

The following remain part of the main-paper evidence and may not be rewritten:

- DRTP development `NO-GO`;
- held-out v2 `HELD_OUT_FAIL`;
- `DRTP_Q2_LIMITATION_ONLY`;
- development seed1902 weakness and held-out seed2002 catastrophic reversal;
- REL-A0 conclusion: high average return with reproducible seed sensitivity;
- S1-R P3 `F_REFERENCE_NOT_REPRODUCED` and unresolved causal root cause.

The new experiment is prospective evidence under a new contract. It cannot be
pooled with historical 3M/10M strata as though all runs were one homogeneous
confirmatory sample.

The contract was frozen at commit `05c37c3` before any of the prospective
trajectories started. Local execution began afterwards under the unchanged
contract, using the output root
`results/formal/drtp_utr_q2_paired_5seed`.

## 2. Methods and sole contrast

Exactly two methods are permitted:

1. `UTR-SG-MAPPO`: fixed 50% nominal anchor; the remaining 50% is distributed
   uniformly across the six frozen failure groups.
2. `DRTP-SG-MAPPO`: the same 50% nominal anchor and same six groups, with the
   already frozen bounded adaptive group-weight update.

Both methods retain the 116,728-parameter matched Single-Graph actor/critic,
PPO, reward, S2 environment, failure semantics, actor information boundary,
seven topology groups, runtime persistence, and inference-time architecture.
The only intended difference is fixed-uniform versus bounded-adaptive
conditional failure-group weighting. No new encoder, loss, curriculum, reward,
PPO sweep, or DRTP modification is permitted.

## 3. Prospective training seeds

The paired training seeds are exactly:

`2301, 2302, 2303, 2304, 2305`

They were selected as a consecutive namespace before any run or result. A
pre-freeze repository and Git-history semantic search found no prior use of
these values as training seeds. Seeds `0–4`, all historical development/
held-out seeds, and any replacement seed are prohibited.

Every seed is an independent training replicate. Evaluation episodes are not
independent method replicates. All ten method-by-seed trajectories must be
reported; weak runs cannot be excluded, retried for performance, or replaced.

## 4. Common mature budget

Every trajectory is from scratch and strict continuous for:

- `39,063` PPO updates;
- `4 environments × 64 rollout steps`;
- `10,000,128 environment steps`.

The budget reuses the existing frozen 10M maturity-observation endpoint. Fixed
0.5M milestones may be saved for learning curves and crash recovery only.
Final comparison uses only the common 10M final checkpoint. There is no early
stopping, best-checkpoint promotion, seed-specific budget, historical resume,
or post-result extension.

Runtime-state persistence is active from update zero. A genuine infrastructure
interruption may resume only from the latest exact runtime-state checkpoint and
must be disclosed. A model-only/warm restart is technical invalid.

## 5. Prospective evaluation tape

Before performance evaluation, generate and hash exactly one new paired tape:

`490000–490099`

Each base ID is reused across 12 frozen conditions:

- nominal;
- F0 `44/80`;
- timing `28/80`, `36/80`, `52/80`, `60/80`;
- duration `44/40`, `44/60`, `44/100`, `44/120`;
- compound `28/120`, `60/120`.

There are 100 episodes per condition and 12,000 total evaluation records over
10 final checkpoints. All original episodes remain in unconditional return and
safety summaries. Pre-trigger collisions are never removed or relabeled.

Technical trigger validity is evaluated within the alive-at-onset risk set:

`trigger_success_rate = exposed episodes alive at onset / episodes alive at onset`.

The tape is prospective formal evidence but is not a canonical-seed tape.

## 6. Endpoints and reporting

For every method × seed report:

- `J_nominal`, `J_F0`, `J_OOD_mean`, `J_OOD_worst`;
- all ten OOD condition returns;
- collision, timeout, and constraint violation;
- pre-trigger collision, survival-to-onset, risk-set size, and trigger validity;
- task-support, legal-information, path-switch, direct/relay path, cache-age,
  traveled-distance, and control-effort telemetry where available;
- realized training-group counts and DRTP weight/EMA/difficulty histories;
- final and milestone checkpoint/runtime-state SHA256.

The primary statistical unit is the paired training seed (`n=5`). Report raw
paired differences, mean, median, sample SD, IQR, MAD, win count, worst
degradation, and paired ratios. Episode-pooled p-values cannot establish method
superiority. Any bootstrap interval is descriptive because `n=5`.

## 7. Frozen catastrophic definition

For a paired seed, DRTP is catastrophic when either performance combination
holds:

1. `J_F0(DRTP)/J_F0(UTR) < 0.70` and
   `J_OOD_worst(DRTP)/J_OOD_worst(UTR) < 0.85`; or
2. `J_OOD_worst(DRTP)/J_OOD_worst(UTR) < 0.70` and
   `J_F0(DRTP)/J_F0(UTR) < 0.85`.

It is also catastrophic when `timeout(DRTP)-timeout(UTR) > 0.20` and either
F0 or OOD-worst ratio is below `0.85`. This definition is inherited from the
pre-result Phase-C stability contract and is not tuned to the new seeds.

## 8. Prospective publication decision

### `FORMAL_CONFIRMATION_PASS_SEED_SENSITIVE`

All technical checks pass and all of the following hold:

- mean and median DRTP−UTR differences are positive for `J_F0`,
  `J_OOD_mean`, and `J_OOD_worst`;
- at least `3/5` paired seeds favor DRTP on each of those three endpoints;
- pooled nominal ratio is at least `0.95` and median nominal paired difference
  is non-negative;
- no more than one catastrophic DRTP seed;
- pooled constraint violation is exactly zero;
- neither collision nor timeout has a pooled DRTP−UTR increase above `0.05`,
  and neither worsens in at least four of five seeds;
- every onset-surviving failure episode triggers correctly and all scheduled
  episodes remain reported.

This verdict supports only a high-upside, seed-sensitive claim. It does not
authorize “stable”, “consistent”, or “universally superior”.

### `FORMAL_CONFIRMATION_LIMITATION_ONLY`

Technical validity passes but at least one PASS row fails without meeting the
demotion rule below. DRTP remains a secondary/limitation result; the manuscript
cannot present prospective superiority.

### `FORMAL_CONFIRMATION_FAIL_DEMOTE_DRTP`

Use this verdict if at least two seeds are catastrophic, or if at least two of
the three primary robustness endpoints have non-positive mean and median
paired differences, or if constraint/safety validity fails materially. DRTP is
demoted from the main-method route; no DRTP-v2 or replacement algorithm follows.

### `FORMAL_CONFIRMATION_TECHNICAL_INVALID`

Use only for a contract, checkpoint, runtime-persistence, tape, evaluator, or
artifact-integrity failure. Poor performance is not technical invalidity.

## 9. Stop rule

After the 10 final checkpoints are evaluated and the report is generated,
stop. Do not automatically launch additional seeds, canonical seeds, component
ablations, scalability, HIL, a new method, or a larger budget. Subsequent work
is manuscript reconstruction from the frozen evidence.
