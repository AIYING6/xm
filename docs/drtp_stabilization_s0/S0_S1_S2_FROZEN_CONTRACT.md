# DRTP two-shot stabilization — S0 frozen contract

Status: `S0_NUMERICAL_FREEZE_COMPLETE — TRAINING_NOT_AUTHORIZED`

## Objective and boundary

This is an engineering reliability screen, not a claim that a diagnosed DRTP
module caused historical failures. The sole objective is **Advantage Retention
+ Downside Protection + Seed Reliability**: retain original DRTP's robust
upside while improving its lower tail without a safety cost.

The historical H1/H2/H3 `NO-GO` conclusions remain unchanged. S0 does not
rewrite them or authorize a causal mechanism claim.

## S0 numerical freeze

The label-free original-DRTP sampler audit in
`S0_DELTA_FREEZE_REPORT.md` includes every accessible valid original-DRTP
sampler trajectory from the historical 1901--1902/2001--2003 records, formal
2301--2305 archive, B3 2701--2703 archive, and H2 2801--2805 archive. It
excludes UTR, R-DRTP, EGTR, SNR, technical smoke runs, and the permanently
technical-invalid 2601--2603 asset. No performance label was used to select a
constant.

| Frozen item | Value / rule |
|---|---|
| S1 method | `DRTP-TR` |
| S1 TR bound | `delta = 0.02513300038143937` |
| delta selection | pooled P90 of final post-projection `||q_(u+1)-q_u||_1`; `n=12,781` valid movements |
| S2 method | `Conservative-DRTP` only: DRTP-TR plus fixed 20% uniform target anchor |
| S2 anchor | uniform mass `0.20`, adaptive mass `0.80` |
| primary robust endpoint | `J_pert_mean = mean(J_F0, J_timing, J_duration, J_compound)` |
| epsilon_J | `7.874919837916801` J units |
| epsilon rule | P90 absolute paired difference of the same checkpoint across two frozen evaluation tapes (`100` pairwise differences across `10` checkpoints) |
| practical downside margin | strictly greater than `7.874919837916801` J units |
| catastrophic rule | inherited F0/OOD-worst/safety-associated collapse rule from the formal UTR--DRTP contract |

`epsilon_J` quantifies observed evaluation-tape variation. It is not a license
to pool distinct training cohorts or to erase a real training difference.

## Frozen methods and order

All S1 arms retain the actor/critic, parameter count, PPO, reward, environment,
topology semantics, observation/information boundary, groups, nominal 0.50
mass, q floor/cap, EMA, difficulty, temperature, smoothing and adaptation
interval of original DRTP.

For DRTP-TR the only method change is:

`adaptive target -> bounded-simplex projection -> final L1 trust region`.

For Conservative-DRTP, only if S2 is authorized after S1 NO-GO:

`adaptive target -> bounded-simplex projection -> 0.80 target + 0.20 uniform target -> final L1 trust region`.

The anchor is deliberately applied **before** the final TR so the final output
retains the hard L1 guarantee. A convex combination of feasible simplex points
already has valid mass and floor/cap; no projection is applied after TR.

No delta/anchor sweep, confidence gate, warm-up change, hysteresis, PPO change,
network change, auxiliary loss, third stabilization version, or result-driven
constant adjustment is permitted.

## S1 design

| Item | Frozen value |
|---|---|
| arms | `utr_sg`, original `drtp_sg`, `drtp_tr_sg` |
| paired development seeds | `2901, 2902, 2903` |
| first budget | exactly 1,953 updates = 499,968 environment steps per run |
| milestones | 976 / 1,953 updates (0.25M / 0.5M) |
| independent tape | `configs/drtp_stabilization_s1_development_tape.json` |
| tape SHA256 | `2ff360d6e240f6f9e3b7a5b74dc56db54da601e391bc259a5a51719d83fa7461` |
| tape protocol | five conditions × same 100 base IDs: nominal/F0/T28/D120/C28-120 |
| checkpoint rule | frozen milestones and final only; no best-checkpoint promotion |
| run discipline | no early stop, seed replacement, rerun based on performance, or extension without a separate gate authorization |

The tape is development-only and may not become a confirmatory tape.

## Definitions for every gate

For a method `m` and training seed `s`, let
`G_m,s = J_pert_mean(m,s) - J_pert_mean(UTR,s)`.

- **Advantage retention:** `mean_s J_pert_mean(TR,s) >= mean_s J_pert_mean(DRTP,s) - epsilon_J`.
- **Downside protection:** `min_s G_TR,s - min_s G_DRTP,s > practical_margin` and the inherited catastrophic count for TR is no greater than original DRTP.
- **Seed reliability:** range, sample SD, and MAD of `G_TR,s` must each be lower than their original-DRTP counterpart; all three are descriptive with `n=3`, but all must move in the prescribed direction.
- **Safety:** mean failure collision and timeout differences of TR minus UTR must each be `<=0.05`; no paired seed-condition increase may exceed `0.10`; constraint violations must remain zero. These are inherited safety tolerances, not newly tuned thresholds.
- **Upper-tail retention:** among seeds with `G_DRTP,s > epsilon_J`, every corresponding `J_pert_mean(TR,s)-J_pert_mean(DRTP,s)` must be `>= -epsilon_J`. If there is no such original-DRTP seed, upper-tail retention is unassessable and an S1 GO cannot be declared.

## 0.5M and 1M decisions

At 0.5M, `S1_EARLY_GO` requires all five definitions above. `S1_NO_GO`
applies if advantage retention fails, the TR worst paired gain is worse than
original DRTP, the inherited catastrophic count increases, any safety rule
fails, or the upper tail fails. `S1_INCONCLUSIVE` is allowed only when there is
no NO-GO and no EARLY_GO; it continues all nine *unchanged* trajectories to
the separately frozen 1M ceiling only after author authorization.

At 1M, a continuation to 3M requires all five definitions. Otherwise S1 is
`NO-GO`. No data may alter `delta`, the anchor, a practical margin, or a gate.

Only `S1_NO_GO` can make the pre-frozen S2 candidate eligible; it does not
start S2 automatically. S2 reuses S1 UTR/original-DRTP trajectories and adds
only Conservative-DRTP on the same seeds/tape/budget after a separate human
authorization. S2 failure permanently closes the stabilization line.

## Technical acceptance

`S0_TECHNICAL_AUDIT.json` must remain PASS: exact original recovery below the
bound, activation on steep targets, final L1/mass/floor/cap checks, deterministic
pre-adaptation RNG selection, mid-window save/resume, candidate telemetry
fields, and frozen constants. This audit creates no environment or training
trajectory.

## S0 terminal condition

S0 ends at this contract. It starts no training, evaluation rerun, cloud job,
or parameter search. The only valid next status is
`S0_READY_FOR_S1_AUTHORIZATION` after all listed source and technical checks
remain valid; otherwise it is `S0_NOT_READY`.
