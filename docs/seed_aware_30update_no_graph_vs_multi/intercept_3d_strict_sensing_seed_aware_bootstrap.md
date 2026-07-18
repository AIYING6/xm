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
| Task success | 36.7% | 95.0% | +58.3 pp | [+11.6, +95.0] pp |
| Post-failure chain recovered | 36.7% | 95.0% | +58.3 pp | [+11.6, +95.0] pp |
| Timeout | 61.7% | 5.0% | -56.7 pp | [-93.3, -11.6] pp |
| Restricted mean recovery steps | 138.10 | 16.70 | -121.40 | [-200.05, -24.53] |
| Tracking during failure | 26.1% | 95.7% | +69.6 pp | [+38.9, +97.0] pp |
| Connectivity during failure | 20.6% | 42.8% | +22.1 pp | [+6.7, +34.7] pp |
| Chain closure during failure | 5.7% | 14.5% | +8.8 pp | [+1.5, +14.6] pp |
| Episode length | 178.10 | 56.70 | -121.40 | [-200.05, -24.53] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| no_graph | 22 | 5.68 |
| multi_relation | 57 | 6.00 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 25.0% | 100.0% | +75.0 pp |
| 0 | Post-failure chain recovered | 25.0% | 100.0% | +75.0 pp |
| 0 | Timeout | 70.0% | 0.0% | -70.0 pp |
| 0 | Restricted mean recovery steps | 156.45 | 6.20 | -150.25 |
| 0 | Tracking during failure | 23.9% | 100.0% | +76.1 pp |
| 0 | Connectivity during failure | 17.2% | 43.3% | +26.1 pp |
| 0 | Chain closure during failure | 3.9% | 14.9% | +11.0 pp |
| 0 | Episode length | 196.45 | 46.20 | -150.25 |
| 1 | Task success | 80.0% | 85.0% | +5.0 pp |
| 1 | Post-failure chain recovered | 80.0% | 85.0% | +5.0 pp |
| 1 | Timeout | 20.0% | 15.0% | -5.0 pp |
| 1 | Restricted mean recovery steps | 48.50 | 37.90 | -10.60 |
| 1 | Tracking during failure | 52.0% | 87.2% | +35.2 pp |
| 1 | Connectivity during failure | 36.4% | 41.7% | +5.3 pp |
| 1 | Chain closure during failure | 12.5% | 13.3% | +0.7 pp |
| 1 | Episode length | 88.50 | 77.90 | -10.60 |
| 2 | Task success | 5.0% | 100.0% | +95.0 pp |
| 2 | Post-failure chain recovered | 5.0% | 100.0% | +95.0 pp |
| 2 | Timeout | 95.0% | 0.0% | -95.0 pp |
| 2 | Restricted mean recovery steps | 209.35 | 6.00 | -203.35 |
| 2 | Tracking during failure | 2.4% | 100.0% | +97.6 pp |
| 2 | Connectivity during failure | 8.4% | 43.5% | +35.1 pp |
| 2 | Chain closure during failure | 0.6% | 15.2% | +14.6 pp |
| 2 | Episode length | 249.35 | 46.00 | -203.35 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
