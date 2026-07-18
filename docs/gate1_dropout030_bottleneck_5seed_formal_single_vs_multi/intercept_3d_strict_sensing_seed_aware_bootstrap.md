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
| Task success | 51.8% | 96.2% | +44.4 pp | [+16.2, +74.4] pp |
| Post-failure chain recovered | 51.8% | 96.2% | +44.4 pp | [+16.2, +74.4] pp |
| Timeout | 47.4% | 3.8% | -43.6 pp | [-73.0, -15.6] pp |
| Restricted mean recovery steps | 108.44 | 23.45 | -85.00 | [-153.87, -22.93] |
| Tracking during failure | 47.0% | 80.9% | +33.9 pp | [+8.5, +62.2] pp |
| Connectivity during failure | 21.2% | 30.0% | +8.8 pp | [+1.6, +16.9] pp |
| Chain closure during failure | 7.9% | 13.8% | +5.9 pp | [+0.9, +11.7] pp |
| Episode length | 148.44 | 63.45 | -85.00 | [-153.87, -22.93] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| single | 259 | 7.81 |
| multi_relation | 481 | 15.68 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 77.0% | 98.0% | +21.0 pp |
| 0 | Post-failure chain recovered | 77.0% | 98.0% | +21.0 pp |
| 0 | Timeout | 23.0% | 2.0% | -21.0 pp |
| 0 | Restricted mean recovery steps | 55.03 | 10.35 | -44.68 |
| 0 | Tracking during failure | 80.3% | 98.3% | +18.0 pp |
| 0 | Connectivity during failure | 28.9% | 32.5% | +3.6 pp |
| 0 | Chain closure during failure | 12.0% | 14.6% | +2.6 pp |
| 0 | Episode length | 95.03 | 50.35 | -44.68 |
| 1 | Task success | 30.0% | 95.0% | +65.0 pp |
| 1 | Post-failure chain recovered | 30.0% | 95.0% | +65.0 pp |
| 1 | Timeout | 68.0% | 5.0% | -63.0 pp |
| 1 | Restricted mean recovery steps | 151.66 | 16.59 | -135.07 |
| 1 | Tracking during failure | 41.4% | 95.6% | +54.2 pp |
| 1 | Connectivity during failure | 16.2% | 31.6% | +15.4 pp |
| 1 | Chain closure during failure | 4.2% | 14.5% | +10.3 pp |
| 1 | Episode length | 191.66 | 56.59 | -135.07 |
| 2 | Task success | 2.0% | 100.0% | +98.0 pp |
| 2 | Post-failure chain recovered | 2.0% | 100.0% | +98.0 pp |
| 2 | Timeout | 97.0% | 0.0% | -97.0 pp |
| 2 | Restricted mean recovery steps | 213.68 | 5.46 | -208.22 |
| 2 | Tracking during failure | 15.2% | 100.0% | +84.8 pp |
| 2 | Connectivity during failure | 9.8% | 32.4% | +22.6 pp |
| 2 | Chain closure during failure | 0.2% | 16.0% | +15.8 pp |
| 2 | Episode length | 253.68 | 45.46 | -208.22 |
| 3 | Task success | 57.0% | 92.0% | +35.0 pp |
| 3 | Post-failure chain recovered | 57.0% | 92.0% | +35.0 pp |
| 3 | Timeout | 43.0% | 8.0% | -35.0 pp |
| 3 | Restricted mean recovery steps | 103.13 | 67.82 | -35.31 |
| 3 | Tracking during failure | 37.6% | 50.2% | +12.6 pp |
| 3 | Connectivity during failure | 20.2% | 22.9% | +2.7 pp |
| 3 | Chain closure during failure | 8.5% | 8.9% | +0.4 pp |
| 3 | Episode length | 143.13 | 107.82 | -35.31 |
| 4 | Task success | 93.0% | 96.0% | +3.0 pp |
| 4 | Post-failure chain recovered | 93.0% | 96.0% | +3.0 pp |
| 4 | Timeout | 6.0% | 4.0% | -2.0 pp |
| 4 | Restricted mean recovery steps | 18.72 | 17.01 | -1.71 |
| 4 | Tracking during failure | 60.3% | 60.4% | +0.0 pp |
| 4 | Connectivity during failure | 30.7% | 30.6% | -0.2 pp |
| 4 | Chain closure during failure | 14.6% | 15.2% | +0.7 pp |
| 4 | Episode length | 58.72 | 57.01 | -1.71 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
