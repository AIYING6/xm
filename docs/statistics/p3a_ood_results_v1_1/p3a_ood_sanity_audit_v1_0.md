# P3-A.3b Final Sanity Audit Memo (2026-08-08)

- raw input: `p3a_ood_raw_results.csv` (locked at `p3a-ood-raw-results-lock-v1.0`,
  SHA256 8a8d1306d786ae77..., 8400 rows) — NOT modified by this audit.
- audit: fully independent recomputation (separate KM implementation in
  `_tmp_p3a_sanity.py` / `_tmp_p3a_sanity_boot.py`), no reuse of
  `analyze_p3a_ood` functions.

## 1. Primary results — fully confirmed (independent recomputation)

21 seed x cell pairs, seed aggregates, and hierarchical paired bootstrap all
match the reported table EXACTLY:

| seed | C1 | C2 | G1 | G2 | J1 | M1 | M2 | Delta^OOD_s |
|---|---|---|---|---|---|---|---|---|
| s0 | -3.17 | -3.17 | -10.60 | 0 | 0 | 0 | 0 | **-2.420** |
| s1 | +4.52 | +4.52 | +1.76 | 0 | 0 | 0 | 0 | **+1.543** |
| s2 | +28.82 | +28.82 | +2.36 | 0 | 0 | 0 | 0 | **+8.571** |

- mean Delta^OOD = **+2.565**, sample SD = **5.567** (arithmetic, deviation < 1e-3).
- Hierarchical paired bootstrap (B=10000, RNG=20260807): mean **+2.5320**,
  95% CI **[-2.3624, +8.4348]**, P(Delta<0) = **0.1749** — identical to report.

## 2. Bug found and fixed (secondary per-cell table only)

Symptom (reported by user): "C1/C2 Full RMST80=80, MAPPO RMST80=80" while
Delta^80(C1/C2) = +10.06 -> internal contradiction.

Root cause: `analyze_p3a_ood.cell_stats` fed `km_rmst` two DISJOINT arrays
(recovered event times, censored times) instead of per-episode PAIRED arrays.
`km_rmst` zips them as if per-episode, mis-pairing -> all events treated as
censored -> RMST80/RMST220 spuriously saturated at the ceiling (80/220).

- Primary path (`block_times`) was always correct (per-episode paired), so
  Delta table / aggregates / bootstrap were NOT affected.
- Fix: `cell_stats` now builds `ev_all`/`ce_all` per-episode paired arrays.
- Regression test added: `test_cell_stats_paired_clock_not_disjoint`.
- After fix: C1 Full RMST80=32.7 (was 80.0), MAPPO=22.6; G1 Full 32.7 vs
  MAPPO 34.9 — all internally consistent with the Delta table.
- Primary numbers unchanged after the fix (same seed deltas, CI, P-value).

## 3. M1/M2/J1 ceiling saturation confirmed (valid science, not "comparable")

- M1/M2/J1: n_recovered = 0 for essentially all method x seed (only exception
  s1 M2 MAPPO: 14 recoveries all at t in [105,126] > 80).
- n_event_before_80 = 0 -> RMST80 = 80.0 = TRUE UPPER-CEILING saturation.
- Interpretation (for paper): the OOD maneuver shift is severe enough that
  post-failure chain recovery fails for ALL compared methods; NOT "Full ~ MAPPO".
- M1/M2/J1 remain pre-registered OOD cells and stay in the 7-cell equal-weight
  primary estimand; they are NOT dropped as "non-informative".

## 4. Verdict

> SANITY AUDIT PASS.
> Primary statistics are fully reproduced independently; the only defect found
> was in the secondary per-cell table (paired-clock fix applied, regression
> test added). Gate C decision is unchanged and stands.
