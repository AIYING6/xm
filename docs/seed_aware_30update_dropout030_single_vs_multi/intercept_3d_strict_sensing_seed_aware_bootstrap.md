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
| Task success | 76.7% | 98.3% | +21.7 pp | [+3.3, +41.7] pp |
| Post-failure chain recovered | 76.7% | 98.3% | +21.7 pp | [+3.3, +41.7] pp |
| Timeout | 21.7% | 1.7% | -20.0 pp | [-41.7, -3.3] pp |
| Restricted mean recovery steps | 51.63 | 9.27 | -42.37 | [-88.08, -6.72] |
| Tracking during failure | 81.4% | 98.6% | +17.2 pp | [+2.8, +35.0] pp |
| Connectivity during failure | 31.2% | 33.1% | +1.9 pp | [-1.0, +4.9] pp |
| Chain closure during failure | 13.4% | 15.5% | +2.1 pp | [-0.3, +4.5] pp |
| Episode length | 91.63 | 49.27 | -42.37 | [-88.08, -6.72] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| single | 46 | 4.87 |
| multi_relation | 59 | 5.69 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 60.0% | 100.0% | +40.0 pp |
| 0 | Post-failure chain recovered | 60.0% | 100.0% | +40.0 pp |
| 0 | Timeout | 40.0% | 0.0% | -40.0 pp |
| 0 | Restricted mean recovery steps | 90.70 | 6.05 | -84.65 |
| 0 | Tracking during failure | 66.4% | 100.0% | +33.6 pp |
| 0 | Connectivity during failure | 28.8% | 33.5% | +4.8 pp |
| 0 | Chain closure during failure | 11.0% | 15.2% | +4.1 pp |
| 0 | Episode length | 130.70 | 46.05 | -84.65 |
| 1 | Task success | 75.0% | 95.0% | +20.0 pp |
| 1 | Post-failure chain recovered | 75.0% | 95.0% | +20.0 pp |
| 1 | Timeout | 20.0% | 5.0% | -15.0 pp |
| 1 | Restricted mean recovery steps | 48.35 | 16.15 | -32.20 |
| 1 | Tracking during failure | 82.1% | 95.8% | +13.7 pp |
| 1 | Connectivity during failure | 31.7% | 32.8% | +1.1 pp |
| 1 | Chain closure during failure | 13.1% | 15.6% | +2.5 pp |
| 1 | Episode length | 88.35 | 56.15 | -32.20 |
| 2 | Task success | 95.0% | 100.0% | +5.0 pp |
| 2 | Post-failure chain recovered | 95.0% | 100.0% | +5.0 pp |
| 2 | Timeout | 5.0% | 0.0% | -5.0 pp |
| 2 | Restricted mean recovery steps | 15.85 | 5.60 | -10.25 |
| 2 | Tracking during failure | 95.8% | 100.0% | +4.2 pp |
| 2 | Connectivity during failure | 33.2% | 33.1% | -0.1 pp |
| 2 | Chain closure during failure | 15.9% | 15.6% | -0.3 pp |
| 2 | Episode length | 55.85 | 45.60 | -10.25 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
