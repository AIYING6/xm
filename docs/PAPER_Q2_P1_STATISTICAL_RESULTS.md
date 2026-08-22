# PAPER-Q2-P1 Statistical Results

The machine-readable sources are `artifacts/paper_q2_p1/main_table.csv`, `seed_level_results.csv`, and `statistical_summary.json`. The independent unit is the training seed. Development 3M and held-out 10M are separate contract strata.

## Historical paired DRTP − UTR summary

| Metric | Wins | Mean | Median | SD | IQR | MAD | Worst |
|---|---:|---:|---:|---:|---:|---:|---:|
| Nominal | 4/5 | +46.231 | +40.794 | 63.390 | 43.742 | 33.886 | −16.254 |
| F0 | 3/5 | +26.404 | +29.804 | 99.467 | 125.952 | 51.491 | −113.951 |
| OOD mean | 3/5 | +34.218 | +26.305 | 88.629 | 112.985 | 80.895 | −88.126 |
| OOD worst | 4/5 | +31.479 | +23.688 | 87.658 | 85.074 | 16.136 | −97.100 |

The exact machine-readable summary is authoritative. These dispersion values are deterministic seed-level descriptive statistics over the five historical paired deltas; they are not population estimates.

## Absolute pooled results

Development 3M: UTR `147.157/127.929/120.607/103.149`; DRTP `171.007/183.880/183.464/172.241`, in the order nominal/F0/OOD mean/OOD worst. Failure collision was `0.0136` versus `0.0014`, timeout `0.8086` versus `0.5600`, and constraint violation was zero for both.

Held-out 10M: UTR `160.341/162.187/155.021/138.354`; DRTP `221.493/168.893/170.147/144.758`. Held-out DRTP timeout was mixed and collision was higher in all three seeds; the held-out contract therefore remains FAIL.

## Interpretation

The mean/median gains are publication-relevant descriptive effects, not evidence of seed-stable superiority. Seed1902 and held-out seed2002 remain in the main reliability narrative.
