# P3-A.3b First Statistical Output — INVALIDATION MEMO (2026-08-08)

- status: **INVALID — code bug found in km_rmst; first output NOT usable.**
- first output kept for provenance: `p3a_ood_analysis.md` (never edited after
  this memo; superseded by the corrected re-run).
- analysis code at the time: `scripts/analyze_p3a_ood.py` (commit `0167218`).

## Bug

`km_rmst` double-counted the [0, tau] area when the first ordered time point
exceeded tau (the `break` path left `t_prev` stale, then the trailing
`if t_prev < tau: area += surv*(tau-t_prev)` re-added the full segment).

Evidence (impossible values, RMST80 must be <= 80, RMST220 <= 220):

| cell | method | RMST80 (buggy) | RMST220 (buggy) |
|---|---|---|---|
| C1 | full_ea_rg | 100.0 | 220.0 |
| G1 | full_ea_rg | 98.7 | 285.3 |
| G2 | full_ea_rg | 160.0 | 223.0 |

## Consequence

- The Gate C verdict produced by the buggy run is void (P(Delta<0)=0.30,
  mean +3.7, family Maneuver +0.000) — all derived from corrupted RMST values.
- No scientific conclusion may be drawn from `p3a_ood_analysis.md`.

## Fix

- Correct `km_rmst` so that any time point at/after tau caps the segment at tau
  and terminates integration (no stale-t_prev double count).
- Add regression tests: single event at t>tau -> RMST80 = tau; censored time
  > tau -> RMST80 = tau; mixed event/censor sanity <= tau.
- Re-run on the SAME locked raw input (`p3a-ood-raw-results-lock-v1.0`,
  SHA 8a8d1306d786ae77, 8400 rows). Raw data is NOT affected by this bug.
