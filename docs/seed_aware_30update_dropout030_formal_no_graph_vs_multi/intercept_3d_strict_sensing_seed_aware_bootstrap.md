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
| Task success | 31.7% | 93.3% | +61.7 pp | [+0.0, +100.0] pp |
| Post-failure chain recovered | 31.7% | 93.3% | +61.7 pp | [+0.0, +100.0] pp |
| Timeout | 68.3% | 6.7% | -61.7 pp | [-100.0, +0.0] pp |
| Restricted mean recovery steps | 152.00 | 20.22 | -131.78 | [-214.00, -0.05] |
| Tracking during failure | 20.2% | 94.4% | +74.2 pp | [+33.1, +99.5] pp |
| Connectivity during failure | 13.7% | 31.1% | +17.4 pp | [+4.1, +26.8] pp |
| Chain closure during failure | 5.2% | 13.9% | +8.8 pp | [-0.1, +14.7] pp |
| Episode length | 192.00 | 60.22 | -131.78 | [-214.00, -0.05] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| no_graph | 19 | 5.26 |
| multi_relation | 56 | 5.95 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 10.0% | 100.0% | +90.0 pp |
| 0 | Post-failure chain recovered | 10.0% | 100.0% | +90.0 pp |
| 0 | Timeout | 90.0% | 0.0% | -90.0 pp |
| 0 | Restricted mean recovery steps | 198.45 | 6.35 | -192.10 |
| 0 | Tracking during failure | 6.4% | 100.0% | +93.6 pp |
| 0 | Connectivity during failure | 8.0% | 30.8% | +22.8 pp |
| 0 | Chain closure during failure | 1.8% | 14.2% | +12.4 pp |
| 0 | Episode length | 238.45 | 46.35 | -192.10 |
| 1 | Task success | 85.0% | 80.0% | -5.0 pp |
| 1 | Post-failure chain recovered | 85.0% | 80.0% | -5.0 pp |
| 1 | Timeout | 15.0% | 20.0% | +5.0 pp |
| 1 | Restricted mean recovery steps | 37.55 | 48.35 | +10.80 |
| 1 | Tracking during failure | 53.7% | 83.1% | +29.5 pp |
| 1 | Connectivity during failure | 28.3% | 31.1% | +2.8 pp |
| 1 | Chain closure during failure | 13.7% | 12.8% | -0.9 pp |
| 1 | Episode length | 77.55 | 88.35 | +10.80 |
| 2 | Task success | 0.0% | 100.0% | +100.0 pp |
| 2 | Post-failure chain recovered | 0.0% | 100.0% | +100.0 pp |
| 2 | Timeout | 100.0% | 0.0% | -100.0 pp |
| 2 | Restricted mean recovery steps | 220.00 | 5.95 | -214.05 |
| 2 | Tracking during failure | 0.5% | 100.0% | +99.5 pp |
| 2 | Connectivity during failure | 4.7% | 31.4% | +26.7 pp |
| 2 | Chain closure during failure | 0.0% | 14.8% | +14.8 pp |
| 2 | Episode length | 260.00 | 45.95 | -214.05 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
