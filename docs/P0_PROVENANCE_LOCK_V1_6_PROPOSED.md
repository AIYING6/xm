# P0 Provenance Lock — v1.6 (survival locked)

- locked: 2026-08-07 (after P1 Decision Gate)
- tag: `paper-v1.6-survival-locked`
- supersedes: `paper-v1.5-pre-survival` (tag on the pre-survival HEAD)

## Provenance fields

| field | value |
|---|---|
| MANUSCRIPT_HEAD_SHA | (post-P1 commit; updated at tag time) |
| MANUSCRIPT_HEAD_TAG | `paper-v1.6-survival-locked` |
| SURVIVAL_PROTOCOL_VERSION | v1.1 (frozen tag `survival-protocol-v1.1`; local SHA `b2500d76...`; sandbox SHA `453d1011...` — same rules) |
| SURVIVAL_RESULTS | `docs/statistics/survival_results_v1_1/` (audit 11/11, RMST seedwise+summary, sensitivity, bootstrap, KM) |
| DECISION_GATE | NO CLEAN A/B/C → conservative comparator/time-scale claim (see P1B_DECISION_MEMO_V1_1) |
| RECOVERY_HEADLINE | early post-failure recovery advantage over MAPPO under matched exposure; full-horizon competitive with HAPPO / wider single-graph |
| RMST(220)_FULL | 14.47 ± 3.10 (n=3 seeds) |
| RMST(220)_MAPPO | 20.39 ± 7.72 (Δ mean −5.93; τ≤100 Δ_s all <0, bootstrap CI excludes 0) |
| RMST(220)_HAPPO | 14.14 ± 2.94 (Δ mean +0.32; mixed seeds) |
| RMST(220)_WIDER_SG | 16.49 ± 8.64 (Δ mean −2.03; seed0-driven) |
| RPG_VERDICT | limited independent benefit under primary RMST(220) (Full 14.47 vs w/o-RPG 13.63) |
| GATE_PRIOR_VERDICT | conditional contribution (optimization stability); removal 14.47→48.48, seed-mixed |
| TASK_SUPPORT_VERDICT | empirically supported task-dependent relation; removal 14.47→29.57, seed-mixed |

## Standing rules (unchanged from v1.5 lock, plus)

- All previous rules carry forward (no retraining; seed = statistical unit; single numeric
  source `canonical_results_v1_5.csv`).
- New: P2 paper must (a) drop conditional-time headline percentages vs HAPPO/wider SG;
  (b) rename t_rec to conditional mean recovery time among recovered failure-exposed
  episodes; (c) use KM + RMST(220) + early-window sensitivity as RQ2 main evidence;
  (d) treat Delayed/Late as terminal-reliability / landmark sensitivity only;
  (e) acknowledge full-horizon HAPPO and w/o-RPG competitiveness in Discussion.
