# Strict-Sensing Seed-Aware Statistics

This report uses matched strict-sensing relay-failure test episodes from the formal development runs.
Uncertainty is estimated with a hierarchical bootstrap: training seeds are resampled first, then matched episodes are resampled within each selected training seed.

- Baseline: `single`
- Proposed: `multi_relation`
- Independent training seeds: 5
- Matched test episodes: 50

## Bootstrap Summary

| Metric | Baseline | Proposed | Delta | 95% CI for delta |
|---|---:|---:|---:|---:|
| Task success | 46.0% | 94.0% | +48.0 pp | [+18.0, +82.0] pp |
| Post-failure chain recovered | 46.0% | 94.0% | +48.0 pp | [+18.0, +82.0] pp |
| Timeout | 52.0% | 6.0% | -46.0 pp | [-80.0, -16.0] pp |
| Restricted mean recovery steps | 117.28 | 27.32 | -89.96 | [-164.39, -27.24] |
| Tracking during failure | 44.7% | 81.7% | +37.0 pp | [+11.3, +67.0] pp |
| Connectivity during failure | 21.5% | 31.2% | +9.7 pp | [+0.9, +19.8] pp |
| Chain closure during failure | 7.4% | 14.4% | +7.0 pp | [+1.7, +13.2] pp |
| Episode length | 157.28 | 67.32 | -89.96 | [-164.39, -27.24] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| single | 23 | 5.39 |
| multi_relation | 47 | 15.02 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 80.0% | 80.0% | +0.0 pp |
| 0 | Post-failure chain recovered | 80.0% | 80.0% | +0.0 pp |
| 0 | Timeout | 20.0% | 20.0% | +0.0 pp |
| 0 | Restricted mean recovery steps | 48.20 | 48.30 | +0.10 |
| 0 | Tracking during failure | 82.6% | 83.3% | +0.7 pp |
| 0 | Connectivity during failure | 32.5% | 29.3% | -3.2 pp |
| 0 | Chain closure during failure | 13.4% | 13.0% | -0.4 pp |
| 0 | Episode length | 88.20 | 88.30 | +0.10 |
| 1 | Task success | 30.0% | 100.0% | +70.0 pp |
| 1 | Post-failure chain recovered | 30.0% | 100.0% | +70.0 pp |
| 1 | Timeout | 60.0% | 0.0% | -60.0 pp |
| 1 | Restricted mean recovery steps | 135.70 | 5.50 | -130.20 |
| 1 | Tracking during failure | 45.0% | 99.4% | +54.4 pp |
| 1 | Connectivity during failure | 18.8% | 33.2% | +14.4 pp |
| 1 | Chain closure during failure | 4.5% | 16.3% | +11.7 pp |
| 1 | Episode length | 175.70 | 45.50 | -130.20 |
| 2 | Task success | 0.0% | 100.0% | +100.0 pp |
| 2 | Post-failure chain recovered | 0.0% | 100.0% | +100.0 pp |
| 2 | Timeout | 100.0% | 0.0% | -100.0 pp |
| 2 | Restricted mean recovery steps | 220.00 | 5.20 | -214.80 |
| 2 | Tracking during failure | 12.9% | 100.0% | +87.1 pp |
| 2 | Connectivity during failure | 7.0% | 33.7% | +26.7 pp |
| 2 | Chain closure during failure | 0.0% | 16.6% | +16.6 pp |
| 2 | Episode length | 260.00 | 45.20 | -214.80 |
| 3 | Task success | 50.0% | 90.0% | +40.0 pp |
| 3 | Post-failure chain recovered | 50.0% | 90.0% | +40.0 pp |
| 3 | Timeout | 50.0% | 10.0% | -40.0 pp |
| 3 | Restricted mean recovery steps | 113.00 | 72.50 | -40.50 |
| 3 | Tracking during failure | 34.8% | 59.0% | +24.2 pp |
| 3 | Connectivity during failure | 20.0% | 23.0% | +3.1 pp |
| 3 | Chain closure during failure | 7.3% | 9.4% | +2.2 pp |
| 3 | Episode length | 153.00 | 112.50 | -40.50 |
| 4 | Task success | 70.0% | 100.0% | +30.0 pp |
| 4 | Post-failure chain recovered | 70.0% | 100.0% | +30.0 pp |
| 4 | Timeout | 30.0% | 0.0% | -30.0 pp |
| 4 | Restricted mean recovery steps | 69.50 | 5.10 | -64.40 |
| 4 | Tracking during failure | 48.2% | 66.7% | +18.5 pp |
| 4 | Connectivity during failure | 29.1% | 36.7% | +7.6 pp |
| 4 | Chain closure during failure | 11.9% | 16.8% | +4.9 pp |
| 4 | Episode length | 109.50 | 45.10 | -64.40 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
