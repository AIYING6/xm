# Strict-Sensing Seed-Aware Statistics

This report uses matched strict-sensing evaluation episodes from the selected scenario.
Uncertainty is estimated with a hierarchical bootstrap: training seeds are resampled first, then matched episodes are resampled within each selected training seed.

- Baseline: `no_graph`
- Proposed: `multi_relation`
- Independent training seeds: 5
- Matched test episodes: 100

## Bootstrap Summary

| Metric | Baseline | Proposed | Delta | 95% CI for delta |
|---|---:|---:|---:|---:|
| Task success | 24.0% | 76.0% | +52.0 pp | [+15.0, +83.0] pp |
| Post-failure chain recovered | 24.0% | 76.0% | +52.0 pp | [+15.0, +83.0] pp |
| Timeout | 76.0% | 24.0% | -52.0 pp | [-83.0, -15.0] pp |
| Restricted mean recovery steps | 168.46 | 57.03 | -111.43 | [-178.10, -31.87] |
| Tracking during failure | 15.1% | 70.4% | +55.3 pp | [+33.0, +79.7] pp |
| Connectivity during failure | 14.5% | 22.2% | +7.6 pp | [+0.7, +14.9] pp |
| Chain closure during failure | 4.0% | 12.2% | +8.2 pp | [+1.8, +13.5] pp |
| Episode length | 208.46 | 97.03 | -111.43 | [-178.10, -31.87] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| no_graph | 24 | 5.25 |
| multi_relation | 76 | 5.57 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 0.0% | 60.0% | +60.0 pp |
| 0 | Post-failure chain recovered | 0.0% | 60.0% | +60.0 pp |
| 0 | Timeout | 100.0% | 40.0% | -60.0 pp |
| 0 | Restricted mean recovery steps | 220.00 | 91.10 | -128.90 |
| 0 | Tracking during failure | 3.7% | 66.2% | +62.4 pp |
| 0 | Connectivity during failure | 5.3% | 23.6% | +18.3 pp |
| 0 | Chain closure during failure | 0.0% | 10.2% | +10.2 pp |
| 0 | Episode length | 260.00 | 131.10 | -128.90 |
| 1 | Task success | 95.0% | 80.0% | -15.0 pp |
| 1 | Post-failure chain recovered | 95.0% | 80.0% | -15.0 pp |
| 1 | Timeout | 5.0% | 20.0% | +15.0 pp |
| 1 | Restricted mean recovery steps | 16.20 | 48.80 | +32.60 |
| 1 | Tracking during failure | 60.8% | 83.0% | +22.3 pp |
| 1 | Connectivity during failure | 23.8% | 21.6% | -2.2 pp |
| 1 | Chain closure during failure | 15.5% | 12.1% | -3.4 pp |
| 1 | Episode length | 56.20 | 88.80 | +32.60 |
| 2 | Task success | 0.0% | 100.0% | +100.0 pp |
| 2 | Post-failure chain recovered | 0.0% | 100.0% | +100.0 pp |
| 2 | Timeout | 100.0% | 0.0% | -100.0 pp |
| 2 | Restricted mean recovery steps | 220.00 | 5.35 | -214.65 |
| 2 | Tracking during failure | 0.5% | 100.0% | +99.5 pp |
| 2 | Connectivity during failure | 22.3% | 23.8% | +1.6 pp |
| 2 | Chain closure during failure | 0.0% | 16.5% | +16.5 pp |
| 2 | Episode length | 260.00 | 45.35 | -214.65 |
| 3 | Task success | 0.0% | 40.0% | +40.0 pp |
| 3 | Post-failure chain recovered | 0.0% | 40.0% | +40.0 pp |
| 3 | Timeout | 100.0% | 60.0% | -40.0 pp |
| 3 | Restricted mean recovery steps | 220.00 | 134.25 | -85.75 |
| 3 | Tracking during failure | 0.0% | 41.9% | +41.9 pp |
| 3 | Connectivity during failure | 13.1% | 18.5% | +5.5 pp |
| 3 | Chain closure during failure | 0.0% | 6.4% | +6.4 pp |
| 3 | Episode length | 260.00 | 174.25 | -85.75 |
| 4 | Task success | 25.0% | 100.0% | +75.0 pp |
| 4 | Post-failure chain recovered | 25.0% | 100.0% | +75.0 pp |
| 4 | Timeout | 75.0% | 0.0% | -75.0 pp |
| 4 | Restricted mean recovery steps | 166.10 | 5.65 | -160.45 |
| 4 | Tracking during failure | 10.4% | 60.8% | +50.4 pp |
| 4 | Connectivity during failure | 8.4% | 23.3% | +14.9 pp |
| 4 | Chain closure during failure | 4.7% | 15.8% | +11.1 pp |
| 4 | Episode length | 206.10 | 45.65 | -160.45 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
