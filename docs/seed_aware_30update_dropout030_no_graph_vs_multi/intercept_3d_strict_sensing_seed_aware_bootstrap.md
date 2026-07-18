# Strict-Sensing Seed-Aware Statistics

This report uses matched strict-sensing relay-failure test episodes from the formal development runs.
Uncertainty is estimated with a hierarchical bootstrap: training seeds are resampled first, then matched episodes are resampled within each selected training seed.

- Baseline: `no_graph`
- Proposed: `multi_relation`
- Independent training seeds: 3
- Matched test episodes: 60

## Bootstrap Summary

| Metric | Baseline | Proposed | Delta | 95% CI for delta |
|---|---:|---:|---:|---:|
| Task success | 28.3% | 98.3% | +70.0 pp | [+13.3, +100.0] pp |
| Post-failure chain recovered | 28.3% | 98.3% | +70.0 pp | [+13.3, +100.0] pp |
| Timeout | 71.7% | 1.7% | -70.0 pp | [-100.0, -13.3] pp |
| Restricted mean recovery steps | 159.13 | 9.27 | -149.87 | [-214.50, -28.38] |
| Tracking during failure | 20.2% | 98.6% | +78.4 pp | [+43.5, +99.7] pp |
| Connectivity during failure | 13.3% | 33.1% | +19.8 pp | [+3.5, +29.5] pp |
| Chain closure during failure | 4.8% | 15.5% | +10.7 pp | [+1.9, +16.1] pp |
| Episode length | 199.13 | 49.27 | -149.87 | [-214.50, -28.38] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| no_graph | 17 | 5.18 |
| multi_relation | 59 | 5.69 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 0.0% | 100.0% | +100.0 pp |
| 0 | Post-failure chain recovered | 0.0% | 100.0% | +100.0 pp |
| 0 | Timeout | 100.0% | 0.0% | -100.0 pp |
| 0 | Restricted mean recovery steps | 220.00 | 6.05 | -213.95 |
| 0 | Tracking during failure | 5.6% | 100.0% | +94.4 pp |
| 0 | Connectivity during failure | 4.9% | 33.5% | +28.6 pp |
| 0 | Chain closure during failure | 0.0% | 15.2% | +15.2 pp |
| 0 | Episode length | 260.00 | 46.05 | -213.95 |
| 1 | Task success | 85.0% | 95.0% | +10.0 pp |
| 1 | Post-failure chain recovered | 85.0% | 95.0% | +10.0 pp |
| 1 | Timeout | 15.0% | 5.0% | -10.0 pp |
| 1 | Restricted mean recovery steps | 37.40 | 16.15 | -21.25 |
| 1 | Tracking during failure | 54.8% | 95.8% | +41.0 pp |
| 1 | Connectivity during failure | 30.2% | 32.8% | +2.6 pp |
| 1 | Chain closure during failure | 14.3% | 15.6% | +1.3 pp |
| 1 | Episode length | 77.40 | 56.15 | -21.25 |
| 2 | Task success | 0.0% | 100.0% | +100.0 pp |
| 2 | Post-failure chain recovered | 0.0% | 100.0% | +100.0 pp |
| 2 | Timeout | 100.0% | 0.0% | -100.0 pp |
| 2 | Restricted mean recovery steps | 220.00 | 5.60 | -214.40 |
| 2 | Tracking during failure | 0.2% | 100.0% | +99.8 pp |
| 2 | Connectivity during failure | 4.8% | 33.1% | +28.3 pp |
| 2 | Chain closure during failure | 0.0% | 15.6% | +15.6 pp |
| 2 | Episode length | 260.00 | 45.60 | -214.40 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
