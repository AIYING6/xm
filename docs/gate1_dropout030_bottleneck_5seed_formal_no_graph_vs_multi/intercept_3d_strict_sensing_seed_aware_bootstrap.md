# Strict-Sensing Seed-Aware Statistics

This report uses matched strict-sensing relay-failure test episodes from the formal development runs.
Uncertainty is estimated with a hierarchical bootstrap: training seeds are resampled first, then matched episodes are resampled within each selected training seed.

- Baseline: `no_graph`
- Proposed: `multi_relation`
- Independent training seeds: 5
- Matched test episodes: 500

## Bootstrap Summary

| Metric | Baseline | Proposed | Delta | 95% CI for delta |
|---|---:|---:|---:|---:|
| Task success | 34.2% | 96.2% | +62.0 pp | [+27.8, +95.2] pp |
| Post-failure chain recovered | 34.2% | 96.2% | +62.0 pp | [+27.8, +95.2] pp |
| Timeout | 64.0% | 3.8% | -60.2 pp | [-93.0, -27.2] pp |
| Restricted mean recovery steps | 143.69 | 23.45 | -120.24 | [-190.78, -50.61] |
| Tracking during failure | 23.4% | 80.9% | +57.4 pp | [+27.6, +86.9] pp |
| Connectivity during failure | 14.6% | 30.0% | +15.4 pp | [+6.0, +25.1] pp |
| Chain closure during failure | 5.5% | 13.8% | +8.4 pp | [+3.3, +13.6] pp |
| Episode length | 183.69 | 63.45 | -120.24 | [-190.78, -50.61] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| no_graph | 171 | 5.53 |
| multi_relation | 481 | 15.68 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 0.0% | 98.0% | +98.0 pp |
| 0 | Post-failure chain recovered | 0.0% | 98.0% | +98.0 pp |
| 0 | Timeout | 100.0% | 2.0% | -98.0 pp |
| 0 | Restricted mean recovery steps | 220.00 | 10.35 | -209.65 |
| 0 | Tracking during failure | 0.1% | 98.3% | +98.3 pp |
| 0 | Connectivity during failure | 4.5% | 32.5% | +28.0 pp |
| 0 | Chain closure during failure | 0.0% | 14.6% | +14.6 pp |
| 0 | Episode length | 260.00 | 50.35 | -209.65 |
| 1 | Task success | 86.0% | 95.0% | +9.0 pp |
| 1 | Post-failure chain recovered | 86.0% | 95.0% | +9.0 pp |
| 1 | Timeout | 14.0% | 5.0% | -9.0 pp |
| 1 | Restricted mean recovery steps | 35.50 | 16.59 | -18.91 |
| 1 | Tracking during failure | 54.7% | 95.6% | +40.9 pp |
| 1 | Connectivity during failure | 29.4% | 31.6% | +2.2 pp |
| 1 | Chain closure during failure | 13.8% | 14.5% | +0.6 pp |
| 1 | Episode length | 75.50 | 56.59 | -18.91 |
| 2 | Task success | 7.0% | 100.0% | +93.0 pp |
| 2 | Post-failure chain recovered | 7.0% | 100.0% | +93.0 pp |
| 2 | Timeout | 89.0% | 0.0% | -89.0 pp |
| 2 | Restricted mean recovery steps | 200.35 | 5.46 | -194.89 |
| 2 | Tracking during failure | 3.2% | 100.0% | +96.8 pp |
| 2 | Connectivity during failure | 6.4% | 32.4% | +25.9 pp |
| 2 | Chain closure during failure | 0.9% | 16.0% | +15.1 pp |
| 2 | Episode length | 240.35 | 45.46 | -194.89 |
| 3 | Task success | 0.0% | 92.0% | +92.0 pp |
| 3 | Post-failure chain recovered | 0.0% | 92.0% | +92.0 pp |
| 3 | Timeout | 95.0% | 8.0% | -87.0 pp |
| 3 | Restricted mean recovery steps | 209.89 | 67.82 | -142.07 |
| 3 | Tracking during failure | 6.8% | 50.2% | +43.4 pp |
| 3 | Connectivity during failure | 5.4% | 22.9% | +17.5 pp |
| 3 | Chain closure during failure | 0.0% | 8.9% | +8.9 pp |
| 3 | Episode length | 249.89 | 107.82 | -142.07 |
| 4 | Task success | 78.0% | 96.0% | +18.0 pp |
| 4 | Post-failure chain recovered | 78.0% | 96.0% | +18.0 pp |
| 4 | Timeout | 22.0% | 4.0% | -18.0 pp |
| 4 | Restricted mean recovery steps | 52.69 | 17.01 | -35.68 |
| 4 | Tracking during failure | 52.5% | 60.4% | +7.8 pp |
| 4 | Connectivity during failure | 27.1% | 30.6% | +3.5 pp |
| 4 | Chain closure during failure | 12.5% | 15.2% | +2.8 pp |
| 4 | Episode length | 92.69 | 57.01 | -35.68 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
