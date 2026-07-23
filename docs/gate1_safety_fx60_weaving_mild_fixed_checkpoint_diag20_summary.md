# Weaving-Mild Fixed-Checkpoint Scenario-Depth Diagnostic

Last updated: 2026-07-22

## Purpose

Test whether the existing straight-target fixed-update-60 checkpoints transfer zero-shot to a mildly maneuvering target under the same strict relay-failure bottleneck.

This is a scenario-depth diagnostic, not a formal paper table.

## Protocol

```text
target_policy = weaving_mild
scenario = dropout030_relay_failure
strict_target_sensing = True
agent_target_info_bottleneck = True
checkpoint = actor_critic_update_0060.pt
methods = no_graph, single, multi_relation
seeds = 0, 1, 2, 3, 4
episodes = 20 per seed
base seed = 392000
out_dir = results/gate1_safety_fx60_weaving_mild_fixed_checkpoint_diag20
```

No method was retrained for weaving targets.

## Aggregate Result

| Method | Recovery | Timeout | Collision | Steps | Tracking during failure | Chain during failure | Connectivity during failure |
|---|---:|---:|---:|---:|---:|---:|---:|
| MAPPO (no graph) | 2.0% | 98.0% | 0.0% | 257.4 | 6.9% | 0.0% | 4.4% |
| Single-graph MAPPO | 0.0% | 100.0% | 0.0% | 260.0 | 13.9% | 0.0% | 6.2% |
| Full multi-relation | 11.0% | 88.0% | 1.0% | 247.2 | 21.9% | 0.0% | 8.7% |

## Interpretation

- `weaving_mild` is substantially harder than the current straight-target relay-failure setting for fixed straight-trained checkpoints.
- The full method still has the best zero-shot recovery, but the absolute success level is too low for a main formal result.
- Chain closure during failure is `0.0%` for all methods, so this diagnostic does not yet support a high-quality scenario-depth claim.
- The result is useful because it shows that maneuvering-target scenario depth requires either target-policy curriculum, weaving-specific fine-tuning, or a less severe maneuvering diagnostic.

## Decision

Do not promote this zero-shot fixed-checkpoint result to the manuscript main table.

Recommended next step:

1. Run a small weaving-specific development fine-tuning for `multi_relation` and `single`.
2. Keep the same strict relay-failure bottleneck.
3. Use a small validation/test split first.
4. Promote only if full recovery reaches a useful range, roughly `60%` to `90%`, while baseline methods remain separated.

## Artifacts

- Raw evaluation: `results/gate1_safety_fx60_weaving_mild_fixed_checkpoint_diag20/`
- Aggregate summary: `results/gate1_safety_fx60_weaving_mild_fixed_checkpoint_diag20/summary_by_method.csv`
