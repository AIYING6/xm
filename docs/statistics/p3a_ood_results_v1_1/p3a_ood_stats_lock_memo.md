# P3-A Statistical Results Lock Memo (2026-08-08)

- status: **FROZEN** (tag: `p3a-ood-stats-lock-v1.0`)
- analysis commit: `1d5843c` (km_rmst fix + cell_stats paired-clock fix + sanity audit)
- frozen after: independent sanity audit PASS; no further re-tuning of tau / cells /
  comparator / training / remedial experiments is permitted.

## 1. Frozen provenance

- raw input = `p3a-ood-raw-results-lock-v1.0` (`ad698ea`, 8400 rows,
  SHA256 8a8d1306d786ae77...)
- implementation = `p3a-ood-eval-impl-v1.1.3`, protocol = `p3a-ood-protocol-v1.1`,
  preflight lock = `p3a-ood-preflight-lock-v1.1`

## 2. Primary estimand (frozen)

- **7-cell equal-weight Full − MAPPO RMST80 aggregate** over G1 G2 M1 M2 C1 C2 J1:
  \[
  \Delta_s^{OOD} = \frac{1}{7}\sum_c (RMST80_{Full,s,c} - RMST80_{MAPPO,s,c}),\qquad
  \bar\Delta^{OOD} = \frac{1}{3}\sum_s \Delta_s^{OOD}
  \]
- RMST80/RMST220 via KM survival with P1-frozen recovery clock
  (T_event = stable_window_start − failure_start; T_censor = steps − failure_start).

## 3. Uncertainty (frozen)

- **Hierarchical paired bootstrap**: B = 10,000, RNG = 20260807; resample seeds,
  then matched episode-index resampling within seed × cell.

## 4. Frozen result

| seed | Delta^OOD_s |
|---|---|
| s0 | −2.420 |
| s1 | +1.543 |
| s2 | +8.571 |
| mean | +2.565 ± 5.567 |

- bootstrap: mean +2.532, 95% CI [−2.362, +8.435], P(Delta<0) = 0.1749
- family effects: Geometry −1.08, Communication +10.06, Maneuver 0.00 (ceiling
  saturation), Joint 0.00 (ceiling saturation)

## 5. Final verdict

> **GATE C: the early-recovery advantage is distribution-dependent.**

## 6. Sanity conclusion (frozen into this lock)

> Primary statistics were independently reproduced and were unaffected by the
> secondary `cell_stats` bug. The bug affected only per-cell RMST reporting and
> was corrected before the statistics lock.

- Independent recomputation matched the primary table exactly (21 pairs,
  aggregates, bootstrap CI, P(Delta<0)).
- M1/M2/J1: RMST80 = 80 is TRUE upper-ceiling saturation (recovery events ~0;
  sole exception s1 M2 MAPPO has 14 recoveries all at t>80) — a genuine
  scientific finding ("OOD maneuver shift overwhelms all compared methods"),
  NOT "Full ~ MAPPO". These cells remain in the 7-cell estimand.

## 7. Paper conclusion (to be written accordingly)

> EA-RG provides reproducible early post-failure recovery gains under the
> nominal held-out distribution, but this advantage is distribution-dependent
> under zero-shot OOD shifts. Geometry shifts preserve part of the benefit,
> communication-topology shifts can reverse the comparison, and maneuver shifts
> can overwhelm all evaluated methods.
