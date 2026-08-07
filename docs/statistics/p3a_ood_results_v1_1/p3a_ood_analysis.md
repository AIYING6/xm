# P3-A OOD Statistical Analysis (P3-A.3b)

- raw input: `docs\statistics\p3a_ood_results_v1_1\p3a_ood_raw_results.csv`
- rows: 8400
- B=10000, RNG=20260807

## Primary: Full vs MAPPO, RMST80, 7-cell equal-weight aggregate

| seed | Delta^OOD_s |
|---|---|
| s0 | -2.420 |
| s1 | +1.543 |
| s2 | +8.571 |
| **mean** | **+2.565 ± 5.567** |

hierarchical paired bootstrap (B=10000): mean +2.532 (SD 2.659), 95% CI [-2.362, +8.435], P(Delta<0) = 0.1749

Gate: **C** — the early-recovery advantage is distribution-dependent.

## Seed x cell Delta^80 (Full - MAPPO, RMST80)

| seed | C1 | C2 | G1 | G2 | J1 | M1 | M2 |
|---|---|---|---|---|---|---|---|
| s0 | -3.17 | -3.17 | -10.60 | +0.00 | +0.00 | +0.00 | +0.00 |
| s1 | +4.52 | +4.52 | +1.76 | +0.00 | +0.00 | +0.00 | +0.00 |
| s2 | +28.82 | +28.82 | +2.36 | +0.00 | +0.00 | +0.00 | +0.00 |

## Family effects (Full - MAPPO, RMST80, seed-averaged)

- Geometry (G1+G2): -1.080
- Maneuver (M1+M2): +0.000
- Communication (C1+C2): +10.057
- Joint (J1): +0.000

## Per-cell secondary (seed-averaged, per method)

| cell | method | RMST80 | RMST220 | P_rec | E[T_rec|rec] (cond) | collision |
|---|---|---|---|---|---|---|
| C1 | full_ea_rg | 32.7 | 65.3 | 0.770 | 19.5 | 0.003 |
| C1 | mappo | 22.6 | 30.1 | 0.960 | 22.2 | 0.000 |
| C1 | happo | 22.6 | 28.2 | 0.967 | 21.8 | 0.003 |
| C1 | param_matched_single | 20.4 | 24.6 | 0.983 | 21.3 | 0.003 |
| C2 | full_ea_rg | 32.7 | 64.9 | 0.773 | 19.8 | 0.003 |
| C2 | mappo | 22.6 | 30.1 | 0.960 | 22.2 | 0.000 |
| C2 | happo | 22.6 | 28.2 | 0.967 | 21.8 | 0.003 |
| C2 | param_matched_single | 20.4 | 24.6 | 0.983 | 21.3 | 0.000 |
| G1 | full_ea_rg | 32.7 | 57.9 | 0.827 | 23.8 | 0.003 |
| G1 | mappo | 34.9 | 58.8 | 0.843 | 28.9 | 0.000 |
| G1 | happo | 26.2 | 31.8 | 0.963 | 24.7 | 0.000 |
| G1 | param_matched_single | 26.4 | 34.3 | 0.957 | 26.2 | 0.003 |
| G2 | full_ea_rg | 80.0 | 219.5 | 0.047 | 212.2 | 0.000 |
| G2 | mappo | 80.0 | 220.0 | 0.000 | nan | 0.000 |
| G2 | happo | 80.0 | 220.0 | 0.000 | nan | 0.000 |
| G2 | param_matched_single | 80.0 | 218.3 | 0.103 | 200.0 | 0.000 |
| J1 | full_ea_rg | 80.0 | 220.0 | 0.000 | nan | 0.007 |
| J1 | mappo | 80.0 | 220.0 | 0.000 | nan | 0.000 |
| J1 | happo | 80.0 | 220.0 | 0.000 | nan | 0.000 |
| J1 | param_matched_single | 80.0 | 220.0 | 0.000 | nan | 0.007 |
| M1 | full_ea_rg | 80.0 | 220.0 | 0.000 | nan | 0.000 |
| M1 | mappo | 80.0 | 220.0 | 0.000 | nan | 0.000 |
| M1 | happo | 80.0 | 220.0 | 0.000 | nan | 0.000 |
| M1 | param_matched_single | 80.0 | 220.0 | 0.000 | nan | 0.007 |
| M2 | full_ea_rg | 80.0 | 220.0 | 0.000 | nan | 0.000 |
| M2 | mappo | 80.0 | 215.0 | 0.047 | 113.4 | 0.000 |
| M2 | happo | 80.0 | 220.0 | 0.000 | nan | 0.000 |
| M2 | param_matched_single | 80.0 | 220.0 | 0.000 | nan | 0.000 |

## Notes

- HAPPO and Wider-SG are strong-reference comparators, not primary.
- Collision is reported separately and does not enter the primary headline.
- No re-tuning of tau / cells / checkpoints / family weights / recovery definition is permitted after this first output.
