# Strict-Sensing Seed-Aware Statistics

This report uses matched strict-sensing relay-failure test episodes from the formal development runs.
Uncertainty is estimated with a hierarchical bootstrap: training seeds are resampled first, then matched episodes are resampled within each selected training seed.

- Baseline: `single`
- Proposed: `multi_relation`
- Independent training seeds: 3
- Matched test episodes: 60

## Bootstrap Summary

| Metric | Baseline | Proposed | Delta | 95% CI for delta |
|---|---:|---:|---:|---:|
| Task success | 88.3% | 96.7% | +8.3 pp | [-1.7, +21.7] pp |
| Post-failure chain recovered | 88.3% | 96.7% | +8.3 pp | [-1.7, +21.7] pp |
| Timeout | 11.7% | 3.3% | -8.3 pp | [-21.7, +1.7] pp |
| Restricted mean recovery steps | 30.47 | 13.05 | -17.42 | [-45.57, +3.77] |
| Tracking during failure | 90.2% | 97.2% | +7.0 pp | [-1.4, +18.1] pp |
| Connectivity during failure | 31.7% | 32.4% | +0.6 pp | [-1.8, +2.8] pp |
| Chain closure during failure | 14.1% | 14.7% | +0.6 pp | [-0.8, +2.1] pp |
| Episode length | 70.47 | 53.05 | -17.42 | [-45.57, +3.77] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| single | 53 | 5.43 |
| multi_relation | 58 | 5.91 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 80.0% | 100.0% | +20.0 pp |
| 0 | Post-failure chain recovered | 80.0% | 100.0% | +20.0 pp |
| 0 | Timeout | 20.0% | 0.0% | -20.0 pp |
| 0 | Restricted mean recovery steps | 48.45 | 6.45 | -42.00 |
| 0 | Tracking during failure | 83.3% | 100.0% | +16.7 pp |
| 0 | Connectivity during failure | 30.3% | 31.9% | +1.6 pp |
| 0 | Chain closure during failure | 12.6% | 14.4% | +1.8 pp |
| 0 | Episode length | 88.45 | 46.45 | -42.00 |
| 1 | Task success | 85.0% | 90.0% | +5.0 pp |
| 1 | Post-failure chain recovered | 85.0% | 90.0% | +5.0 pp |
| 1 | Timeout | 15.0% | 10.0% | -5.0 pp |
| 1 | Restricted mean recovery steps | 37.75 | 27.10 | -10.65 |
| 1 | Tracking during failure | 87.3% | 91.6% | +4.3 pp |
| 1 | Connectivity during failure | 30.3% | 32.3% | +1.9 pp |
| 1 | Chain closure during failure | 13.3% | 14.1% | +0.8 pp |
| 1 | Episode length | 77.75 | 67.10 | -10.65 |
| 2 | Task success | 100.0% | 100.0% | +0.0 pp |
| 2 | Post-failure chain recovered | 100.0% | 100.0% | +0.0 pp |
| 2 | Timeout | 0.0% | 0.0% | +0.0 pp |
| 2 | Restricted mean recovery steps | 5.20 | 5.60 | +0.40 |
| 2 | Tracking during failure | 100.0% | 100.0% | +0.0 pp |
| 2 | Connectivity during failure | 34.6% | 33.0% | -1.6 pp |
| 2 | Chain closure during failure | 16.5% | 15.7% | -0.8 pp |
| 2 | Episode length | 45.20 | 45.60 | +0.40 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
