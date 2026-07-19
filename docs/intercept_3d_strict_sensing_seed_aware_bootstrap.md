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
| Task success | 21.8% | 88.6% | +66.8 pp | [+28.6, +93.8] pp |
| Post-failure chain recovered | 21.8% | 88.6% | +66.8 pp | [+28.6, +93.8] pp |
| Timeout | 77.4% | 11.4% | -66.0 pp | [-92.4, -28.4] pp |
| Restricted mean recovery steps | 171.82 | 36.02 | -135.80 | [-190.85, -57.14] |
| Tracking during failure | 14.8% | 77.6% | +62.8 pp | [+42.5, +84.2] pp |
| Connectivity during failure | 7.8% | 20.3% | +12.4 pp | [+5.8, +16.8] pp |
| Chain closure during failure | 3.7% | 13.8% | +10.1 pp | [+3.8, +14.8] pp |
| Episode length | 211.82 | 76.02 | -135.80 | [-190.85, -57.14] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| no_graph | 109 | 5.14 |
| multi_relation | 443 | 12.35 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 0.0% | 65.0% | +65.0 pp |
| 0 | Post-failure chain recovered | 0.0% | 65.0% | +65.0 pp |
| 0 | Timeout | 99.0% | 35.0% | -64.0 pp |
| 0 | Restricted mean recovery steps | 218.01 | 80.40 | -137.61 |
| 0 | Tracking during failure | 3.5% | 70.4% | +67.0 pp |
| 0 | Connectivity during failure | 4.0% | 19.4% | +15.5 pp |
| 0 | Chain closure during failure | 0.0% | 10.7% | +10.7 pp |
| 0 | Episode length | 258.01 | 120.40 | -137.61 |
| 1 | Task success | 96.0% | 90.0% | -6.0 pp |
| 1 | Post-failure chain recovered | 96.0% | 90.0% | -6.0 pp |
| 1 | Timeout | 4.0% | 10.0% | +6.0 pp |
| 1 | Restricted mean recovery steps | 13.79 | 27.04 | +13.25 |
| 1 | Tracking during failure | 64.0% | 91.5% | +27.6 pp |
| 1 | Connectivity during failure | 21.8% | 21.2% | -0.5 pp |
| 1 | Chain closure during failure | 16.0% | 14.1% | -1.9 pp |
| 1 | Episode length | 53.79 | 67.04 | +13.25 |
| 2 | Task success | 0.0% | 99.0% | +99.0 pp |
| 2 | Post-failure chain recovered | 0.0% | 99.0% | +99.0 pp |
| 2 | Timeout | 98.0% | 1.0% | -97.0 pp |
| 2 | Restricted mean recovery steps | 217.22 | 7.16 | -210.06 |
| 2 | Tracking during failure | 0.3% | 99.2% | +98.9 pp |
| 2 | Connectivity during failure | 3.6% | 21.7% | +18.1 pp |
| 2 | Chain closure during failure | 0.0% | 16.8% | +16.8 pp |
| 2 | Episode length | 257.22 | 47.16 | -210.06 |
| 3 | Task success | 0.0% | 92.0% | +92.0 pp |
| 3 | Post-failure chain recovered | 0.0% | 92.0% | +92.0 pp |
| 3 | Timeout | 99.0% | 8.0% | -91.0 pp |
| 3 | Restricted mean recovery steps | 218.06 | 53.93 | -164.13 |
| 3 | Tracking during failure | 0.0% | 66.1% | +66.1 pp |
| 3 | Connectivity during failure | 3.4% | 17.4% | +14.0 pp |
| 3 | Chain closure during failure | 0.0% | 10.9% | +10.9 pp |
| 3 | Episode length | 258.06 | 93.93 | -164.13 |
| 4 | Task success | 13.0% | 97.0% | +84.0 pp |
| 4 | Post-failure chain recovered | 13.0% | 97.0% | +84.0 pp |
| 4 | Timeout | 87.0% | 3.0% | -84.0 pp |
| 4 | Restricted mean recovery steps | 192.01 | 11.58 | -180.43 |
| 4 | Tracking during failure | 6.3% | 60.9% | +54.6 pp |
| 4 | Connectivity during failure | 6.4% | 21.5% | +15.1 pp |
| 4 | Chain closure during failure | 2.3% | 16.2% | +13.9 pp |
| 4 | Episode length | 232.01 | 51.58 | -180.43 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
