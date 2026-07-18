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
| Task success | 43.3% | 93.3% | +50.0 pp | [+15.0, +80.0] pp |
| Post-failure chain recovered | 43.3% | 93.3% | +50.0 pp | [+15.0, +80.0] pp |
| Timeout | 56.7% | 5.0% | -51.7 pp | [-80.0, -20.0] pp |
| Restricted mean recovery steps | 127.32 | 16.75 | -110.57 | [-171.70, -42.23] |
| Tracking during failure | 51.4% | 95.3% | +44.0 pp | [+16.4, +69.0] pp |
| Connectivity during failure | 20.6% | 32.2% | +11.6 pp | [+2.5, +19.1] pp |
| Chain closure during failure | 6.3% | 14.1% | +7.8 pp | [+1.9, +12.9] pp |
| Episode length | 167.32 | 56.75 | -110.57 | [-171.70, -42.23] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| single | 26 | 6.12 |
| multi_relation | 56 | 5.89 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 75.0% | 90.0% | +15.0 pp |
| 0 | Post-failure chain recovered | 75.0% | 90.0% | +15.0 pp |
| 0 | Timeout | 25.0% | 5.0% | -20.0 pp |
| 0 | Restricted mean recovery steps | 59.30 | 17.25 | -42.05 |
| 0 | Tracking during failure | 78.8% | 94.9% | +16.2 pp |
| 0 | Connectivity during failure | 29.6% | 31.7% | +2.0 pp |
| 0 | Chain closure during failure | 11.6% | 13.3% | +1.7 pp |
| 0 | Episode length | 99.30 | 57.25 | -42.05 |
| 1 | Task success | 35.0% | 90.0% | +55.0 pp |
| 1 | Post-failure chain recovered | 35.0% | 90.0% | +55.0 pp |
| 1 | Timeout | 65.0% | 10.0% | -55.0 pp |
| 1 | Restricted mean recovery steps | 145.40 | 27.35 | -118.05 |
| 1 | Tracking during failure | 44.8% | 91.1% | +46.3 pp |
| 1 | Connectivity during failure | 17.3% | 31.4% | +14.1 pp |
| 1 | Chain closure during failure | 4.5% | 13.4% | +8.9 pp |
| 1 | Episode length | 185.40 | 67.35 | -118.05 |
| 2 | Task success | 20.0% | 100.0% | +80.0 pp |
| 2 | Post-failure chain recovered | 20.0% | 100.0% | +80.0 pp |
| 2 | Timeout | 80.0% | 0.0% | -80.0 pp |
| 2 | Restricted mean recovery steps | 177.25 | 5.65 | -171.60 |
| 2 | Tracking during failure | 30.6% | 100.0% | +69.4 pp |
| 2 | Connectivity during failure | 14.9% | 33.5% | +18.6 pp |
| 2 | Chain closure during failure | 2.8% | 15.5% | +12.7 pp |
| 2 | Episode length | 217.25 | 45.65 | -171.60 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
