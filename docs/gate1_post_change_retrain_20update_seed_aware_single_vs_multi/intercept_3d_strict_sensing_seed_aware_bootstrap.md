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
| Task success | 33.3% | 93.3% | +60.0 pp | [+16.7, +91.7] pp |
| Post-failure chain recovered | 33.3% | 93.3% | +60.0 pp | [+16.7, +91.7] pp |
| Timeout | 65.0% | 6.7% | -58.3 pp | [-88.3, -16.7] pp |
| Restricted mean recovery steps | 145.25 | 20.12 | -125.13 | [-189.58, -35.85] |
| Tracking during failure | 43.7% | 94.4% | +50.7 pp | [+14.5, +76.8] pp |
| Connectivity during failure | 18.3% | 30.8% | +12.5 pp | [+1.5, +19.8] pp |
| Chain closure during failure | 5.0% | 14.3% | +9.3 pp | [+2.4, +14.4] pp |
| Episode length | 185.25 | 60.12 | -125.13 | [-189.58, -35.85] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| single | 20 | 6.05 |
| multi_relation | 56 | 5.84 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 70.0% | 85.0% | +15.0 pp |
| 0 | Post-failure chain recovered | 70.0% | 85.0% | +15.0 pp |
| 0 | Timeout | 30.0% | 15.0% | -15.0 pp |
| 0 | Restricted mean recovery steps | 70.15 | 38.05 | -32.10 |
| 0 | Tracking during failure | 74.8% | 87.7% | +12.9 pp |
| 0 | Connectivity during failure | 28.9% | 30.1% | +1.3 pp |
| 0 | Chain closure during failure | 10.7% | 12.9% | +2.1 pp |
| 0 | Episode length | 110.15 | 78.05 | -32.10 |
| 1 | Task success | 20.0% | 95.0% | +75.0 pp |
| 1 | Post-failure chain recovered | 20.0% | 95.0% | +75.0 pp |
| 1 | Timeout | 80.0% | 5.0% | -75.0 pp |
| 1 | Restricted mean recovery steps | 177.30 | 16.60 | -160.70 |
| 1 | Tracking during failure | 32.0% | 95.5% | +63.5 pp |
| 1 | Connectivity during failure | 13.0% | 31.6% | +18.6 pp |
| 1 | Chain closure during failure | 2.7% | 14.4% | +11.7 pp |
| 1 | Episode length | 217.30 | 56.60 | -160.70 |
| 2 | Task success | 10.0% | 100.0% | +90.0 pp |
| 2 | Post-failure chain recovered | 10.0% | 100.0% | +90.0 pp |
| 2 | Timeout | 85.0% | 0.0% | -85.0 pp |
| 2 | Restricted mean recovery steps | 188.30 | 5.70 | -182.60 |
| 2 | Tracking during failure | 24.4% | 100.0% | +75.6 pp |
| 2 | Connectivity during failure | 13.2% | 30.7% | +17.5 pp |
| 2 | Chain closure during failure | 1.5% | 15.6% | +14.1 pp |
| 2 | Episode length | 228.30 | 45.70 | -182.60 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
