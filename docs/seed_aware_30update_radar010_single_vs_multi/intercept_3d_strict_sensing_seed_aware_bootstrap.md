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
| Task success | 95.0% | 93.3% | -1.7 pp | [-15.0, +11.7] pp |
| Post-failure chain recovered | 95.0% | 93.3% | -1.7 pp | [-15.0, +11.7] pp |
| Timeout | 5.0% | 6.7% | +1.7 pp | [-11.7, +15.0] pp |
| Restricted mean recovery steps | 16.22 | 20.15 | +3.93 | [-24.30, +32.48] |
| Tracking during failure | 85.0% | 84.5% | -0.5 pp | [-10.7, +7.9] pp |
| Connectivity during failure | 43.5% | 42.8% | -0.7 pp | [-2.3, +0.7] pp |
| Chain closure during failure | 15.3% | 14.4% | -0.9 pp | [-2.8, +0.7] pp |
| Episode length | 56.22 | 60.15 | +3.93 | [-24.30, +32.48] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| single | 57 | 5.49 |
| multi_relation | 56 | 5.88 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 100.0% | 100.0% | +0.0 pp |
| 0 | Post-failure chain recovered | 100.0% | 100.0% | +0.0 pp |
| 0 | Timeout | 0.0% | 0.0% | +0.0 pp |
| 0 | Restricted mean recovery steps | 5.35 | 5.50 | +0.15 |
| 0 | Tracking during failure | 88.4% | 90.2% | +1.8 pp |
| 0 | Connectivity during failure | 44.3% | 44.2% | -0.1 pp |
| 0 | Chain closure during failure | 16.4% | 16.3% | -0.1 pp |
| 0 | Episode length | 45.35 | 45.50 | +0.15 |
| 1 | Task success | 95.0% | 80.0% | -15.0 pp |
| 1 | Post-failure chain recovered | 95.0% | 80.0% | -15.0 pp |
| 1 | Timeout | 5.0% | 20.0% | +15.0 pp |
| 1 | Restricted mean recovery steps | 16.15 | 48.55 | +32.40 |
| 1 | Tracking during failure | 84.2% | 74.5% | -9.7 pp |
| 1 | Connectivity during failure | 43.7% | 41.3% | -2.4 pp |
| 1 | Chain closure during failure | 15.5% | 12.6% | -2.9 pp |
| 1 | Episode length | 56.15 | 88.55 | +32.40 |
| 2 | Task success | 90.0% | 100.0% | +10.0 pp |
| 2 | Post-failure chain recovered | 90.0% | 100.0% | +10.0 pp |
| 2 | Timeout | 10.0% | 0.0% | -10.0 pp |
| 2 | Restricted mean recovery steps | 27.15 | 6.40 | -20.75 |
| 2 | Tracking during failure | 82.5% | 88.8% | +6.3 pp |
| 2 | Connectivity during failure | 42.5% | 42.9% | +0.4 pp |
| 2 | Chain closure during failure | 14.0% | 14.3% | +0.3 pp |
| 2 | Episode length | 67.15 | 46.40 | -20.75 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
