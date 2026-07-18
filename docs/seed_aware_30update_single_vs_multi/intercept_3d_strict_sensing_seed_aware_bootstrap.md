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
| Task success | 90.0% | 95.0% | +5.0 pp | [-3.3, +13.3] pp |
| Post-failure chain recovered | 90.0% | 95.0% | +5.0 pp | [-3.3, +13.3] pp |
| Timeout | 10.0% | 5.0% | -5.0 pp | [-13.3, +3.3] pp |
| Restricted mean recovery steps | 26.88 | 16.70 | -10.18 | [-27.85, +7.43] |
| Tracking during failure | 91.5% | 95.7% | +4.3 pp | [-2.8, +11.3] pp |
| Connectivity during failure | 43.1% | 42.8% | -0.3 pp | [-1.3, +0.6] pp |
| Chain closure during failure | 14.6% | 14.5% | -0.1 pp | [-1.1, +0.8] pp |
| Episode length | 66.88 | 56.70 | -10.18 | [-27.85, +7.43] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| single | 54 | 5.43 |
| multi_relation | 57 | 6.00 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 90.0% | 100.0% | +10.0 pp |
| 0 | Post-failure chain recovered | 90.0% | 100.0% | +10.0 pp |
| 0 | Timeout | 10.0% | 0.0% | -10.0 pp |
| 0 | Restricted mean recovery steps | 27.00 | 6.20 | -20.80 |
| 0 | Tracking during failure | 91.6% | 100.0% | +8.4 pp |
| 0 | Connectivity during failure | 43.0% | 43.3% | +0.2 pp |
| 0 | Chain closure during failure | 14.4% | 14.9% | +0.5 pp |
| 0 | Episode length | 67.00 | 46.20 | -20.80 |
| 1 | Task success | 85.0% | 85.0% | +0.0 pp |
| 1 | Post-failure chain recovered | 85.0% | 85.0% | +0.0 pp |
| 1 | Timeout | 15.0% | 15.0% | +0.0 pp |
| 1 | Restricted mean recovery steps | 37.50 | 37.90 | +0.40 |
| 1 | Tracking during failure | 87.3% | 87.2% | -0.1 pp |
| 1 | Connectivity during failure | 42.8% | 41.7% | -1.1 pp |
| 1 | Chain closure during failure | 14.0% | 13.3% | -0.7 pp |
| 1 | Episode length | 77.50 | 77.90 | +0.40 |
| 2 | Task success | 95.0% | 100.0% | +5.0 pp |
| 2 | Post-failure chain recovered | 95.0% | 100.0% | +5.0 pp |
| 2 | Timeout | 5.0% | 0.0% | -5.0 pp |
| 2 | Restricted mean recovery steps | 16.15 | 6.00 | -10.15 |
| 2 | Tracking during failure | 95.5% | 100.0% | +4.5 pp |
| 2 | Connectivity during failure | 43.4% | 43.5% | +0.1 pp |
| 2 | Chain closure during failure | 15.3% | 15.2% | -0.1 pp |
| 2 | Episode length | 56.15 | 46.00 | -10.15 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
