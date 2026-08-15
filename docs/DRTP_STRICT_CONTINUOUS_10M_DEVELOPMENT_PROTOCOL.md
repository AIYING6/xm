# DRTP Strict-Continuous 10M Development Protocol

## Status and precedence

**AUTHORIZED DEVELOPMENT TRAINING PROTOCOL / HELD-OUT AND CANONICAL WORK
REMAIN PROHIBITED.**

This protocol cancels only the execution of the proposed 3M→5M checkpoint
warm-restart maturity extension.  The warm-restart amendment and its runtime
persistence implementation remain retained as provenance and fault-tolerance
artifacts, but no legacy 3M checkpoint is a starting point for this study.

This protocol supersedes the fresh-trajectory 1M/2M/3M budget execution in
`DRTP_SG_MAPPO_TRAINING_MATURITY_ADDENDUM.md`.  The frozen method contract,
sampler constants, S2 task, evaluation contract, development retention gates,
and safety gates remain controlling and unchanged.

## 1. Strict continuous trajectories

Exactly four development-only trajectories are authorized:

| arm | seeds | start | terminal budget |
|---|---|---|---:|
| UTR-SG-MAPPO | 1901, 1902 | from scratch at update 0 | 39,063 updates = 10,000,128 steps |
| DRTP-SG-MAPPO | 1901, 1902 | from scratch at update 0 | 39,063 updates = 10,000,128 steps |

Every trajectory uses 4 environments × 64 rollout steps, the 116,728-parameter
matched Single-Graph model, unchanged PPO, seven frozen topology groups,
50% nominal anchor, S2 environment/reward/failure semantics, and the existing
actor information boundary.  UTR and DRTP differ only in fixed-uniform versus
bounded-adaptive conditional failure-group weights.

No legacy checkpoint is loaded.  There is no warm restart, no legacy resume,
no early stopping, no best-checkpoint promotion, no seed exclusion, no new
encoder/loss/curriculum, and no PPO sweep.

## 2. Runtime persistence from update zero

`runtime_state_checkpointing=True` is active in all four trajectories from
their initial invocation.  Each fixed checkpoint includes model, optimizer,
global update, Python/NumPy/PyTorch CPU/CUDA RNG, every environment state/RNG,
current observations, episode counters, sampler state, active DRTP selections,
`q`/EMA/difficulty/adaptation window return values and counts, and explicit
normalization state (currently `null`).  The implementation is bound to commit
`23ccaabc17fe7d3624b678fabe1b43626929df9f` and its deterministic
save→reload→next-update technical PASS.

The present protocol does not intentionally interrupt a trajectory.  These
states exist for crash recovery only; any such recovery must use strict runtime
continuation and be recorded in the run manifest.  Under normal completion,
`strict_continuous_trajectory=true` and `runtime_resume_used=false`.

## 3. Fixed checkpoints and evaluation

The following fixed labels are learning-curve checkpoints; no label can be
promoted or selected as a method result:

| label | update | environment steps |
|---|---:|---:|
| 500k | 1,953 | 499,968 |
| 1m | 3,907 | 1,000,192 |
| 1500k | 5,859 | 1,499,904 |
| 2m | 7,813 | 2,000,128 |
| 2500k | 9,766 | 2,500,096 |
| 3m | 11,719 | 3,000,064 |
| 3500k | 13,672 | 3,500,032 |
| 4m | 15,625 | 4,000,000 |
| 4500k | 17,578 | 4,499,968 |
| 5m | 19,531 | 4,999,936 |
| 5500k | 21,484 | 5,499,904 |
| 6m | 23,438 | 6,000,128 |
| 6500k | 25,391 | 6,500,096 |
| 7m | 27,344 | 7,000,064 |
| 7500k | 29,297 | 7,500,032 |
| 8m | 31,250 | 8,000,000 |
| 8500k | 33,203 | 8,499,968 |
| 9m | 35,156 | 8,999,936 |
| 9500k | 37,109 | 9,499,904 |
| 10m | 39,063 | 10,000,128 |

Every label is evaluated with the single frozen development tape
`420000–420099` and its nominal, F0, ten OOD timing/duration/compound
conditions.  Reported fields are `J_nominal`, `J_F0`, `J_OOD_mean`,
`J_OOD_worst`, collision, timeout, constraint violation, and exposure.
The final UTR-versus-DRTP development comparison uses only the common 10M
final checkpoint.

## 4. Maturity observation rule

`J_OOD_worst` is the primary maturity metric.  For a method and a one-million
step interval, continuing growth is the pre-existing condition: pooled relative
increase at least 5% and non-negative direction for both development seeds.
The first stable plateau is the earliest full-million label at which the two
immediately preceding full-million intervals both lack this continuing-growth
condition.  `J_nominal`, `J_F0`, `J_OOD_mean`, safety, and exposure are checked
alongside it and are never replaced by the primary metric.

10M is a maximum observation window, not a claim of automatic convergence.  If
either method has continuing growth in both 8M→9M and 9M→10M intervals, the
only maturity conclusion is `training maturity unresolved at <=10M`; the
controller stops and does not extend to 20M.

## 5. Decision boundary

At 10M, apply the unchanged development retention/safety matrix in
`DRTP_SG_MAPPO_METHOD_CONTRACT.md` to the two seeds and 420k tape.  Held-out
seeds `2001/2002/2003`, held-out tape `430000–430099`, canonical seeds `0–4`,
formal OOD studies, and any follow-on algorithm remain prohibited unless a
separate decision finds maturity, retention, seed consistency, and safety all
PASS.
