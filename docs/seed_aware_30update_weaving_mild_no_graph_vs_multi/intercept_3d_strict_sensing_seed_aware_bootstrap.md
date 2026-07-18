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
| Task success | 0.0% | 6.7% | +6.7 pp | [+0.0, +18.3] pp |
| Post-failure chain recovered | 0.0% | 6.7% | +6.7 pp | [+0.0, +18.3] pp |
| Timeout | 100.0% | 93.3% | -6.7 pp | [-18.3, +0.0] pp |
| Restricted mean recovery steps | 220.00 | 212.37 | -7.63 | [-22.33, +0.00] |
| Tracking during failure | 5.2% | 31.5% | +26.4 pp | [+18.7, +34.1] pp |
| Connectivity during failure | 7.2% | 13.2% | +6.1 pp | [+5.3, +7.1] pp |
| Chain closure during failure | 0.0% | 0.0% | +0.0 pp | [+0.0, +0.0] pp |
| Episode length | 260.00 | 252.37 | -7.63 | [-22.33, +0.00] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| no_graph | 0 | nan |
| multi_relation | 4 | 105.50 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 0.0% | 15.0% | +15.0 pp |
| 0 | Post-failure chain recovered | 0.0% | 15.0% | +15.0 pp |
| 0 | Timeout | 100.0% | 85.0% | -15.0 pp |
| 0 | Restricted mean recovery steps | 220.00 | 200.35 | -19.65 |
| 0 | Tracking during failure | 3.5% | 37.7% | +34.3 pp |
| 0 | Connectivity during failure | 7.7% | 13.3% | +5.6 pp |
| 0 | Chain closure during failure | 0.0% | 0.0% | +0.0 pp |
| 0 | Episode length | 260.00 | 240.35 | -19.65 |
| 1 | Task success | 0.0% | 0.0% | +0.0 pp |
| 1 | Post-failure chain recovered | 0.0% | 0.0% | +0.0 pp |
| 1 | Timeout | 100.0% | 100.0% | +0.0 pp |
| 1 | Restricted mean recovery steps | 220.00 | 220.00 | +0.00 |
| 1 | Tracking during failure | 7.1% | 25.4% | +18.4 pp |
| 1 | Connectivity during failure | 7.1% | 12.9% | +5.8 pp |
| 1 | Chain closure during failure | 0.0% | 0.0% | +0.0 pp |
| 1 | Episode length | 260.00 | 260.00 | +0.00 |
| 2 | Task success | 0.0% | 5.0% | +5.0 pp |
| 2 | Post-failure chain recovered | 0.0% | 5.0% | +5.0 pp |
| 2 | Timeout | 100.0% | 95.0% | -5.0 pp |
| 2 | Restricted mean recovery steps | 220.00 | 216.75 | -3.25 |
| 2 | Tracking during failure | 4.9% | 31.5% | +26.5 pp |
| 2 | Connectivity during failure | 6.7% | 13.4% | +6.7 pp |
| 2 | Chain closure during failure | 0.0% | 0.0% | +0.0 pp |
| 2 | Episode length | 260.00 | 256.75 | -3.25 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
