# Parameter-Matched Single-Graph Update-60 Development Summary

Last updated: 2026-07-22

## Purpose

Run a fairer development extension for the parameter-matched single-graph baseline. The previous three-seed diagnostic used only ten strict-stage updates, so it was useful for checking feasibility but not enough to judge whether extra capacity plus longer training could close the gap.

This update-60 result remains a development result, but it is now a much stronger capacity-control check.

## Protocol

Parameter-matched single-graph:

```text
graph_encoder = single
hidden_dim = 240
total_params = 394,913
strict-stage updates = 60
save interval = 10
validation episodes = 20 per seed
test episodes = 20 per seed
seeds = 0, 1, 2
scenario = dropout030_relay_failure
strict_target_sensing = True
agent_target_info_bottleneck = True
```

Full reference:

```text
graph_encoder = multi_relation
checkpoint = actor_critic_update_0060.pt
total_params = 390,385
test episodes = 20 per seed
same test base seed = 369000
```

Artifacts:

```text
parameter-matched strict run:
results/param_matched_single_graph_3seed_bottleneck_strict_update60_dev/

full same-split reference:
results/param_matched_single_graph_3seed_update60_full_reference_same_split/

combined summary:
results/param_matched_single_graph_3seed_update60_dev_summary/
```

## Checkpoint Selection

The parameter-matched single-graph baseline used validation selection over checkpoints saved every ten updates.

| Train seed | Selected update |
|---:|---:|
| 0 | 20 |
| 1 | 60 |
| 2 | 60 |

## Seed-Level Test Result

| Variant | Train seed | Recovery | Timeout | Collision | Steps | Tracking during failure | Chain during failure |
|---|---:|---:|---:|---:|---:|---:|---:|
| Single-graph MAPPO (param-matched, update-60 dev) | 0 | 55.0% | 45.0% | 0.0% | 177.3 | 9.0% | 3.1% |
| Single-graph MAPPO (param-matched, update-60 dev) | 1 | 0.0% | 100.0% | 0.0% | 260.0 | 0.4% | 0.0% |
| Single-graph MAPPO (param-matched, update-60 dev) | 2 | 0.0% | 100.0% | 0.0% | 260.0 | 6.5% | 0.0% |
| Full multi-relation reference | 0 | 75.0% | 25.0% | 0.0% | 99.0 | 78.7% | 12.4% |
| Full multi-relation reference | 1 | 90.0% | 10.0% | 0.0% | 67.0 | 91.5% | 14.3% |
| Full multi-relation reference | 2 | 100.0% | 0.0% | 0.0% | 45.1 | 100.0% | 16.8% |

## Aggregate Test Result

| Variant | Recovery | Timeout | Collision | Steps | Tracking during failure | Chain during failure | Connectivity during failure |
|---|---:|---:|---:|---:|---:|---:|---:|
| Single-graph MAPPO (param-matched, update-60 dev) | 18.3% | 81.7% | 0.0% | 232.4 | 5.3% | 1.0% | 6.2% |
| Full multi-relation reference | 88.3% | 11.7% | 0.0% | 70.3 | 90.1% | 14.5% | 21.8% |

Seed-level full-minus-parameter-matched-single deltas:

```text
recovery: +20.0 pp, +90.0 pp, +100.0 pp
timeout:  -20.0 pp, -90.0 pp, -100.0 pp
steps:    -78.3, -193.1, -215.0
tracking during failure: +69.7 pp, +91.1 pp, +93.5 pp
chain during failure: +9.2 pp, +14.3 pp, +16.8 pp
```

## Interpretation

- Longer strict-stage training improves the parameter-matched single-graph baseline compared with the ten-update diagnostic.
- The improvement is concentrated in seed 0; seeds 1 and 2 still fail to recover on the matched test split.
- The full multi-relation method remains clearly stronger on the same three seeds and same test split.
- This reduces the risk that the full method's advantage is only due to parameter count.

## Boundary

This is still not a final paper table:

- only three training seeds;
- only twenty test episodes per seed;
- parameter-matched single-graph source checkpoints were prepared in development runs rather than a fully frozen formal protocol;
- full reference uses the existing fixed-update-60 candidate, while the parameter-matched baseline uses validation-selected checkpoints from its own update-60 strict continuation.

Recommended next decision:

- If the manuscript needs a strong capacity-control baseline, promote this to a five-seed formal run with 50-100 test episodes per seed.
- If runtime is constrained, keep this as an appendix-level development check and prioritize hardened true `no_role_identity` or scenario-depth experiments.
