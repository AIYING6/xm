# PP-DRTP P3 pilot contract

**Status:** `P3_PILOT_AUTHORIZED`  
**Scope:** Mainline-B development only.  It must not be merged with, or alter,
Mainline-A results, text, checkpoints, tapes, or claims.

## Frozen experiment

| Item | Frozen value |
| --- | --- |
| Arms | `utr_sg`, `drtp_sg`, `pp_drtp_sg` |
| Training seeds | `3401`, `3402`, `3403` |
| Budget | 1,953 updates = 499,968 training environment steps per trajectory |
| Total trajectories | 9, from scratch, paired by seed |
| Checkpoints | fixed 250k and final 500k; final only for the gate |
| PP probe size | 4 common base IDs x 7 groups at each existing post-warm-up adaptation boundary |
| PP method changes | sampler return-estimation stream only; no actor/critic/PPO/reward/environment change |
| Evaluation | new development-only tape, fixed before training; 100 episodes/condition |

Seeds `3401--3403` passed a provenance scan for `seed3401`, `seed3402`,
`seed3403`, and JSON training-seed fields outside generated results and
archives.  They are not historical, formal, independent, S1/S2/R1, D5, or
Mainline-A seeds.

## Gate, frozen before results

Let `G_m,s = J_pert_mean(m,s) - J_pert_mean(UTR,s)`.  This pilot uses the
pre-existing measurement-noise margin `epsilon_J = 7.874919837916801`; it is
not to be recalibrated from P3 results.

`PP_PILOT_EARLY_GO` requires all of the following:

1. Mean PP-DRTP `J_pert_mean` is no more than `epsilon_J` below Original DRTP.
2. PP-DRTP improves the worst paired gain relative to Original DRTP by more
   than `epsilon_J`, without increasing catastrophic-seed count.
3. Range, sample SD and MAD of paired gain all decrease relative to Original
   DRTP.
4. Every Original-DRTP upper-tail seed (`G_drtp > epsilon_J`) retains
   `J_pert_mean` within `epsilon_J` under PP-DRTP.
5. Failure collision and timeout safety follow the inherited pooled `0.05`,
   seed-condition `0.10`, and zero-constraint-violation limits.

Any failure is `PP_PILOT_NO_GO`; it does not authorize probe-count tuning,
another PP variant, continuation, or a replacement seed.  The only permitted
output after the gate is a report for human review.

## Prohibited actions

No early stop, checkpoint promotion, performance rerun, probe-size sweep,
PPO change, sampler-parameter change, 1M/3M continuation, or confirmatory
training is authorized.
