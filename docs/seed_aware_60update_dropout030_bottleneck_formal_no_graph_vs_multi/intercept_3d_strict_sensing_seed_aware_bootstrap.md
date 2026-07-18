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
| Task success | 25.0% | 95.0% | +70.0 pp | [+20.0, +100.0] pp |
| Post-failure chain recovered | 25.0% | 95.0% | +70.0 pp | [+20.0, +100.0] pp |
| Timeout | 75.0% | 5.0% | -70.0 pp | [-100.0, -20.0] pp |
| Restricted mean recovery steps | 166.27 | 16.48 | -149.78 | [-214.47, -42.57] |
| Tracking during failure | 17.3% | 95.8% | +78.4 pp | [+44.2, +99.7] pp |
| Connectivity during failure | 11.6% | 31.9% | +20.2 pp | [+6.1, +29.0] pp |
| Chain closure during failure | 4.3% | 14.7% | +10.4 pp | [+2.4, +15.9] pp |
| Episode length | 206.27 | 56.48 | -149.78 | [-214.47, -42.57] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| no_graph | 15 | 5.07 |
| multi_relation | 57 | 5.77 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 0.0% | 95.0% | +95.0 pp |
| 0 | Post-failure chain recovered | 0.0% | 95.0% | +95.0 pp |
| 0 | Timeout | 100.0% | 5.0% | -95.0 pp |
| 0 | Restricted mean recovery steps | 220.00 | 17.05 | -202.95 |
| 0 | Tracking during failure | 1.3% | 95.8% | +94.6 pp |
| 0 | Connectivity during failure | 4.7% | 32.8% | +28.1 pp |
| 0 | Chain closure during failure | 0.0% | 13.7% | +13.7 pp |
| 0 | Episode length | 260.00 | 57.05 | -202.95 |
| 1 | Task success | 75.0% | 90.0% | +15.0 pp |
| 1 | Post-failure chain recovered | 75.0% | 90.0% | +15.0 pp |
| 1 | Timeout | 25.0% | 10.0% | -15.0 pp |
| 1 | Restricted mean recovery steps | 58.80 | 26.95 | -31.85 |
| 1 | Tracking during failure | 50.5% | 91.5% | +41.0 pp |
| 1 | Connectivity during failure | 25.9% | 30.8% | +5.0 pp |
| 1 | Chain closure during failure | 12.8% | 14.4% | +1.6 pp |
| 1 | Episode length | 98.80 | 66.95 | -31.85 |
| 2 | Task success | 0.0% | 100.0% | +100.0 pp |
| 2 | Post-failure chain recovered | 0.0% | 100.0% | +100.0 pp |
| 2 | Timeout | 100.0% | 0.0% | -100.0 pp |
| 2 | Restricted mean recovery steps | 220.00 | 5.45 | -214.55 |
| 2 | Tracking during failure | 0.3% | 100.0% | +99.7 pp |
| 2 | Connectivity during failure | 4.4% | 32.0% | +27.5 pp |
| 2 | Chain closure during failure | 0.0% | 16.0% | +16.0 pp |
| 2 | Episode length | 260.00 | 45.45 | -214.55 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
