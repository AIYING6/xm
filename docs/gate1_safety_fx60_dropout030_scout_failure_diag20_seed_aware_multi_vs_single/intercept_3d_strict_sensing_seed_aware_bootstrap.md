# Strict-Sensing Seed-Aware Statistics

This report uses matched strict-sensing evaluation episodes from the selected scenario.
Uncertainty is estimated with a hierarchical bootstrap: training seeds are resampled first, then matched episodes are resampled within each selected training seed.

- Baseline: `single`
- Proposed: `multi_relation`
- Independent training seeds: 5
- Matched test episodes: 100

## Bootstrap Summary

| Metric | Baseline | Proposed | Delta | 95% CI for delta |
|---|---:|---:|---:|---:|
| Task success | 51.0% | 76.0% | +25.0 pp | [-15.0, +66.0] pp |
| Post-failure chain recovered | 51.0% | 76.0% | +25.0 pp | [-15.0, +66.0] pp |
| Timeout | 47.0% | 24.0% | -23.0 pp | [-63.0, +15.0] pp |
| Restricted mean recovery steps | 106.89 | 57.03 | -49.86 | [-135.77, +31.62] |
| Tracking during failure | 44.7% | 70.4% | +25.6 pp | [-5.2, +59.4] pp |
| Connectivity during failure | 16.3% | 22.2% | +5.8 pp | [-0.2, +13.0] pp |
| Chain closure during failure | 7.6% | 12.2% | +4.6 pp | [-1.4, +11.1] pp |
| Episode length | 146.86 | 97.03 | -49.83 | [-135.77, +31.68] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| single | 51 | 6.27 |
| multi_relation | 76 | 5.57 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 80.0% | 60.0% | -20.0 pp |
| 0 | Post-failure chain recovered | 80.0% | 60.0% | -20.0 pp |
| 0 | Timeout | 20.0% | 40.0% | +20.0 pp |
| 0 | Restricted mean recovery steps | 49.30 | 91.10 | +41.80 |
| 0 | Tracking during failure | 83.4% | 66.2% | -17.2 pp |
| 0 | Connectivity during failure | 24.0% | 23.6% | -0.5 pp |
| 0 | Chain closure during failure | 11.7% | 10.2% | -1.6 pp |
| 0 | Episode length | 89.30 | 131.10 | +41.80 |
| 1 | Task success | 30.0% | 80.0% | +50.0 pp |
| 1 | Post-failure chain recovered | 30.0% | 80.0% | +50.0 pp |
| 1 | Timeout | 70.0% | 20.0% | -50.0 pp |
| 1 | Restricted mean recovery steps | 156.10 | 48.80 | -107.30 |
| 1 | Tracking during failure | 37.0% | 83.0% | +46.0 pp |
| 1 | Connectivity during failure | 12.0% | 21.6% | +9.6 pp |
| 1 | Chain closure during failure | 3.8% | 12.1% | +8.4 pp |
| 1 | Episode length | 196.10 | 88.80 | -107.30 |
| 2 | Task success | 0.0% | 100.0% | +100.0 pp |
| 2 | Post-failure chain recovered | 0.0% | 100.0% | +100.0 pp |
| 2 | Timeout | 95.0% | 0.0% | -95.0 pp |
| 2 | Restricted mean recovery steps | 210.45 | 5.35 | -205.10 |
| 2 | Tracking during failure | 13.5% | 100.0% | +86.5 pp |
| 2 | Connectivity during failure | 4.7% | 23.8% | +19.1 pp |
| 2 | Chain closure during failure | 0.0% | 16.5% | +16.5 pp |
| 2 | Episode length | 250.45 | 45.35 | -205.10 |
| 3 | Task success | 65.0% | 40.0% | -25.0 pp |
| 3 | Post-failure chain recovered | 65.0% | 40.0% | -25.0 pp |
| 3 | Timeout | 35.0% | 60.0% | +25.0 pp |
| 3 | Restricted mean recovery steps | 80.75 | 134.25 | +53.50 |
| 3 | Tracking during failure | 35.8% | 41.9% | +6.1 pp |
| 3 | Connectivity during failure | 19.5% | 18.5% | -1.0 pp |
| 3 | Chain closure during failure | 10.2% | 6.4% | -3.8 pp |
| 3 | Episode length | 120.75 | 174.25 | +53.50 |
| 4 | Task success | 80.0% | 100.0% | +20.0 pp |
| 4 | Post-failure chain recovered | 80.0% | 100.0% | +20.0 pp |
| 4 | Timeout | 15.0% | 0.0% | -15.0 pp |
| 4 | Restricted mean recovery steps | 37.85 | 5.65 | -32.20 |
| 4 | Tracking during failure | 54.0% | 60.8% | +6.8 pp |
| 4 | Connectivity during failure | 21.3% | 23.3% | +2.0 pp |
| 4 | Chain closure during failure | 12.2% | 15.8% | +3.6 pp |
| 4 | Episode length | 77.70 | 45.65 | -32.05 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
