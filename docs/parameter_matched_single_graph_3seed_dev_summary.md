# Parameter-Matched Single-Graph Three-Seed Development Summary

Last updated: 2026-07-22

## Purpose

Check whether the full method's advantage under strict relay-failure sensing can be explained mainly by a larger neural-network parameter budget.

This is a three-seed development diagnostic. It is stronger than the seed-0 smoke result, but it is still not a final manuscript table because the parameter-matched single-graph strict stage used a short development budget and only ten test episodes per seed.

## Baseline Specification

```text
method = Single-graph MAPPO (param-matched)
graph_encoder = single
hidden_dim = 240
total_params = 394,913
reference full total_params = 390,385
```

The capacity-control baseline has approximately the same total parameter count as the full `EA-RG-MAPPO-S` policy while retaining a single union-graph message-passing structure.

## Protocol

Parameter-matched single-graph source training:

```text
seeds = 0, 1, 2
BC episodes = 120
BC epochs = 20
nominal PPO updates = 20
topology curriculum updates = 10
num_envs = 4
rollout_steps = 64
hidden_dim = 240
```

Strict bottleneck continuation:

```text
strict updates = 10
validation episodes = 10 per seed
test episodes = 10 per seed
scenario = dropout030_relay_failure
strict_target_sensing = True
agent_target_info_bottleneck = True
```

Full-method same-split reference:

```text
method = EA-RG-MAPPO-S / multi_relation
checkpoint = actor_critic_update_0060.pt
test episodes = 10 per seed
base seed = 367000
```

## Seed-Level Result

| Variant | Train seed | Recovery | Timeout | Collision | Steps |
|---|---:|---:|---:|---:|---:|
| Single-graph MAPPO (param-matched) | 0 | 10.0% | 90.0% | 0.0% | 238.5 |
| Single-graph MAPPO (param-matched) | 1 | 0.0% | 100.0% | 0.0% | 260.0 |
| Single-graph MAPPO (param-matched) | 2 | 0.0% | 100.0% | 0.0% | 260.0 |
| Full multi-relation reference | 0 | 90.0% | 10.0% | 0.0% | 66.7 |
| Full multi-relation reference | 1 | 90.0% | 10.0% | 0.0% | 66.5 |
| Full multi-relation reference | 2 | 100.0% | 0.0% | 0.0% | 44.8 |

## Aggregate Result

| Variant | Recovery | Timeout | Collision | Steps | Tracking during failure | Chain during failure |
|---|---:|---:|---:|---:|---:|---:|
| Single-graph MAPPO (param-matched) | 3.3% | 96.7% | 0.0% | 252.8 | 4.0% | 0.6% |
| Full multi-relation reference | 93.3% | 6.7% | 0.0% | 59.3 | 94.4% | 16.0% |

Seed-level full-minus-parameter-matched-single deltas:

```text
recovery: +80.0 pp, +90.0 pp, +100.0 pp
timeout:  -80.0 pp, -90.0 pp, -100.0 pp
steps:    -171.8, -193.5, -215.2
```

## Interpretation

- The parameter-matched single-graph baseline is runnable under the strict bottleneck protocol.
- Increasing single-graph capacity alone did not close the relay-failure recovery gap in this development run.
- The result supports the claim that the multi-relation role graph structure is not just benefiting from a larger parameter count.
- Seeds 1 and 2 show weak source-policy transfer for the parameter-matched single-graph baseline, which means any final paper-facing capacity-control result should use a more conservative, fixed-budget formal protocol before being placed in a main table.

## Boundary

Do not overclaim this diagnostic:

- only three training seeds;
- only ten matched test episodes per seed;
- the full reference uses an existing fixed-update-60 checkpoint, while the parameter-matched single-graph strict stage used ten strict updates;
- this is a capacity-control development check, not the final formal baseline package.

If this baseline is included in the manuscript, the next fair step is to run a fixed-budget parameter-matched single-graph protocol with the same checkpoint-selection rule and enough matched test episodes.

## Artifacts

- Combined summary: `results/param_matched_single_graph_3seed_dev_summary/`
- Seed-0 source: `results/param_matched_single_graph_seed0_dev_source/`
- Seeds 1-2 source: `results/param_matched_single_graph_3seed_dev_source/`
- Seed-0 strict diagnostic: `results/param_matched_single_graph_seed0_bottleneck_strict_dev10/`
- Seeds 1-2 strict diagnostic: `results/param_matched_single_graph_3seed_bottleneck_strict_dev10/`
- Seed-0 full reference: `results/param_matched_single_graph_seed0_dev10_full_reference_same_split/`
- Seeds 1-2 full reference: `results/param_matched_single_graph_3seed_dev10_full_reference_same_split/`
