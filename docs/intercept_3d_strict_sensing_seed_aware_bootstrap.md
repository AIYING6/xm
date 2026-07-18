# Strict-Sensing Seed-Aware Statistics

This report uses matched strict-sensing relay-failure test episodes from the formal development runs.
Uncertainty is estimated with a hierarchical bootstrap: training seeds are resampled first, then matched episodes are resampled within each selected training seed.

- Baseline: `single`
- Proposed: `multi_relation`
- Independent training seeds: 3
- Matched test episodes: 300

## Bootstrap Summary

| Metric | Baseline | Proposed | Delta | 95% CI for delta |
|---|---:|---:|---:|---:|
| Task success | 92.7% | 100.0% | +7.3 pp | [+0.0, +13.7] pp |
| Post-failure chain recovered | 92.7% | 100.0% | +7.3 pp | [+0.0, +13.7] pp |
| Timeout | 7.3% | 0.0% | -7.3 pp | [-13.7, +0.0] pp |
| Restricted mean recovery steps | 21.12 | 5.43 | -15.69 | [-29.34, +0.25] |
| Tracking during failure | 93.7% | 100.0% | +6.3 pp | [+0.1, +11.6] pp |
| Connectivity during failure | 43.2% | 44.0% | +0.9 pp | [-0.3, +1.8] pp |
| Chain closure during failure | 15.0% | 16.0% | +1.1 pp | [-0.4, +2.2] pp |
| Episode length | 61.12 | 45.43 | -15.69 | [-29.34, +0.25] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| single | 278 | 5.38 |
| multi_relation | 300 | 5.43 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 90.0% | 100.0% | +10.0 pp |
| 0 | Post-failure chain recovered | 90.0% | 100.0% | +10.0 pp |
| 0 | Timeout | 10.0% | 0.0% | -10.0 pp |
| 0 | Restricted mean recovery steps | 26.93 | 5.52 | -21.41 |
| 0 | Tracking during failure | 91.4% | 100.0% | +8.6 pp |
| 0 | Connectivity during failure | 42.8% | 43.9% | +1.2 pp |
| 0 | Chain closure during failure | 14.4% | 15.9% | +1.5 pp |
| 0 | Episode length | 66.93 | 45.52 | -21.41 |
| 1 | Task success | 88.0% | 100.0% | +12.0 pp |
| 1 | Post-failure chain recovered | 88.0% | 100.0% | +12.0 pp |
| 1 | Timeout | 12.0% | 0.0% | -12.0 pp |
| 1 | Restricted mean recovery steps | 31.17 | 5.26 | -25.91 |
| 1 | Tracking during failure | 89.8% | 100.0% | +10.2 pp |
| 1 | Connectivity during failure | 42.5% | 44.2% | +1.7 pp |
| 1 | Chain closure during failure | 14.2% | 16.3% | +2.2 pp |
| 1 | Episode length | 71.17 | 45.26 | -25.91 |
| 2 | Task success | 100.0% | 100.0% | +0.0 pp |
| 2 | Post-failure chain recovered | 100.0% | 100.0% | +0.0 pp |
| 2 | Timeout | 0.0% | 0.0% | +0.0 pp |
| 2 | Restricted mean recovery steps | 5.26 | 5.52 | +0.26 |
| 2 | Tracking during failure | 99.9% | 100.0% | +0.1 pp |
| 2 | Connectivity during failure | 44.2% | 43.9% | -0.3 pp |
| 2 | Chain closure during failure | 16.3% | 15.9% | -0.5 pp |
| 2 | Episode length | 45.26 | 45.52 | +0.26 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
