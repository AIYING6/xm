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
| Task success | 86.7% | 93.3% | +6.7 pp | [-15.0, +33.3] pp |
| Post-failure chain recovered | 86.7% | 93.3% | +6.7 pp | [-15.0, +33.3] pp |
| Timeout | 13.3% | 6.7% | -6.7 pp | [-33.3, +15.0] pp |
| Restricted mean recovery steps | 34.05 | 20.22 | -13.83 | [-70.57, +32.28] |
| Tracking during failure | 88.6% | 94.4% | +5.7 pp | [-12.6, +28.3] pp |
| Connectivity during failure | 31.6% | 31.1% | -0.6 pp | [-2.9, +1.8] pp |
| Chain closure during failure | 13.9% | 13.9% | +0.1 pp | [-2.5, +3.4] pp |
| Episode length | 74.05 | 60.22 | -13.83 | [-70.57, +32.28] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| single | 52 | 5.44 |
| multi_relation | 56 | 5.95 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 65.0% | 100.0% | +35.0 pp |
| 0 | Post-failure chain recovered | 65.0% | 100.0% | +35.0 pp |
| 0 | Timeout | 35.0% | 0.0% | -35.0 pp |
| 0 | Restricted mean recovery steps | 80.45 | 6.35 | -74.10 |
| 0 | Tracking during failure | 70.4% | 100.0% | +29.6 pp |
| 0 | Connectivity during failure | 29.5% | 30.8% | +1.3 pp |
| 0 | Chain closure during failure | 10.6% | 14.2% | +3.6 pp |
| 0 | Episode length | 120.45 | 46.35 | -74.10 |
| 1 | Task success | 95.0% | 80.0% | -15.0 pp |
| 1 | Post-failure chain recovered | 95.0% | 80.0% | -15.0 pp |
| 1 | Timeout | 5.0% | 20.0% | +15.0 pp |
| 1 | Restricted mean recovery steps | 16.20 | 48.35 | +32.15 |
| 1 | Tracking during failure | 95.6% | 83.1% | -12.4 pp |
| 1 | Connectivity during failure | 32.7% | 31.1% | -1.7 pp |
| 1 | Chain closure during failure | 15.1% | 12.8% | -2.3 pp |
| 1 | Episode length | 56.20 | 88.35 | +32.15 |
| 2 | Task success | 100.0% | 100.0% | +0.0 pp |
| 2 | Post-failure chain recovered | 100.0% | 100.0% | +0.0 pp |
| 2 | Timeout | 0.0% | 0.0% | +0.0 pp |
| 2 | Restricted mean recovery steps | 5.50 | 5.95 | +0.45 |
| 2 | Tracking during failure | 100.0% | 100.0% | +0.0 pp |
| 2 | Connectivity during failure | 32.7% | 31.4% | -1.3 pp |
| 2 | Chain closure during failure | 15.9% | 14.8% | -1.1 pp |
| 2 | Episode length | 45.50 | 45.95 | +0.45 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
