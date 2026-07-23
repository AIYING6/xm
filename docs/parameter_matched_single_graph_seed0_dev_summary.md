# Parameter-Matched Single-Graph Seed-0 Development Summary

Last updated: 2026-07-22

## Purpose

Test whether a capacity-matched single-graph baseline can immediately close the gap to the full multi-relation method.

This is a seed-0 development diagnostic, not manuscript-level evidence.

## Baseline Specification

```text
method = Single-graph MAPPO (param-matched)
graph_encoder = single
hidden_dim = 240
total_params = 394,913
reference full total_params = 390,385
```

The parameter count is therefore matched to the full method while preserving a single union-graph information structure.

## Training Chain

Source preparation:

```text
out_dir = results/param_matched_single_graph_seed0_dev_source
seed = 0
BC episodes = 120
BC epochs = 20
nominal PPO updates = 20
topology curriculum updates = 10
num_envs = 4
rollout_steps = 64
```

Strict bottleneck diagnostic:

```text
out_dir = results/param_matched_single_graph_seed0_bottleneck_strict_dev10
source = stage3 curriculum checkpoint
strict updates = 10
validation episodes = 10
test episodes = 10
scenario = dropout030_relay_failure
strict_target_sensing = True
agent_target_info_bottleneck = True
```

Full-method same-split reference:

```text
out_dir = results/param_matched_single_graph_seed0_dev10_full_reference_same_split
checkpoint = full multi-relation actor_critic_update_0060.pt
test episodes = 10
base seed = 367000
```

## Result

| Variant | Train seed | Checkpoint | Recovery | Timeout | Collision | Steps | Tracking during failure | Chain during failure |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Single-graph MAPPO (param-matched) | 0 | update 10 | 10.0% | 90.0% | 0.0% | 238.5 | 3.4% | 1.7% |
| Full multi-relation reference | 0 | update 60 | 90.0% | 10.0% | 0.0% | 66.7 | 91.6% | 14.9% |

## Interpretation

- The parameter-matched single-graph baseline trains and evaluates correctly.
- Increasing single-graph capacity alone did not close the strict bottleneck relay-failure gap in this seed-0 diagnostic.
- The result supports expanding the parameter-matched single baseline to a three-seed development diagnostic.

## Boundary

Do not use this table as formal paper evidence:

- only one training seed;
- only ten matched test episodes;
- full reference uses an existing stronger fixed-update-60 checkpoint, while the parameter-matched single result uses a short development budget.

The next step is a three-seed development run with the same parameter-matched hidden dimension and a documented budget.

## Artifacts

- Source training root: `results/param_matched_single_graph_seed0_dev_source/`
- Strict diagnostic root: `results/param_matched_single_graph_seed0_bottleneck_strict_dev10/`
- Full same-split reference root: `results/param_matched_single_graph_seed0_dev10_full_reference_same_split/`
