# Parameter-Matched Single-Graph Five-Seed Test-50 Candidate Summary

Last updated: 2026-07-22

## Purpose

Promote the parameter-matched single-graph baseline from a three-seed development check to a five-seed capacity-control candidate.

This result uses fixed validation-selected checkpoints and a larger independent test split of 50 episodes per seed. It is the strongest current evidence that the multi-relation method's advantage is not only a parameter-count effect.

## Protocol

Parameter-matched single-graph:

```text
graph_encoder = single
hidden_dim = 240
total_params = 394,913
strict-stage updates = 60
checkpoint selection = validation split, 20 episodes per seed
test episodes = 50 per seed
test base seed = 372000
seeds = 0, 1, 2, 3, 4
scenario = dropout030_relay_failure
strict_target_sensing = True
agent_target_info_bottleneck = True
```

Full reference:

```text
graph_encoder = multi_relation
checkpoint = actor_critic_update_0060.pt
total_params = 390,385
test episodes = 50 per seed
same test base seed = 372000
```

## Selected Checkpoints

| Train seed | Selected update |
|---:|---:|
| 0 | 20 |
| 1 | 60 |
| 2 | 60 |
| 3 | 10 |
| 4 | 60 |

## Seed-Level Test Result

| Variant | Train seed | Recovery | Timeout | Collision | Steps | Tracking during failure | Chain during failure |
|---|---:|---:|---:|---:|---:|---:|---:|
| Single-graph MAPPO (param-matched) | 0 | 64.0% | 36.0% | 0.0% | 143.5 | 15.8% | 6.6% |
| Single-graph MAPPO (param-matched) | 1 | 0.0% | 100.0% | 0.0% | 260.0 | 0.5% | 0.0% |
| Single-graph MAPPO (param-matched) | 2 | 0.0% | 100.0% | 0.0% | 260.0 | 6.1% | 0.0% |
| Single-graph MAPPO (param-matched) | 3 | 2.0% | 98.0% | 0.0% | 260.0 | 1.8% | 0.0% |
| Single-graph MAPPO (param-matched) | 4 | 100.0% | 0.0% | 0.0% | 47.0 | 77.3% | 13.5% |
| Full multi-relation reference | 0 | 54.0% | 46.0% | 0.0% | 144.2 | 61.1% | 8.5% |
| Full multi-relation reference | 1 | 98.0% | 2.0% | 0.0% | 50.3 | 98.3% | 14.5% |
| Full multi-relation reference | 2 | 100.0% | 0.0% | 0.0% | 45.3 | 100.0% | 16.3% |
| Full multi-relation reference | 3 | 98.0% | 2.0% | 0.0% | 66.0 | 78.4% | 13.0% |
| Full multi-relation reference | 4 | 96.0% | 4.0% | 0.0% | 60.1 | 56.8% | 14.5% |

## Aggregate Test Result

| Variant | Recovery | Timeout | Collision | Steps | Tracking during failure | Chain during failure | Connectivity during failure |
|---|---:|---:|---:|---:|---:|---:|---:|
| Single-graph MAPPO (param-matched) | 33.2% | 66.8% | 0.0% | 194.1 | 20.3% | 4.0% | 10.3% |
| Full multi-relation reference | 89.2% | 10.8% | 0.0% | 73.2 | 78.9% | 13.4% | 21.7% |

Seed-level full-minus-parameter-matched-single deltas:

```text
recovery: -10.0 pp, +98.0 pp, +100.0 pp, +96.0 pp, -4.0 pp
timeout:  +10.0 pp, -98.0 pp, -100.0 pp, -96.0 pp, +4.0 pp
steps:    +0.7, -209.7, -214.7, -194.0, +13.1
tracking during failure: +45.3 pp, +97.8 pp, +93.9 pp, +76.7 pp, -20.5 pp
chain during failure: +1.9 pp, +14.5 pp, +16.3 pp, +13.0 pp, +1.0 pp
```

## Interpretation

- The full multi-relation method remains much stronger on average: `89.2%` recovery versus `33.2%` for the parameter-matched single-graph baseline.
- The result is not a trivial parameter-count artifact because the single-graph baseline has slightly more total parameters than the full method.
- The parameter-matched single-graph baseline is high-variance: it is competitive or stronger on seeds 0 and 4, but nearly fails on seeds 1, 2, and 3.
- This strengthens the paper's argument if reported with seed-level scatter or paired seed differences, not only a mean bar chart.

## Seed-Aware Statistics

Hierarchical bootstrap statistics are recorded in:

```text
results/param_matched_single_graph_5seed_update60_candidate_test50/seed_aware_stats/
docs/parameter_matched_single_graph_5seed_test50_seed_aware_stats/
```

The bootstrap resamples training seeds first, then matched episodes within each selected training seed.

| Metric | Single | Full | Delta full - single | 95% CI |
|---|---:|---:|---:|---:|
| Recovery | 33.2% | 89.2% | +56.0 pp | [+11.2, +98.8] pp |
| Timeout | 66.8% | 10.8% | -56.0 pp | [-98.8, -11.2] pp |
| Restricted mean recovery steps | 154.09 | 33.17 | -120.92 | [-208.93, -29.97] |
| Tracking during failure | 20.3% | 78.9% | +58.6 pp | [+16.9, +91.7] pp |
| Connectivity during failure | 10.3% | 21.7% | +11.5 pp | [+3.9, +17.7] pp |
| Chain closure during failure | 4.0% | 13.4% | +9.4 pp | [+3.6, +15.0] pp |

The recovery interval stays above zero despite strong seed-level variance, so this is usable as a capacity-control credibility result if the manuscript clearly reports the seed scatter.

## Boundary

This is a formal-candidate result, not yet a final locked manuscript table:

- checkpoint selection used 20 validation episodes per seed;
- source checkpoints for seeds 0-2 and 3-4 were prepared in separate runs with the same documented budget, then assembled;
- the full reference uses the existing fixed-update-60 candidate rather than retraining inside this exact output directory.

Recommended next step:

- Add the capacity-control baseline as either a supplemental table or a main-table credibility row.
- Report the seed scatter honestly: single-graph can occasionally work, but is less reliable across seeds.
- Do not replace the primary single-graph baseline with only this parameter-matched variant; use it to answer the parameter-count objection.

## Artifacts

- Parameter-matched source seeds 3-4: `results/param_matched_single_graph_5seed_formal_source/`
- Formal-candidate strict checkpoints: `results/param_matched_single_graph_5seed_bottleneck_strict_update60_formal_candidate/`
- Five-seed test50 parameter-matched output: `results/param_matched_single_graph_5seed_update60_candidate_test50/param_matched_single/`
- Five-seed test50 full reference output: `results/param_matched_single_graph_5seed_update60_candidate_test50/full_multi_reference/`
- Combined summary: `results/param_matched_single_graph_5seed_update60_candidate_test50/combined_summary/`
- Seed-aware statistics: `results/param_matched_single_graph_5seed_update60_candidate_test50/seed_aware_stats/`
