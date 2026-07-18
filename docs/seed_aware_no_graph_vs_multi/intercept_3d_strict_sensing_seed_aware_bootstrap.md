# Strict-Sensing Seed-Aware Statistics

This report uses matched strict-sensing relay-failure test episodes from the formal development runs.
Uncertainty is estimated with a hierarchical bootstrap: training seeds are resampled first, then matched episodes are resampled within each selected training seed.

- Baseline: `no_graph`
- Proposed: `multi_relation`
- Independent training seeds: 3
- Matched test episodes: 30

## Bootstrap Summary

| Metric | Baseline | Proposed | Delta | 95% CI for delta |
|---|---:|---:|---:|---:|
| Task success | 40.0% | 100.0% | +60.0 pp | [+13.3, +100.0] pp |
| Post-failure chain recovered | 40.0% | 100.0% | +60.0 pp | [+13.3, +100.0] pp |
| Timeout | 60.0% | 0.0% | -60.0 pp | [-100.0, -13.3] pp |
| Restricted mean recovery steps | 134.10 | 5.60 | -128.50 | [-214.43, -28.23] |
| Tracking during failure | 27.5% | 100.0% | +72.5 pp | [+43.9, +99.4] pp |
| Connectivity during failure | 21.8% | 44.0% | +22.2 pp | [+4.7, +37.3] pp |
| Chain closure during failure | 6.6% | 16.0% | +9.4 pp | [+1.5, +16.1] pp |
| Episode length | 174.10 | 45.60 | -128.50 | [-214.43, -28.23] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| no_graph | 12 | 5.25 |
| multi_relation | 30 | 5.60 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 30.0% | 100.0% | +70.0 pp |
| 0 | Post-failure chain recovered | 30.0% | 100.0% | +70.0 pp |
| 0 | Timeout | 70.0% | 0.0% | -70.0 pp |
| 0 | Restricted mean recovery steps | 155.50 | 5.60 | -149.90 |
| 0 | Tracking during failure | 25.1% | 100.0% | +74.9 pp |
| 0 | Connectivity during failure | 18.3% | 44.0% | +25.7 pp |
| 0 | Chain closure during failure | 5.1% | 16.0% | +10.9 pp |
| 0 | Episode length | 195.50 | 45.60 | -149.90 |
| 1 | Task success | 90.0% | 100.0% | +10.0 pp |
| 1 | Post-failure chain recovered | 90.0% | 100.0% | +10.0 pp |
| 1 | Timeout | 10.0% | 0.0% | -10.0 pp |
| 1 | Restricted mean recovery steps | 26.80 | 5.70 | -21.10 |
| 1 | Tracking during failure | 56.8% | 100.0% | +43.2 pp |
| 1 | Connectivity during failure | 40.5% | 43.9% | +3.4 pp |
| 1 | Chain closure during failure | 14.7% | 15.8% | +1.1 pp |
| 1 | Episode length | 66.80 | 45.70 | -21.10 |
| 2 | Task success | 0.0% | 100.0% | +100.0 pp |
| 2 | Post-failure chain recovered | 0.0% | 100.0% | +100.0 pp |
| 2 | Timeout | 100.0% | 0.0% | -100.0 pp |
| 2 | Restricted mean recovery steps | 220.00 | 5.50 | -214.50 |
| 2 | Tracking during failure | 0.5% | 100.0% | +99.5 pp |
| 2 | Connectivity during failure | 6.7% | 44.1% | +37.4 pp |
| 2 | Chain closure during failure | 0.0% | 16.2% | +16.2 pp |
| 2 | Episode length | 260.00 | 45.50 | -214.50 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
