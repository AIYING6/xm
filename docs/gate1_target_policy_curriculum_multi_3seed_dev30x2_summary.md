# Target-Policy Curriculum Multi-Relation Dev30x2 Summary

Date: 2026-07-22

## Purpose

This diagnostic tested whether the new target-policy curriculum route improves nominal `weaving_mild` transfer.

The curriculum was:

```text
mature straight checkpoint -> weaving_tiny -> weaving_mild
```

This is still a scenario-depth development run, not manuscript evidence.

## Protocol

- Method: `multi_relation`
- Seeds: `0, 1, 2`
- Stage policies: `weaving_tiny`, `weaving_mild`
- Stage updates: `30, 30`
- Source checkpoints: mature straight-target safety fixed-update-60 checkpoints
- Hidden dimension: `64`
- Learning rate: `1e-5`
- Strict sensing: disabled
- Agent target-information bottleneck: disabled
- Node failure: disabled
- Validation: 30 episodes per seed on final `weaving_mild` stage snapshots
- Test: 50 episodes per seed using validation-selected checkpoints

Outputs:

- `results/gate1_target_policy_curriculum_multi_3seed_dev30x2/`

## Result

Validation selected:

| Seed | Selected update | Validation success | Validation collision |
|---:|---:|---:|---:|
| 0 | 30 | 60.0% | 0.0% |
| 1 | 30 | 0.0% | 0.0% |
| 2 | 20 | 30.0% | 0.0% |

Disjoint test result:

| Seed | Selected update | Test success | Test collision |
|---:|---:|---:|---:|
| 0 | 30 | 58.0% | 0.0% |
| 1 | 30 | 0.0% | 0.0% |
| 2 | 20 | 24.0% | 0.0% |

Aggregate test success is `27.3%` with zero collisions.

## Interpretation

The two-stage target-policy curriculum is executable and slightly better than direct `weaving_mild` adaptation, but it does not solve the scenario-depth problem.

The core blocker remains seed-level brittleness:

- seed 0 is usable;
- seed 2 is weak but nonzero;
- seed 1 remains completely stuck.

This means the maneuvering-target route should not enter strict sensing or relay failure yet.

## Decision

Do not promote maneuvering-target results into the formal table.

The next maneuvering-target work should diagnose why seed 1 cannot approach the attack geometry. Likely directions:

1. inspect trajectories and minimum range for seed 1;
2. test easier initial geometry or smaller lateral drift;
3. improve demonstration or auxiliary shaping before spending larger PPO budgets.
