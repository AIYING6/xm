# Strict-Sensing Seed-Aware Statistics

This report uses matched strict-sensing relay-failure test episodes from the formal development runs.
Uncertainty is estimated with a hierarchical bootstrap: training seeds are resampled first, then matched episodes are resampled within each selected training seed.

- Baseline: `no_role_identity`
- Proposed: `full_multi`
- Independent training seeds: 5
- Matched test episodes: 250

## Bootstrap Summary

| Metric | Baseline | Proposed | Delta | 95% CI for delta |
|---|---:|---:|---:|---:|
| Task success | 56.8% | 87.2% | +30.4 pp | [+7.2, +64.4] pp |
| Post-failure chain recovered | 56.8% | 87.2% | +30.4 pp | [+7.2, +64.4] pp |
| Timeout | 35.2% | 12.8% | -22.4 pp | [-41.6, -7.2] pp |
| Restricted mean recovery steps | 97.99 | 37.93 | -60.06 | [-135.92, -6.15] |
| Tracking during failure | 36.8% | 76.4% | +39.7 pp | [+3.1, +75.5] pp |
| Connectivity during failure | 15.1% | 21.9% | +6.8 pp | [+1.3, +13.4] pp |
| Chain closure during failure | 8.7% | 12.9% | +4.2 pp | [-0.2, +10.1] pp |
| Episode length | 137.99 | 77.93 | -60.06 | [-135.92, -6.15] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| no_role_identity | 142 | 5.74 |
| full_multi | 218 | 11.20 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 40.0% | 50.0% | +10.0 pp |
| 0 | Post-failure chain recovered | 40.0% | 50.0% | +10.0 pp |
| 0 | Timeout | 60.0% | 50.0% | -10.0 pp |
| 0 | Restricted mean recovery steps | 134.42 | 112.72 | -21.70 |
| 0 | Tracking during failure | 27.3% | 57.8% | +30.5 pp |
| 0 | Connectivity during failure | 12.3% | 19.3% | +7.0 pp |
| 0 | Chain closure during failure | 5.8% | 8.1% | +2.3 pp |
| 0 | Episode length | 174.42 | 152.72 | -21.70 |
| 1 | Task success | 66.0% | 92.0% | +26.0 pp |
| 1 | Post-failure chain recovered | 66.0% | 92.0% | +26.0 pp |
| 1 | Timeout | 32.0% | 8.0% | -24.0 pp |
| 1 | Restricted mean recovery steps | 78.60 | 23.20 | -55.40 |
| 1 | Tracking during failure | 22.4% | 93.2% | +70.8 pp |
| 1 | Connectivity during failure | 15.9% | 23.0% | +7.1 pp |
| 1 | Chain closure during failure | 10.0% | 13.6% | +3.6 pp |
| 1 | Episode length | 118.60 | 63.20 | -55.40 |
| 2 | Task success | 2.0% | 98.0% | +96.0 pp |
| 2 | Post-failure chain recovered | 2.0% | 98.0% | +96.0 pp |
| 2 | Timeout | 60.0% | 2.0% | -58.0 pp |
| 2 | Restricted mean recovery steps | 214.18 | 9.78 | -204.40 |
| 2 | Tracking during failure | 1.0% | 98.3% | +97.4 pp |
| 2 | Connectivity during failure | 4.2% | 23.4% | +19.2 pp |
| 2 | Chain closure during failure | 0.2% | 15.6% | +15.3 pp |
| 2 | Episode length | 254.18 | 49.78 | -204.40 |
| 3 | Task success | 88.0% | 96.0% | +8.0 pp |
| 3 | Post-failure chain recovered | 88.0% | 96.0% | +8.0 pp |
| 3 | Timeout | 12.0% | 4.0% | -8.0 pp |
| 3 | Restricted mean recovery steps | 31.28 | 38.24 | +6.96 |
| 3 | Tracking during failure | 45.9% | 70.6% | +24.7 pp |
| 3 | Connectivity during failure | 20.7% | 20.1% | -0.6 pp |
| 3 | Chain closure during failure | 13.7% | 11.8% | -1.9 pp |
| 3 | Episode length | 71.28 | 78.24 | +6.96 |
| 4 | Task success | 88.0% | 100.0% | +12.0 pp |
| 4 | Post-failure chain recovered | 88.0% | 100.0% | +12.0 pp |
| 4 | Timeout | 12.0% | 0.0% | -12.0 pp |
| 4 | Restricted mean recovery steps | 31.46 | 5.70 | -25.76 |
| 4 | Tracking during failure | 87.2% | 62.2% | -25.0 pp |
| 4 | Connectivity during failure | 22.4% | 23.6% | +1.2 pp |
| 4 | Chain closure during failure | 13.7% | 15.5% | +1.7 pp |
| 4 | Episode length | 71.46 | 45.70 | -25.76 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
