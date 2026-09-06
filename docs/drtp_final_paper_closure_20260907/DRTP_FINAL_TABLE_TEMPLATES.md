# DRTP final table templates

Fill cells only from the corresponding frozen aggregation artifacts. Report A and B separately in every primary table.

## Table 1. Main 3-UAV fixed-endpoint robustness

| Cohort | Method | Perturbed return, mean ± SD | Median | Worst seed | Seeds with positive paired delta vs UTR | Nominal return | Timeout | Collision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A | UTR | 177.02 ± 64.53 | [import] | 79.75 | — | [import] | [import] | [import] |
| A | Original DRTP | 216.66 ± 23.48 | [import] | 191.49 | [import] | [import] | [import] | [import] |
| B | UTR | 187.18 ± [import] | [import] | [import] | — | [import] | [import] | [import] |
| B | Original DRTP | 210.34 ± 30.54 | [import] | 172.03 | [import] | [import] | [import] | [import] |

*Caption boundary:* each row contains five independently trained policies. No pooled inferential test is reported.

## Table 2. Frozen held-out/OOD robustness

| Cohort | Shift family | Method | Return | Paired delta DRTP − UTR | Worst-seed delta | Timeout | Collision |
|---|---|---|---:|---:|---:|---:|---:|
| A | Structural held-out | UTR | [import] | — | — | [import] | [import] |
| A | Structural held-out | Original DRTP | [import] | +22.77 mean | +32.48 | [import] | [import] |
| B | Structural held-out | UTR | [import] | — | — | [import] | [import] |
| B | Structural held-out | Original DRTP | [import] | +11.96 mean | +20.03 | [import] | [import] |
| A/B | Parameter shift | Original DRTP vs UTR | [import] | A +51.71; B +17.48 | [import] | [import] | [import] |

## Table 3. External matched PLR-style comparator

| Cohort | Method | Perturbed return | Median | Worst seed | Nominal return | Timeout | Collision | Status |
|---|---|---:|---:|---:|---:|---:|---:|---|
| A | UTR | [import] | [import] | [import] | [import] | [import] | [import] | pending |
| A | PLR-style | [import] | [import] | [import] | [import] | [import] | [import] | pending |
| A | Original DRTP | [import] | [import] | [import] | [import] | [import] | [import] | pending |
| B | UTR / PLR-style / Original DRTP | [import] | [import] | [import] | [import] | [import] | [import] | pending |

## Table 4. Cross-scale 6-UAV result

| Cohort / seed set | Method | Perturbed return | Success | Timeout | Collision | Paired delta | Status |
|---|---|---:|---:|---:|---:|---:|---|
| Frozen 6-UAV protocol | UTR | [import] | [import] | [import] | [import] | — | pending |
| Frozen 6-UAV protocol | Original DRTP | [import] | [import] | [import] | [import] | [import] | pending |

## Table 5. Computational overhead

| Configuration | Parameters | Wall-clock / 1M steps | Peak GPU memory | Sampler update time | Relative wall-clock to UTR |
|---|---:|---:|---:|---:|---:|
| UTR | [measure] | [measure] | [measure] | fixed reset selection | 1.00× |
| Original DRTP | [same policy] | [measure] | [measure] | [measure] | [measure] |
| PLR-style | [measure] | [measure] | [measure] | [measure] | [measure] |

