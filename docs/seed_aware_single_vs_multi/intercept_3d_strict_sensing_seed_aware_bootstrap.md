# Strict-Sensing Seed-Aware Statistics

This report uses matched strict-sensing relay-failure test episodes from the formal development runs.
Uncertainty is estimated with a hierarchical bootstrap: training seeds are resampled first, then matched episodes are resampled within each selected training seed.

- Baseline: `single`
- Proposed: `multi_relation`
- Independent training seeds: 3
- Matched test episodes: 30

## Bootstrap Summary

| Metric | Baseline | Proposed | Delta | 95% CI for delta |
|---|---:|---:|---:|---:|
| Task success | 93.3% | 100.0% | +6.7 pp | [+0.0, +23.3] pp |
| Post-failure chain recovered | 93.3% | 100.0% | +6.7 pp | [+0.0, +23.3] pp |
| Timeout | 6.7% | 0.0% | -6.7 pp | [-23.3, +0.0] pp |
| Restricted mean recovery steps | 19.40 | 5.60 | -13.80 | [-49.13, +0.47] |
| Tracking during failure | 94.4% | 100.0% | +5.6 pp | [+0.0, +19.5] pp |
| Connectivity during failure | 43.8% | 44.0% | +0.2 pp | [-0.6, +1.7] pp |
| Chain closure during failure | 15.9% | 16.0% | +0.1 pp | [-0.9, +1.9] pp |
| Episode length | 59.40 | 45.60 | -13.80 | [-49.13, +0.47] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| single | 28 | 5.07 |
| multi_relation | 30 | 5.60 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 100.0% | 100.0% | +0.0 pp |
| 0 | Post-failure chain recovered | 100.0% | 100.0% | +0.0 pp |
| 0 | Timeout | 0.0% | 0.0% | +0.0 pp |
| 0 | Restricted mean recovery steps | 5.20 | 5.60 | +0.40 |
| 0 | Tracking during failure | 100.0% | 100.0% | +0.0 pp |
| 0 | Connectivity during failure | 44.5% | 44.0% | -0.5 pp |
| 0 | Chain closure during failure | 16.7% | 16.0% | -0.7 pp |
| 0 | Episode length | 45.20 | 45.60 | +0.40 |
| 1 | Task success | 80.0% | 100.0% | +20.0 pp |
| 1 | Post-failure chain recovered | 80.0% | 100.0% | +20.0 pp |
| 1 | Timeout | 20.0% | 0.0% | -20.0 pp |
| 1 | Restricted mean recovery steps | 47.80 | 5.70 | -42.10 |
| 1 | Tracking during failure | 83.3% | 100.0% | +16.7 pp |
| 1 | Connectivity during failure | 42.5% | 43.9% | +1.4 pp |
| 1 | Chain closure during failure | 14.2% | 15.8% | +1.6 pp |
| 1 | Episode length | 87.80 | 45.70 | -42.10 |
| 2 | Task success | 100.0% | 100.0% | +0.0 pp |
| 2 | Post-failure chain recovered | 100.0% | 100.0% | +0.0 pp |
| 2 | Timeout | 0.0% | 0.0% | +0.0 pp |
| 2 | Restricted mean recovery steps | 5.20 | 5.50 | +0.30 |
| 2 | Tracking during failure | 100.0% | 100.0% | +0.0 pp |
| 2 | Connectivity during failure | 44.5% | 44.1% | -0.3 pp |
| 2 | Chain closure during failure | 16.7% | 16.2% | -0.5 pp |
| 2 | Episode length | 45.20 | 45.50 | +0.30 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
