# Strict-Sensing Seed-Aware Statistics

This report uses matched strict-sensing relay-failure test episodes from the formal development runs.
Uncertainty is estimated with a hierarchical bootstrap: training seeds are resampled first, then matched episodes are resampled within each selected training seed.

- Baseline: `single`
- Proposed: `multi_relation`
- Independent training seeds: 5
- Matched test episodes: 500

## Bootstrap Summary

| Metric | Baseline | Proposed | Delta | 95% CI for delta |
|---|---:|---:|---:|---:|
| Task success | 46.6% | 88.2% | +41.6 pp | [+4.4, +78.6] pp |
| Post-failure chain recovered | 46.6% | 88.2% | +41.6 pp | [+4.4, +78.6] pp |
| Timeout | 50.0% | 11.6% | -38.4 pp | [-74.8, -2.0] pp |
| Restricted mean recovery steps | 128.22 | 50.28 | -77.94 | [-158.63, -0.47] |
| Tracking during failure | 42.7% | 65.9% | +23.3 pp | [+2.4, +44.9] pp |
| Connectivity during failure | 15.9% | 21.9% | +6.0 pp | [+2.3, +10.3] pp |
| Chain closure during failure | 2.1% | 3.9% | +1.8 pp | [+0.1, +3.6] pp |
| Episode length | 153.22 | 75.28 | -77.94 | [-158.63, -0.47] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| single | 233 | 20.92 |
| multi_relation | 441 | 26.04 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 74.0% | 57.0% | -17.0 pp |
| 0 | Post-failure chain recovered | 74.0% | 57.0% | -17.0 pp |
| 0 | Timeout | 26.0% | 43.0% | +17.0 pp |
| 0 | Restricted mean recovery steps | 76.60 | 112.73 | +36.13 |
| 0 | Tracking during failure | 66.8% | 57.4% | -9.4 pp |
| 0 | Connectivity during failure | 15.9% | 19.6% | +3.7 pp |
| 0 | Chain closure during failure | 3.4% | 2.7% | -0.7 pp |
| 0 | Episode length | 101.60 | 137.73 | +36.13 |
| 1 | Task success | 14.0% | 91.0% | +77.0 pp |
| 1 | Post-failure chain recovered | 14.0% | 91.0% | +77.0 pp |
| 1 | Timeout | 78.0% | 8.0% | -70.0 pp |
| 1 | Restricted mean recovery steps | 188.80 | 38.23 | -150.57 |
| 1 | Tracking during failure | 33.0% | 75.7% | +42.8 pp |
| 1 | Connectivity during failure | 14.0% | 22.7% | +8.6 pp |
| 1 | Chain closure during failure | 0.6% | 4.1% | +3.5 pp |
| 1 | Episode length | 213.80 | 63.23 | -150.57 |
| 2 | Task success | 0.0% | 100.0% | +100.0 pp |
| 2 | Post-failure chain recovered | 0.0% | 100.0% | +100.0 pp |
| 2 | Timeout | 98.0% | 0.0% | -98.0 pp |
| 2 | Restricted mean recovery steps | 231.31 | 20.36 | -210.95 |
| 2 | Tracking during failure | 21.0% | 79.7% | +58.7 pp |
| 2 | Connectivity during failure | 9.9% | 23.4% | +13.5 pp |
| 2 | Chain closure during failure | 0.0% | 4.7% | +4.7 pp |
| 2 | Episode length | 256.31 | 45.36 | -210.95 |
| 3 | Task success | 54.0% | 93.0% | +39.0 pp |
| 3 | Post-failure chain recovered | 54.0% | 93.0% | +39.0 pp |
| 3 | Timeout | 44.0% | 7.0% | -37.0 pp |
| 3 | Restricted mean recovery steps | 115.34 | 59.45 | -55.89 |
| 3 | Tracking during failure | 36.3% | 54.6% | +18.3 pp |
| 3 | Connectivity during failure | 16.9% | 20.4% | +3.5 pp |
| 3 | Chain closure during failure | 2.5% | 3.4% | +0.9 pp |
| 3 | Episode length | 140.34 | 84.45 | -55.89 |
| 4 | Task success | 91.0% | 100.0% | +9.0 pp |
| 4 | Post-failure chain recovered | 91.0% | 100.0% | +9.0 pp |
| 4 | Timeout | 4.0% | 0.0% | -4.0 pp |
| 4 | Restricted mean recovery steps | 29.05 | 20.61 | -8.44 |
| 4 | Tracking during failure | 56.3% | 62.3% | +6.1 pp |
| 4 | Connectivity during failure | 22.8% | 23.4% | +0.6 pp |
| 4 | Chain closure during failure | 4.2% | 4.6% | +0.5 pp |
| 4 | Episode length | 54.05 | 45.61 | -8.44 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
