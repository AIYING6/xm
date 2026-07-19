# Strict-Sensing Seed-Aware Statistics

This report uses matched strict-sensing relay-failure test episodes from the formal development runs.
Uncertainty is estimated with a hierarchical bootstrap: training seeds are resampled first, then matched episodes are resampled within each selected training seed.

- Baseline: `no_task_support`
- Proposed: `multi_relation`
- Independent training seeds: 5
- Matched test episodes: 500

## Bootstrap Summary

| Metric | Baseline | Proposed | Delta | 95% CI for delta |
|---|---:|---:|---:|---:|
| Task success | 64.8% | 88.6% | +23.8 pp | [-9.2, +63.6] pp |
| Post-failure chain recovered | 64.8% | 88.6% | +23.8 pp | [-9.2, +63.6] pp |
| Timeout | 34.4% | 11.4% | -23.0 pp | [-63.2, +9.8] pp |
| Restricted mean recovery steps | 88.18 | 36.02 | -52.16 | [-137.26, +19.06] |
| Tracking during failure | 59.6% | 77.6% | +18.0 pp | [-6.3, +42.3] pp |
| Connectivity during failure | 16.0% | 20.3% | +4.2 pp | [-1.0, +11.3] pp |
| Chain closure during failure | 8.9% | 13.8% | +4.8 pp | [-0.9, +11.0] pp |
| Episode length | 128.18 | 76.02 | -52.16 | [-137.26, +19.06] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| no_task_support | 324 | 19.17 |
| multi_relation | 443 | 12.35 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 91.0% | 65.0% | -26.0 pp |
| 0 | Post-failure chain recovered | 91.0% | 65.0% | -26.0 pp |
| 0 | Timeout | 9.0% | 35.0% | +26.0 pp |
| 0 | Restricted mean recovery steps | 25.11 | 80.40 | +55.29 |
| 0 | Tracking during failure | 92.0% | 70.4% | -21.6 pp |
| 0 | Connectivity during failure | 21.9% | 19.4% | -2.4 pp |
| 0 | Chain closure during failure | 14.0% | 10.7% | -3.3 pp |
| 0 | Episode length | 65.11 | 120.40 | +55.29 |
| 1 | Task success | 89.0% | 90.0% | +1.0 pp |
| 1 | Post-failure chain recovered | 89.0% | 90.0% | +1.0 pp |
| 1 | Timeout | 10.0% | 10.0% | +0.0 pp |
| 1 | Restricted mean recovery steps | 26.92 | 27.04 | +0.12 |
| 1 | Tracking during failure | 90.1% | 91.5% | +1.5 pp |
| 1 | Connectivity during failure | 21.9% | 21.2% | -0.7 pp |
| 1 | Chain closure during failure | 14.6% | 14.1% | -0.5 pp |
| 1 | Episode length | 66.92 | 67.04 | +0.12 |
| 2 | Task success | 72.0% | 99.0% | +27.0 pp |
| 2 | Post-failure chain recovered | 72.0% | 99.0% | +27.0 pp |
| 2 | Timeout | 27.0% | 1.0% | -26.0 pp |
| 2 | Restricted mean recovery steps | 63.52 | 7.16 | -56.36 |
| 2 | Tracking during failure | 76.8% | 99.2% | +22.5 pp |
| 2 | Connectivity during failure | 20.1% | 21.7% | +1.6 pp |
| 2 | Chain closure during failure | 11.2% | 16.8% | +5.6 pp |
| 2 | Episode length | 103.52 | 47.16 | -56.36 |
| 3 | Task success | 72.0% | 92.0% | +20.0 pp |
| 3 | Post-failure chain recovered | 72.0% | 92.0% | +20.0 pp |
| 3 | Timeout | 26.0% | 8.0% | -18.0 pp |
| 3 | Restricted mean recovery steps | 105.37 | 53.93 | -51.44 |
| 3 | Tracking during failure | 38.9% | 66.1% | +27.3 pp |
| 3 | Connectivity during failure | 12.3% | 17.4% | +5.1 pp |
| 3 | Chain closure during failure | 5.0% | 10.9% | +5.9 pp |
| 3 | Episode length | 145.37 | 93.93 | -51.44 |
| 4 | Task success | 0.0% | 97.0% | +97.0 pp |
| 4 | Post-failure chain recovered | 0.0% | 97.0% | +97.0 pp |
| 4 | Timeout | 100.0% | 3.0% | -97.0 pp |
| 4 | Restricted mean recovery steps | 220.00 | 11.58 | -208.42 |
| 4 | Tracking during failure | 0.5% | 60.9% | +60.4 pp |
| 4 | Connectivity during failure | 4.0% | 21.5% | +17.5 pp |
| 4 | Chain closure during failure | 0.0% | 16.2% | +16.2 pp |
| 4 | Episode length | 260.00 | 51.58 | -208.42 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
