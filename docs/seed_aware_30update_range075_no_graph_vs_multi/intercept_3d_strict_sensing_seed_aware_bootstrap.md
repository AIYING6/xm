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
| Task success | 38.3% | 98.3% | +60.0 pp | [+6.7, +100.0] pp |
| Post-failure chain recovered | 38.3% | 98.3% | +60.0 pp | [+6.7, +100.0] pp |
| Timeout | 61.7% | 1.7% | -60.0 pp | [-100.0, -6.7] pp |
| Restricted mean recovery steps | 137.67 | 9.57 | -128.10 | [-213.37, -14.10] |
| Tracking during failure | 27.5% | 98.6% | +71.1 pp | [+38.7, +99.0] pp |
| Connectivity during failure | 20.0% | 19.7% | -0.3 pp | [-19.4, +14.9] pp |
| Chain closure during failure | 6.4% | 15.0% | +8.7 pp | [+0.6, +14.2] pp |
| Episode length | 177.67 | 49.57 | -128.10 | [-213.37, -14.10] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| no_graph | 23 | 5.22 |
| multi_relation | 59 | 6.00 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 25.0% | 100.0% | +75.0 pp |
| 0 | Post-failure chain recovered | 25.0% | 100.0% | +75.0 pp |
| 0 | Timeout | 75.0% | 0.0% | -75.0 pp |
| 0 | Restricted mean recovery steps | 166.10 | 5.60 | -160.50 |
| 0 | Tracking during failure | 22.5% | 99.8% | +77.3 pp |
| 0 | Connectivity during failure | 15.3% | 19.2% | +3.9 pp |
| 0 | Chain closure during failure | 4.7% | 16.3% | +11.6 pp |
| 0 | Episode length | 206.10 | 45.60 | -160.50 |
| 1 | Task success | 90.0% | 95.0% | +5.0 pp |
| 1 | Post-failure chain recovered | 90.0% | 95.0% | +5.0 pp |
| 1 | Timeout | 10.0% | 5.0% | -5.0 pp |
| 1 | Restricted mean recovery steps | 26.90 | 16.60 | -10.30 |
| 1 | Tracking during failure | 58.9% | 95.9% | +37.0 pp |
| 1 | Connectivity during failure | 40.1% | 19.9% | -20.1 pp |
| 1 | Chain closure during failure | 14.4% | 14.7% | +0.3 pp |
| 1 | Episode length | 66.90 | 56.60 | -10.30 |
| 2 | Task success | 0.0% | 100.0% | +100.0 pp |
| 2 | Post-failure chain recovered | 0.0% | 100.0% | +100.0 pp |
| 2 | Timeout | 100.0% | 0.0% | -100.0 pp |
| 2 | Restricted mean recovery steps | 220.00 | 6.50 | -213.50 |
| 2 | Tracking during failure | 1.0% | 100.0% | +99.0 pp |
| 2 | Connectivity during failure | 4.6% | 19.8% | +15.3 pp |
| 2 | Chain closure during failure | 0.0% | 14.1% | +14.1 pp |
| 2 | Episode length | 260.00 | 46.50 | -213.50 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
