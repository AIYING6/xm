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
| Task success | 56.0% | 85.0% | +29.0 pp | [-5.0, +70.0] pp |
| Post-failure chain recovered | 56.0% | 85.0% | +29.0 pp | [-5.0, +70.0] pp |
| Timeout | 42.0% | 15.0% | -27.0 pp | [-67.0, +6.0] pp |
| Restricted mean recovery steps | 95.81 | 37.69 | -58.12 | [-144.37, +12.88] |
| Tracking during failure | 50.1% | 78.3% | +28.2 pp | [+0.8, +61.1] pp |
| Connectivity during failure | 17.1% | 21.8% | +4.7 pp | [-1.0, +11.5] pp |
| Chain closure during failure | 8.7% | 13.6% | +4.9 pp | [-0.6, +11.6] pp |
| Episode length | 135.79 | 77.69 | -58.10 | [-144.37, +12.92] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| single | 56 | 5.80 |
| multi_relation | 85 | 5.52 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 90.0% | 80.0% | -10.0 pp |
| 0 | Post-failure chain recovered | 90.0% | 80.0% | -10.0 pp |
| 0 | Timeout | 10.0% | 20.0% | +10.0 pp |
| 0 | Restricted mean recovery steps | 27.00 | 48.70 | +21.70 |
| 0 | Tracking during failure | 91.6% | 82.9% | -8.7 pp |
| 0 | Connectivity during failure | 24.5% | 23.4% | -1.2 pp |
| 0 | Chain closure during failure | 14.5% | 12.4% | -2.1 pp |
| 0 | Episode length | 67.00 | 88.70 | +21.70 |
| 1 | Task success | 15.0% | 70.0% | +55.0 pp |
| 1 | Post-failure chain recovered | 15.0% | 70.0% | +55.0 pp |
| 1 | Timeout | 85.0% | 30.0% | -55.0 pp |
| 1 | Restricted mean recovery steps | 188.05 | 70.10 | -117.95 |
| 1 | Tracking during failure | 26.4% | 74.5% | +48.1 pp |
| 1 | Connectivity during failure | 10.3% | 19.4% | +9.1 pp |
| 1 | Chain closure during failure | 1.9% | 10.6% | +8.7 pp |
| 1 | Episode length | 228.05 | 110.10 | -117.95 |
| 2 | Task success | 0.0% | 100.0% | +100.0 pp |
| 2 | Post-failure chain recovered | 0.0% | 100.0% | +100.0 pp |
| 2 | Timeout | 95.0% | 0.0% | -95.0 pp |
| 2 | Restricted mean recovery steps | 209.80 | 5.15 | -204.65 |
| 2 | Tracking during failure | 14.8% | 100.0% | +85.2 pp |
| 2 | Connectivity during failure | 5.8% | 22.2% | +16.5 pp |
| 2 | Chain closure during failure | 0.0% | 16.7% | +16.7 pp |
| 2 | Episode length | 249.80 | 45.15 | -204.65 |
| 3 | Task success | 80.0% | 75.0% | -5.0 pp |
| 3 | Post-failure chain recovered | 80.0% | 75.0% | -5.0 pp |
| 3 | Timeout | 20.0% | 25.0% | +5.0 pp |
| 3 | Restricted mean recovery steps | 48.35 | 59.00 | +10.65 |
| 3 | Tracking during failure | 55.0% | 68.7% | +13.7 pp |
| 3 | Connectivity during failure | 23.5% | 21.8% | -1.7 pp |
| 3 | Chain closure during failure | 12.9% | 12.3% | -0.6 pp |
| 3 | Episode length | 88.35 | 99.00 | +10.65 |
| 4 | Task success | 95.0% | 100.0% | +5.0 pp |
| 4 | Post-failure chain recovered | 95.0% | 100.0% | +5.0 pp |
| 4 | Timeout | 0.0% | 0.0% | +0.0 pp |
| 4 | Restricted mean recovery steps | 5.85 | 5.50 | -0.35 |
| 4 | Tracking during failure | 62.8% | 65.5% | +2.7 pp |
| 4 | Connectivity during failure | 21.3% | 22.0% | +0.7 pp |
| 4 | Chain closure during failure | 14.1% | 16.1% | +2.0 pp |
| 4 | Episode length | 45.75 | 45.50 | -0.25 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
