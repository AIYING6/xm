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
| Task success | 21.8% | 88.0% | +66.2 pp | [+29.4, +93.2] pp |
| Post-failure chain recovered | 21.8% | 88.0% | +66.2 pp | [+29.4, +93.2] pp |
| Timeout | 77.8% | 12.0% | -65.8 pp | [-92.8, -29.2] pp |
| Restricted mean recovery steps | 172.45 | 37.60 | -134.85 | [-190.87, -60.44] |
| Tracking during failure | 14.6% | 76.0% | +61.5 pp | [+42.6, +82.7] pp |
| Connectivity during failure | 8.2% | 21.2% | +13.0 pp | [+6.2, +17.6] pp |
| Chain closure during failure | 3.5% | 12.9% | +9.4 pp | [+3.7, +13.9] pp |
| Episode length | 212.45 | 77.60 | -134.85 | [-190.87, -60.44] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| no_graph | 109 | 5.50 |
| multi_relation | 440 | 12.73 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 0.0% | 57.0% | +57.0 pp |
| 0 | Post-failure chain recovered | 0.0% | 57.0% | +57.0 pp |
| 0 | Timeout | 99.0% | 43.0% | -56.0 pp |
| 0 | Restricted mean recovery steps | 218.01 | 97.75 | -120.26 |
| 0 | Tracking during failure | 3.6% | 63.3% | +59.6 pp |
| 0 | Connectivity during failure | 4.1% | 19.4% | +15.3 pp |
| 0 | Chain closure during failure | 0.0% | 9.1% | +9.1 pp |
| 0 | Episode length | 258.01 | 137.75 | -120.26 |
| 1 | Task success | 93.0% | 91.0% | -2.0 pp |
| 1 | Post-failure chain recovered | 93.0% | 91.0% | -2.0 pp |
| 1 | Timeout | 7.0% | 9.0% | +2.0 pp |
| 1 | Restricted mean recovery steps | 20.71 | 25.33 | +4.62 |
| 1 | Tracking during failure | 61.3% | 92.4% | +31.1 pp |
| 1 | Connectivity during failure | 21.8% | 21.8% | +0.0 pp |
| 1 | Chain closure during failure | 14.5% | 13.5% | -1.0 pp |
| 1 | Episode length | 60.71 | 65.33 | +4.62 |
| 2 | Task success | 0.0% | 100.0% | +100.0 pp |
| 2 | Post-failure chain recovered | 0.0% | 100.0% | +100.0 pp |
| 2 | Timeout | 99.0% | 0.0% | -99.0 pp |
| 2 | Restricted mean recovery steps | 218.04 | 5.37 | -212.67 |
| 2 | Tracking during failure | 0.6% | 100.0% | +99.4 pp |
| 2 | Connectivity during failure | 3.9% | 23.5% | +19.5 pp |
| 2 | Chain closure during failure | 0.0% | 16.2% | +16.2 pp |
| 2 | Episode length | 258.04 | 45.37 | -212.67 |
| 3 | Task success | 0.0% | 92.0% | +92.0 pp |
| 3 | Post-failure chain recovered | 0.0% | 92.0% | +92.0 pp |
| 3 | Timeout | 100.0% | 8.0% | -92.0 pp |
| 3 | Restricted mean recovery steps | 220.00 | 52.74 | -167.26 |
| 3 | Tracking during failure | 0.1% | 63.6% | +63.4 pp |
| 3 | Connectivity during failure | 3.6% | 18.3% | +14.7 pp |
| 3 | Chain closure during failure | 0.0% | 10.4% | +10.4 pp |
| 3 | Episode length | 260.00 | 92.74 | -167.26 |
| 4 | Task success | 16.0% | 100.0% | +84.0 pp |
| 4 | Post-failure chain recovered | 16.0% | 100.0% | +84.0 pp |
| 4 | Timeout | 84.0% | 0.0% | -84.0 pp |
| 4 | Restricted mean recovery steps | 185.49 | 6.83 | -178.66 |
| 4 | Tracking during failure | 7.3% | 61.0% | +53.8 pp |
| 4 | Connectivity during failure | 7.6% | 23.1% | +15.5 pp |
| 4 | Chain closure during failure | 3.0% | 15.4% | +12.3 pp |
| 4 | Episode length | 225.49 | 46.83 | -178.66 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
